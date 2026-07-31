import concurrent.futures
import hashlib
import io
import ipaddress
import json
import logging
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone
from pypdf import PdfReader

from catalog.ai_datasheets import (
    AIExtractionError,
    ai_is_configured,
    extract_specs_with_ai,
)
from catalog.management.commands.crawl_product_specs import (
    OFFICIAL_DOMAINS,
    USER_AGENT,
    extract_specs,
    html_to_text,
    model_token_present,
)
from catalog.models import (
    DatasheetIngestion,
    Product,
    ProductSpec,
    SourceDocument,
    SpecEvidence,
)
from catalog.product_types import product_type_code
from catalog.services import template_fields

logger = logging.getLogger(__name__)
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=max(1, settings.AI_DATASHEET_WORKERS),
    thread_name_prefix="datasheet-ingestion",
)
_PIPELINE_VERSION = "adaptive-v1"


class DatasheetValidationError(ValueError):
    pass


class DatasheetMismatchError(DatasheetValidationError):
    pass


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    final_url: str
    content: bytes
    page_count: int | None
    is_pdf: bool


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl, req.allowed_domains)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        redirected.allowed_domains = req.allowed_domains
        return redirected


def _host_matches(host, domains):
    host = host.casefold().rstrip(".")
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def validate_public_url(url, allowed_domains=()):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise DatasheetValidationError("Datasheet URL 必须是有效的 HTTP 或 HTTPS 地址。")
    host = parsed.hostname.casefold().rstrip(".")
    if allowed_domains and not _host_matches(host, allowed_domains):
        raise DatasheetValidationError("Datasheet URL 不是该品牌的官方域名。")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise DatasheetValidationError("Datasheet URL 的域名无法解析。") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise DatasheetValidationError("Datasheet URL 指向非公网地址，已拒绝访问。")
    return url


def _fetch(url, allowed_domains):
    validate_public_url(url, allowed_domains)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.8",
        },
    )
    request.allowed_domains = allowed_domains
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    max_bytes = settings.DATASHEET_MAX_BYTES
    try:
        with opener.open(request, timeout=25) as response:
            final_url = response.geturl()
            validate_public_url(final_url, allowed_domains)
            declared_size = response.headers.get("Content-Length", "")
            if declared_size.isdigit() and int(declared_size) > max_bytes:
                raise DatasheetValidationError("Datasheet 文件超过系统允许的大小。")
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise DatasheetValidationError("Datasheet 文件超过系统允许的大小。")
            return final_url, response.headers.get("Content-Type", ""), data
    except DatasheetValidationError:
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DatasheetValidationError(f"无法读取 Datasheet URL：{exc}") from exc


def _pdf_document(data, final_url=""):
    if not data.startswith(b"%PDF-"):
        raise DatasheetValidationError("文件内容不是有效的 PDF。")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise DatasheetValidationError("PDF 已加密，无法自动提取规格。")
        if not reader.pages:
            raise DatasheetValidationError("PDF 没有可读取的页面。")
        if len(reader.pages) > 200:
            raise DatasheetValidationError("PDF 页数超过 200 页，无法自动处理。")
        page_texts = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text(extraction_mode="layout") or ""
            except (TypeError, ValueError):
                page_text = page.extract_text() or ""
            page_texts.append(
                f"\n=== PDF PAGE {page_number} ===\n{page_text}"
            )
        text = "".join(page_texts)
    except DatasheetValidationError:
        raise
    except Exception as exc:
        raise DatasheetValidationError("PDF 文件损坏或无法解析。") from exc
    if len(re.sub(r"\s+", "", text)) < 20 and not ai_is_configured():
        raise DatasheetValidationError("PDF 中没有足够的可提取文字，请上传文本型 Datasheet。")
    return ExtractedDocument(text, final_url, data, len(reader.pages), True)


def _html_pdf_links(data, base_url):
    decoded = data.decode("utf-8", errors="ignore").replace("\\/", "/")
    links = re.findall(
        r"""(?:href|src)\s*=\s*["']([^"'#]+)["']""",
        decoded,
        flags=re.IGNORECASE,
    )
    links.extend(
        re.findall(
            r"""https?://[^\s"'<>]+?\.pdf(?:\?[^\s"'<>]*)?""",
            decoded,
            flags=re.IGNORECASE,
        )
    )
    ranked = []
    for link in links:
        absolute = urllib.parse.urljoin(base_url, link)
        lowered = absolute.casefold()
        score = int(lowered.split("?", 1)[0].endswith(".pdf")) * 4
        score += int("datasheet" in lowered or "data-sheet" in lowered) * 3
        if score:
            ranked.append((score, absolute))
    ranked.sort(key=lambda item: (-item[0], len(item[1])))
    return list(dict.fromkeys(url for _, url in ranked))[:10]


def fetch_url_document(product, source_url=None):
    domains = tuple(OFFICIAL_DOMAINS.get(product.brand.name, ()))
    if not domains:
        official_host = urllib.parse.urlparse(product.brand.official_website).hostname
        if official_host:
            domains = (official_host.casefold().removeprefix("www."),)
    if not domains:
        raise DatasheetValidationError(
            "该品牌尚未配置官方域名，无法安全地自动抓取 Datasheet URL。"
        )
    requested_url = source_url or product.datasheet_url
    if not requested_url:
        raise DatasheetValidationError("产品没有 Datasheet URL。")
    final_url, content_type, data = _fetch(requested_url, domains)
    if data.startswith(b"%PDF-") or "application/pdf" in content_type.casefold():
        return _pdf_document(data, final_url)
    if "html" not in content_type.casefold() and b"<html" not in data[:1000].lower():
        raise DatasheetValidationError("Datasheet URL 返回的内容不是 PDF 或网页。")
    page_text = html_to_text(data)
    pdf_links = _html_pdf_links(data, final_url)
    for linked_url in pdf_links:
        try:
            pdf_url, pdf_type, pdf_data = _fetch(linked_url, domains)
            if pdf_data.startswith(b"%PDF-") or "application/pdf" in pdf_type.casefold():
                document = _pdf_document(pdf_data, pdf_url)
                if model_token_present(product.model, document.text):
                    return document
        except DatasheetValidationError:
            continue
    if pdf_links:
        raise DatasheetValidationError(
            "Datasheet 网页包含 PDF，但 PDF 无法通过安全校验或型号校验。"
        )
    if len(re.sub(r"\s+", "", page_text)) < 100:
        raise DatasheetValidationError("Datasheet 网页没有足够的可提取规格内容。")
    return ExtractedDocument(page_text, final_url, data, None, False)


def read_uploaded_document(ingestion):
    max_bytes = settings.DATASHEET_MAX_BYTES
    with ingestion.uploaded_file.open("rb") as uploaded:
        data = uploaded.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise DatasheetValidationError("Datasheet 文件超过系统允许的大小。")
    return _pdf_document(data)


def validate_product_match(product, document, ai_result=None):
    if not model_token_present(product.model, document.text) and not ai_result:
        raise DatasheetMismatchError(
            f"文档中未识别到产品型号 {product.model}，未写入任何规格。"
        )
    return ai_result.matched_model if ai_result else product.model


def _store_specs(
    ingestion,
    document,
    extracted=None,
    extraction_metadata=None,
    extraction_method=DatasheetIngestion.ExtractionMethod.RULES,
):
    product = ingestion.product
    extracted = extracted if extracted is not None else extract_specs(
        document.text,
        product.category.slug,
    )
    extraction_metadata = extraction_metadata or {}
    allowed_definitions = {
        item.spec_definition.code: item.spec_definition
        for item in template_fields(product.category, product_type_code(product))
    }
    extracted = {
        code: value
        for code, value in extracted.items()
        if code in allowed_definitions
    }
    if not extracted:
        raise DatasheetValidationError(
            "文档与型号匹配，但未提取到当前产品形态模板中的规格字段。"
        )

    today = date.today()
    document_version = ingestion.file_sha256 if ingestion.source_type == ingestion.SourceType.UPLOAD else ""
    source, _ = SourceDocument.objects.update_or_create(
        url=document.final_url,
        document_version=document_version,
        defaults={
            "brand": product.brand,
            "product": product,
            "document_type": SourceDocument.DocumentType.DATASHEET,
            "title": f"{product.brand.name} {product.model} Datasheet",
            "file": ingestion.uploaded_file.name if ingestion.uploaded_file else "",
            "region": product.region,
            "accessed_date": today,
            "active": True,
        },
    )
    imported = 0
    retained = 0
    for code, (value_kind, value, raw_value) in extracted.items():
        definition = allowed_definitions[code]
        existing = ProductSpec.objects.filter(
            product=product,
            definition=definition,
        ).first()
        automated_notes = {
            "已校验型号，并从 Datasheet 自动提取。",
            "已校验型号，并通过 AI 从 Datasheet 自动提取。",
        }
        if (
            existing
            and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
            and existing.display_value != "Unknown"
            and existing.source_note not in automated_notes
        ):
            spec = existing
            retained += 1
        else:
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(value),
                "unit": definition.unit,
                "raw_value": str(raw_value)[:1000],
                "source_url": document.final_url[:200],
                "source_note": (
                    "已校验型号，并通过 AI 从 Datasheet 自动提取。"
                    if extraction_metadata.get(code, {}).get("method") == "ai"
                    else "已校验型号，并从 Datasheet 自动提取。"
                ),
                "verified_date": today,
                "updated_by": ingestion.requested_by,
            }
            if value_kind == "text":
                defaults["value_text"] = str(value)
            elif value_kind == "number":
                defaults["value_number"] = Decimal(str(value)).quantize(Decimal("0.001"))
            else:
                defaults["value_boolean"] = bool(value)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults=defaults,
            )
            imported += 1
        meta = extraction_metadata.get(code, {})
        location_parts = [
            "Datasheet AI extraction"
            if meta.get("method") == "ai"
            else "Datasheet automated extraction",
            code,
        ]
        if meta.get("page_number"):
            location_parts.append(f"page {meta['page_number']}")
        if meta.get("confidence") is not None:
            location_parts.append(f"confidence {meta['confidence']:.3f}")
        SpecEvidence.objects.update_or_create(
            product_spec=spec,
            source_document=source,
            source_location=": ".join(location_parts),
            defaults={
                "source_excerpt": str(raw_value)[:1000],
                "evidence_level": SpecEvidence.EvidenceLevel.A,
                "verified_by": ingestion.requested_by,
                "verified_at": timezone.now(),
            },
        )
    return imported, retained


def _known_spec_codes(product):
    known = set()
    for spec in ProductSpec.objects.filter(product=product).select_related("definition"):
        if (
            spec.value_status == ProductSpec.ValueStatus.PUBLISHED
            and spec.display_value != "Unknown"
        ):
            known.add(spec.definition.code)
    return known


def _ai_target_items(product, template_items, rule_specs):
    allowed = {item.spec_definition.code for item in template_items}
    resolved = (set(rule_specs) | _known_spec_codes(product)) & allowed
    return [
        item
        for item in template_items
        if item.spec_definition.code not in resolved
    ], resolved


def _pipeline_details(**values):
    return json.dumps(
        {"pipeline_version": _PIPELINE_VERSION, **values},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def process_datasheet_ingestion(ingestion_id):
    started = time.perf_counter()
    close_old_connections()
    try:
        ingestion = DatasheetIngestion.objects.select_related(
            "product__brand",
            "product__category",
            "product__product_type",
        ).get(pk=ingestion_id)
        ingestion.status = DatasheetIngestion.Status.PROCESSING
        ingestion.validation_message = ""
        ingestion.save(update_fields=("status", "validation_message", "updated_at"))
        fetch_started = time.perf_counter()
        if ingestion.source_type == DatasheetIngestion.SourceType.URL:
            source_url = ingestion.source_url or ingestion.product.datasheet_url
            if not source_url:
                raise DatasheetValidationError("产品没有 Datasheet URL。")
            document = fetch_url_document(ingestion.product, source_url)
        else:
            document = read_uploaded_document(ingestion)
        fetch_ms = round((time.perf_counter() - fetch_started) * 1000, 1)
        file_hash = hashlib.sha256(document.content).hexdigest()
        cached = (
            DatasheetIngestion.objects.filter(
                product=ingestion.product,
                file_sha256=file_hash,
                status=DatasheetIngestion.Status.VALIDATED,
                extraction_details__startswith=(
                    f'{{"pipeline_version":"{_PIPELINE_VERSION}"'
                ),
            )
            .exclude(pk=ingestion.pk)
            .first()
        )
        if cached:
            retained = ProductSpec.objects.filter(
                product=ingestion.product,
                value_status=ProductSpec.ValueStatus.PUBLISHED,
            ).count()
            DatasheetIngestion.objects.filter(pk=ingestion.pk).update(
                status=DatasheetIngestion.Status.VALIDATED,
                validation_message="Datasheet 内容未变化，已复用上次识别结果。",
                detected_model=cached.detected_model,
                page_count=document.page_count,
                file_sha256=file_hash,
                retained_spec_count=retained,
                extraction_method=cached.extraction_method,
                ai_model=cached.ai_model,
                ai_spec_count=cached.ai_spec_count,
                average_confidence=cached.average_confidence,
                extraction_details=_pipeline_details(
                    cache_hit=True,
                    cached_ingestion_id=cached.pk,
                    fetch_ms=fetch_ms,
                    total_ms=round((time.perf_counter() - started) * 1000, 1),
                ),
                processed_at=timezone.now(),
            )
            return DatasheetIngestion.objects.get(pk=ingestion.pk)
        template_items = template_fields(
            ingestion.product.category,
            product_type_code(ingestion.product),
        )
        rules_started = time.perf_counter()
        rule_specs = extract_specs(document.text, ingestion.product.category.slug)
        rules_ms = round((time.perf_counter() - rules_started) * 1000, 1)
        merged_specs = dict(rule_specs)
        extraction_metadata = {
            code: {"method": "rules"}
            for code in rule_specs
        }
        ai_result = None
        ai_error = ""
        ai_error_metrics = {}
        ai_items, resolved_codes = _ai_target_items(
            ingestion.product,
            template_items,
            rule_specs,
        )
        coverage = (
            len(resolved_codes)
            / len(template_items)
            if template_items
            else 1.0
        )
        should_run_ai = (
            ai_is_configured()
            and bool(ai_items)
            and coverage < settings.AI_DATASHEET_RULE_SKIP_RATIO
        )
        if should_run_ai:
            try:
                ai_result = extract_specs_with_ai(
                    ingestion.product,
                    document,
                    ai_items,
                )
                merged_specs.update(ai_result.specs)
                extraction_metadata.update(ai_result.metadata)
            except AIExtractionError as exc:
                ai_error = str(exc)
                ai_error_metrics = exc.metrics
                logger.warning(
                    "AI Datasheet extraction fell back to rules for job %s: %s",
                    ingestion.pk,
                    exc,
                )
        detected_model = validate_product_match(
            ingestion.product,
            document,
            ai_result=ai_result,
        )
        ingestion.file_sha256 = file_hash
        method = (
            DatasheetIngestion.ExtractionMethod.HYBRID
            if ai_result and rule_specs
            else DatasheetIngestion.ExtractionMethod.AI
            if ai_result
            else DatasheetIngestion.ExtractionMethod.RULES
        )
        with transaction.atomic():
            imported, retained = _store_specs(
                ingestion,
                document,
                extracted=merged_specs,
                extraction_metadata=extraction_metadata,
                extraction_method=method,
            )
            DatasheetIngestion.objects.filter(pk=ingestion.pk).update(
                status=DatasheetIngestion.Status.VALIDATED,
                validation_message="型号校验通过，规格已写入数据库。",
                detected_model=detected_model,
                page_count=document.page_count,
                file_sha256=file_hash,
                extracted_spec_count=imported,
                retained_spec_count=retained,
                extraction_method=method,
                ai_model=ai_result.model_name if ai_result else "",
                ai_spec_count=len(ai_result.specs) if ai_result else 0,
                average_confidence=(
                    ai_result.average_confidence if ai_result else None
                ),
                extraction_details=_pipeline_details(
                    cache_hit=False,
                    fetch_ms=fetch_ms,
                    rules_ms=rules_ms,
                    total_ms=round((time.perf_counter() - started) * 1000, 1),
                    template_field_count=len(template_items),
                    resolved_before_ai=len(resolved_codes),
                    ai_target_count=len(ai_items) if should_run_ai else 0,
                    ai_skipped=not should_run_ai,
                    ai_error=ai_error,
                    ai_metrics=(
                        ai_result.metrics
                        if ai_result
                        else ai_error_metrics
                    ),
                ),
                processed_at=timezone.now(),
            )
            if (
                ingestion.source_type == DatasheetIngestion.SourceType.URL
                and ingestion.source_url
            ):
                Product.objects.filter(pk=ingestion.product_id).update(
                    datasheet_url=ingestion.source_url
                )
        return DatasheetIngestion.objects.get(pk=ingestion.pk)
    except DatasheetValidationError as exc:
        DatasheetIngestion.objects.filter(pk=ingestion_id).update(
            status=DatasheetIngestion.Status.REJECTED,
            validation_message=str(exc),
            processed_at=timezone.now(),
        )
        return DatasheetIngestion.objects.get(pk=ingestion_id)
    except Exception as exc:
        logger.exception("Datasheet ingestion %s failed", ingestion_id)
        DatasheetIngestion.objects.filter(pk=ingestion_id).update(
            status=DatasheetIngestion.Status.FAILED,
            validation_message=f"处理失败：{exc}",
            processed_at=timezone.now(),
        )
        return DatasheetIngestion.objects.get(pk=ingestion_id)
    finally:
        close_old_connections()


def schedule_url_ingestion(product_id, requested_by_id=None, force=False):
    product = Product.objects.get(pk=product_id)
    if not product.datasheet_url:
        return None
    if not force:
        duplicate = product.datasheet_ingestions.filter(
            source_type=DatasheetIngestion.SourceType.URL,
            source_url=product.datasheet_url,
            status__in=(
                DatasheetIngestion.Status.PENDING,
                DatasheetIngestion.Status.PROCESSING,
                DatasheetIngestion.Status.VALIDATED,
            ),
        ).first()
        if duplicate:
            return duplicate
    ingestion = DatasheetIngestion.objects.create(
        product=product,
        source_type=DatasheetIngestion.SourceType.URL,
        source_url=product.datasheet_url,
        requested_by_id=requested_by_id,
    )
    schedule_datasheet_ingestion(ingestion.pk)
    return ingestion


def schedule_datasheet_ingestion(ingestion_id):
    """Queue one ingestion while keeping CPU-heavy Ollama inference serialized."""
    return _EXECUTOR.submit(process_datasheet_ingestion, ingestion_id)
