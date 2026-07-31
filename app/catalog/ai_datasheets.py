import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from django.conf import settings

from catalog.models import SpecDefinition


class AIExtractionError(RuntimeError):
    def __init__(self, message, metrics=None):
        super().__init__(message)
        self.metrics = metrics or {}


@dataclass(frozen=True)
class AIExtractionResult:
    specs: dict
    metadata: dict
    matched_model: str
    model_evidence: str
    model_page: int | None
    model_confidence: float
    average_confidence: float | None
    model_name: str
    metrics: dict = field(default_factory=dict)


_PDF_PAGE_MARKER = re.compile(r"\n=== PDF PAGE (\d+) ===\n")
_SEARCH_STOPWORDS = {
    "and",
    "data",
    "features",
    "for",
    "from",
    "maximum",
    "product",
    "spec",
    "support",
    "supported",
    "that",
    "the",
    "this",
    "type",
    "value",
    "with",
}


def ai_is_configured():
    return bool(
        settings.AI_DATASHEET_ENABLED
        and settings.AI_DATASHEET_BASE_URL
        and (
            settings.AI_DATASHEET_TEXT_MODEL
            or settings.AI_DATASHEET_VISION_MODEL
            or settings.AI_DATASHEET_MODEL
        )
    )


def _field_catalog(template_items):
    return [
        {
            "code": item.spec_definition.code,
            "name": item.spec_definition.display_name,
            "group": item.display_group or item.spec_definition.group,
            "data_type": item.spec_definition.data_type,
            "unit": item.spec_definition.unit,
            "description": item.spec_definition.description,
            "collection_rule": item.spec_definition.collection_rule,
        }
        for item in template_items
    ]


def _split_pdf_pages(text):
    matches = list(_PDF_PAGE_MARKER.finditer(text))
    if not matches:
        return []
    pages = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages.append((int(match.group(1)), text[match.end():end].strip()))
    return pages


def _normalized_search_text(value):
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _model_aliases(value):
    full = _normalized_search_text(value)
    aliases = {full} if full else set()
    for token in re.findall(
        r"[a-z0-9]+(?:[-_/+.][a-z0-9]+)*",
        str(value).casefold(),
    ):
        normalized = _normalized_search_text(token)
        if len(normalized) >= 4 and re.search(r"\d", normalized):
            aliases.add(normalized)
    return aliases


def _models_equivalent(expected, actual):
    return bool(_model_aliases(expected) & _model_aliases(actual))


def _model_evidence_contains(model, evidence):
    normalized_evidence = _normalized_search_text(evidence)
    return any(alias in normalized_evidence for alias in _model_aliases(model))


def _field_search_terms(fields):
    terms = set()
    phrases = {
        "dimensions",
        "interfaces",
        "operating temperature",
        "ports",
        "power consumption",
        "specifications",
        "technical specifications",
    }
    for field_config in fields:
        code = field_config["code"].replace("_", " ")
        name = field_config["name"]
        if code:
            phrases.add(code.casefold())
        if name:
            phrases.add(name.casefold())
        source = " ".join(
            (
                code,
                name,
                field_config.get("group", ""),
                field_config.get("description", ""),
                field_config.get("collection_rule", ""),
            )
        )
        terms.update(
            token
            for token in re.findall(r"[a-z0-9]+", source.casefold())
            if len(token) >= 3 and token not in _SEARCH_STOPWORDS
        )
    return terms, phrases


def _select_relevant_page_numbers(text, model, fields, page_limit=None):
    """Rank evidence pages and return a hard-capped, document-ordered selection."""
    pages = _split_pdf_pages(text)
    if not pages:
        return []

    page_limit = max(
        1,
        page_limit or settings.AI_DATASHEET_TEXT_PAGE_LIMIT,
    )
    if len(pages) <= page_limit:
        return [page_number for page_number, _ in pages]

    model_aliases = _model_aliases(model)
    terms, phrases = _field_search_terms(fields)
    scores = {}
    model_pages = set()
    field_pages = set()
    for page_number, page_text in pages:
        lowered = page_text.casefold()
        compact = _normalized_search_text(page_text)
        model_hit = any(alias in compact for alias in model_aliases)
        if model_hit:
            model_pages.add(page_number)
        score = 30 if model_hit else 0
        score += 8 if re.search(
            r"\b(?:product|technical)\s+specifications?\b",
            lowered,
        ) else 0
        score += min(16, sum(1 for term in terms if term in lowered))
        score += min(
            4,
            len(
                re.findall(
                    r"\b\d+(?:\.\d+)?\s*(?:gbps|mbps|mpps|w|mm|dbi|°c|ports?)\b",
                    lowered,
                )
            )
            / 4,
        )
        scores[page_number] = score

    # Boost the best evidence page for each still-missing field. Unlike the old
    # selector this never expands beyond the configured hard page limit.
    for field_config in fields:
        field_terms, field_phrases = _field_search_terms([field_config])
        field_scores = []
        for page_number, page_text in pages:
            lowered = page_text.casefold()
            score = 10 * sum(
                1 for phrase in field_phrases if phrase in lowered
            )
            score += sum(1 for term in field_terms if term in lowered)
            if score:
                field_scores.append((score, page_number))
        if field_scores:
            best_score, best_page = sorted(
                field_scores,
                key=lambda item: (-item[0], item[1]),
            )[0]
            scores[best_page] += 12 + best_score
            field_pages.add(best_page)

    selected = set()
    first_page = pages[0][0]
    selected.add(first_page)
    if model_pages:
        selected.add(
            max(model_pages, key=lambda page_number: scores[page_number])
        )
    head_pages = max(0, settings.AI_DATASHEET_HEAD_PAGES)
    for page_number, _ in pages[:head_pages]:
        if len(selected) < page_limit:
            selected.add(page_number)
    for page_number, _ in sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        if len(selected) >= page_limit:
            break
        selected.add(page_number)
    evidence_limit = max(
        page_limit,
        settings.AI_DATASHEET_EVIDENCE_PAGE_LIMIT,
    )
    for page_number in sorted(
        model_pages,
        key=lambda number: (-scores[number], number),
    ):
        if len(selected) >= evidence_limit:
            break
        selected.add(page_number)
    for page_number in sorted(
        field_pages,
        key=lambda number: (-scores[number], number),
    ):
        if len(selected) >= evidence_limit:
            break
        selected.add(page_number)
    for page_number, _ in sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        if len(selected) >= evidence_limit:
            break
        selected.add(page_number)
    return sorted(selected)


def _page_excerpt(page_text, model, fields, character_limit):
    if len(page_text) <= character_limit:
        return page_text
    terms, phrases = _field_search_terms(fields)
    aliases = _model_aliases(model)
    lines = page_text.splitlines()
    ranked = []
    for index, line in enumerate(lines):
        lowered = line.casefold()
        compact = _normalized_search_text(line)
        score = 20 * sum(1 for alias in aliases if alias in compact)
        score += 8 * sum(1 for phrase in phrases if phrase in lowered)
        score += sum(1 for term in terms if term in lowered)
        score += 2 if re.search(r"\d", line) else 0
        if score:
            ranked.append((score, index))
    selected_lines = set(range(min(8, len(lines))))
    for _, index in sorted(ranked, key=lambda item: (-item[0], item[1])):
        selected_lines.update(
            range(max(0, index - 2), min(len(lines), index + 3))
        )
        excerpt = "\n".join(
            lines[line_index] for line_index in sorted(selected_lines)
        )
        if len(excerpt) >= character_limit:
            break
    return "\n".join(
        lines[index] for index in sorted(selected_lines)
    )[:character_limit]


def _select_relevant_text(text, model, fields):
    """Reduce long PDFs while retaining the highest-value evidence pages."""
    pages = _split_pdf_pages(text)
    if not pages:
        return text[: settings.AI_DATASHEET_MAX_TEXT_CHARS]
    selected = set(_select_relevant_page_numbers(text, model, fields))

    per_page_limit = max(
        1200,
        settings.AI_DATASHEET_MAX_TEXT_CHARS // max(1, len(selected)),
    )
    compact_pages = []
    for page_number, page_text in pages:
        if page_number not in selected:
            continue
        compact_pages.append(
            f"\n=== PDF PAGE {page_number} ===\n"
            + _page_excerpt(
                page_text,
                model,
                fields,
                per_page_limit,
            )
        )
    return "".join(compact_pages)[: settings.AI_DATASHEET_MAX_TEXT_CHARS]


def _canonical_unit(value):
    compact = re.sub(r"[\s.]+", "", str(value).casefold())
    aliases = {
        "c": "°c",
        "celsius": "°c",
        "degreec": "°c",
        "degreescelcius": "°c",
        "degreescelsius": "°c",
        "mb/s": "mbps",
        "mbyte/s": "mbps",
        "gb/s": "gbps",
    }
    return aliases.get(compact, compact)


def _evidence_supported(raw_value, page_number, page_map):
    if not page_map:
        return True
    if not isinstance(page_number, int) or page_number not in page_map:
        return False
    raw = str(raw_value).strip()
    page = page_map[page_number]
    normalized_raw = _normalized_search_text(raw)
    normalized_page = _normalized_search_text(page)
    if len(normalized_raw) >= 6 and normalized_raw in normalized_page:
        return True
    raw_tokens = re.findall(r"[a-z0-9]+", raw.casefold())
    informative = [
        token for token in raw_tokens
        if token not in _SEARCH_STOPWORDS and len(token) >= 2
    ]
    if len(informative) < 3:
        return False
    page_tokens = set(re.findall(r"[a-z0-9]+", page.casefold()))
    overlap = sum(1 for token in informative if token in page_tokens)
    raw_numbers = re.findall(r"-?\d+(?:\.\d+)?", raw)
    return (
        overlap / len(informative) >= 0.8
        and all(number in page for number in raw_numbers)
    )


def _response_schema(codes):
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["document_match", "specs"],
        "properties": {
            "document_match": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "model_present",
                    "matched_model",
                    "model_evidence",
                    "page_number",
                    "confidence",
                ],
                "properties": {
                    "model_present": {"type": "boolean"},
                    "matched_model": {"type": "string"},
                    "model_evidence": {"type": "string"},
                    "page_number": {"type": ["integer", "null"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
            "specs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "code",
                        "value_kind",
                        "value_text",
                        "value_number",
                        "value_boolean",
                        "unit",
                        "raw_value",
                        "page_number",
                        "confidence",
                    ],
                    "properties": {
                        "code": {"type": "string", "enum": codes},
                        "value_kind": {
                            "type": "string",
                            "enum": ["text", "number", "boolean"],
                        },
                        "value_text": {"type": "string"},
                        "value_number": {"type": ["number", "null"]},
                        "value_boolean": {"type": ["boolean", "null"]},
                        "unit": {"type": "string"},
                        "raw_value": {"type": "string"},
                        "page_number": {"type": ["integer", "null"]},
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                    },
                },
            },
        },
    }


def _render_pdf_images(pdf_bytes, page_numbers=None):
    try:
        import fitz
    except ImportError as exc:
        raise AIExtractionError(
            "扫描 PDF 需要安装 PyMuPDF 才能转为页面图片。"
        ) from exc
    try:
        pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(pdf) > settings.AI_DATASHEET_MAX_VISION_PAGES:
            raise AIExtractionError(
                f"扫描 PDF 超过 {settings.AI_DATASHEET_MAX_VISION_PAGES} 页，"
                "为避免本地模型长时间占用 CPU，已停止视觉识别。"
            )
        page_limit = max(1, settings.AI_DATASHEET_VISION_PAGE_LIMIT)
        selected_indexes = (
            [number - 1 for number in page_numbers if 1 <= number <= len(pdf)]
            if page_numbers
            else list(range(min(len(pdf), page_limit)))
        )[:page_limit]
        scale = settings.AI_DATASHEET_RENDER_DPI / 72
        matrix = fitz.Matrix(scale, scale)
        images = []
        for page_index in selected_indexes:
            page = pdf[page_index]
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            images.append(
                base64.b64encode(
                    pixmap.tobytes("jpeg", jpg_quality=68)
                ).decode("ascii")
            )
        return images
    except AIExtractionError:
        raise
    except Exception as exc:
        raise AIExtractionError("无法将扫描 PDF 渲染为页面图片。") from exc


def _request_ollama(body):
    endpoint = urllib.parse.urljoin(
        settings.AI_DATASHEET_BASE_URL.rstrip("/") + "/",
        "api/chat",
    )
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=settings.AI_DATASHEET_TIMEOUT,
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read(2000).decode("utf-8", errors="replace")
        raise AIExtractionError(
            f"本地 Ollama 返回 HTTP {exc.code}: {details}"
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AIExtractionError(f"无法连接本地 Ollama 服务：{exc}") from exc


def _document_content(document, product, fields):
    compact_length = len("".join(document.text.split()))
    if not document.is_pdf or compact_length >= settings.AI_DATASHEET_OCR_THRESHOLD:
        selected_text = _select_relevant_text(
            document.text,
            product.model,
            fields,
        )
        return (
            "DOCUMENT TEXT WITH PAGE MARKERS:\n"
            + selected_text,
            [],
            "layout text",
            settings.AI_DATASHEET_TEXT_MODEL or settings.AI_DATASHEET_MODEL,
            len(_split_pdf_pages(selected_text)),
        )
    image_count = min(
        document.page_count or settings.AI_DATASHEET_VISION_PAGE_LIMIT,
        settings.AI_DATASHEET_VISION_PAGE_LIMIT,
    )
    page_numbers = list(range(1, image_count + 1))
    return (
        f"The attached {image_count} images are consecutive one-based PDF pages "
        "starting at page 1.",
        _render_pdf_images(document.content, page_numbers),
        "local vision OCR",
        settings.AI_DATASHEET_VISION_MODEL or settings.AI_DATASHEET_MODEL,
        image_count,
    )


def extract_specs_with_ai(product, document, template_items):
    if not ai_is_configured():
        raise AIExtractionError("本地 AI Datasheet 识别尚未配置。")
    fields = _field_catalog(template_items)
    if not fields:
        raise AIExtractionError("当前产品形态没有可供 AI 映射的规格字段。")
    schema = _response_schema([field["code"] for field in fields])
    field_json = json.dumps(fields, ensure_ascii=False, separators=(",", ":"))
    document_text, images, input_mode, selected_model, input_page_count = _document_content(
        document,
        product,
        fields,
    )
    prompt = f"""
You extract product specifications from official networking-product datasheets.

Target product:
- brand: {product.brand.name}
- model: {product.model}
- category: {product.category.name}
- product form: {product.product_type.name if product.product_type else ""}

Allowed fields and required database units:
{field_json}

Rules:
1. Verify that the exact target model is the subject of the document. A product
   family, related model, accessory compatibility mention, or navigation text is
   not sufficient.
2. Extract every allowed field explicitly stated or unambiguously derivable from
   the document. Do not invent, estimate, or use outside knowledge.
3. Return values in the database units above. Convert only exact unit conversions.
   raw_value must be a short, exact source excerpt from the reported page, not a
   paraphrase.
4. page_number is one-based. Give null only for HTML without page boundaries.
5. Omit uncertain fields. Marketing language alone is not technical evidence.
6. Use number for integer/decimal fields, boolean only for explicit support, and
   text for text/choice fields.
7. In a product-family table, use only the row or column explicitly belonging to
   the target model. Never combine values from neighboring models. Include the
   target model identifier in raw_value when the evidence comes from such a table.
8. Return only JSON matching this schema:
{json.dumps(schema, ensure_ascii=False, separators=(",", ":"))}

{document_text}
""".strip()
    message = {"role": "user", "content": prompt}
    if images:
        message["images"] = images
    body = {
        "model": selected_model,
        "messages": [message],
        "stream": False,
        "think": False,
        "format": schema,
        "options": {
            "temperature": 0,
            "num_ctx": settings.AI_DATASHEET_CONTEXT_LENGTH,
            "num_predict": settings.AI_DATASHEET_MAX_OUTPUT_TOKENS,
        },
        "keep_alive": settings.AI_DATASHEET_KEEP_ALIVE,
    }
    payload = _request_ollama(body)
    metrics = {
        "input_mode": input_mode,
        "input_page_count": input_page_count,
        "input_characters": len(document_text),
        "total_duration_ms": round(payload.get("total_duration", 0) / 1_000_000, 1),
        "load_duration_ms": round(payload.get("load_duration", 0) / 1_000_000, 1),
        "prompt_eval_count": payload.get("prompt_eval_count", 0),
        "prompt_eval_duration_ms": round(
            payload.get("prompt_eval_duration", 0) / 1_000_000,
            1,
        ),
        "eval_count": payload.get("eval_count", 0),
        "eval_duration_ms": round(
            payload.get("eval_duration", 0) / 1_000_000,
            1,
        ),
    }
    try:
        message = payload["message"]
        structured_text = message.get("content") or message.get("thinking")
        parsed = json.loads(structured_text)
    except (KeyError, json.JSONDecodeError, TypeError) as exc:
        raise AIExtractionError(
            "本地模型返回的结构化结果无法解析。",
            metrics,
        ) from exc

    page_map = dict(_split_pdf_pages(document.text))
    if len(_normalized_search_text("".join(page_map.values()))) < (
        settings.AI_DATASHEET_OCR_THRESHOLD
    ):
        page_map = {}
    try:
        match = parsed["document_match"]
        matched_model = str(match["matched_model"]).strip()
        model_evidence = str(match["model_evidence"]).strip()
        model_confidence = float(match["confidence"])
        model_present = bool(match["model_present"])
        model_page = match["page_number"]
        parsed_specs = parsed["specs"]
        if not isinstance(parsed_specs, list):
            raise TypeError("specs must be a list")
    except (KeyError, TypeError, ValueError) as exc:
        raise AIExtractionError(
            "本地模型返回的字段结构不完整。",
            metrics,
        ) from exc
    metrics["document_match"] = {
        "matched_model": matched_model,
        "model_present": model_present,
        "confidence": model_confidence,
        "page_number": model_page,
    }
    if (
        not model_present
        or not _models_equivalent(product.model, matched_model)
        or not _model_evidence_contains(product.model, model_evidence)
        or model_confidence < 0.85
        or not _evidence_supported(
            model_evidence,
            model_page,
            page_map,
        )
    ):
        raise AIExtractionError(
            "本地 AI 无法以足够置信度确认产品型号一致。",
            metrics,
        )

    definitions = {
        item.spec_definition.code: item.spec_definition
        for item in template_items
    }
    accepted = {}
    metadata = {}
    confidences = []
    for item in parsed_specs:
        try:
            code = item["code"]
            definition = definitions.get(code)
            confidence = float(item["confidence"])
            raw_value = str(item["raw_value"]).strip()
            page_number = item["page_number"]
            returned_unit = _canonical_unit(item["unit"])
            value_kind = item["value_kind"]
        except (KeyError, TypeError, ValueError):
            continue
        if (
            not definition
            or confidence < settings.AI_DATASHEET_MIN_CONFIDENCE
            or not raw_value
            or not _evidence_supported(
                raw_value,
                page_number,
                page_map,
            )
        ):
            continue
        expected_unit = _canonical_unit(definition.unit)
        if expected_unit != returned_unit:
            continue
        expected_kind = (
            "number"
            if definition.data_type
            in {SpecDefinition.DataType.INTEGER, SpecDefinition.DataType.DECIMAL}
            else "boolean"
            if definition.data_type == SpecDefinition.DataType.BOOLEAN
            else "text"
        )
        if value_kind != expected_kind:
            continue
        if expected_kind == "number":
            value = item["value_number"]
            if value is None:
                continue
            if definition.data_type == SpecDefinition.DataType.INTEGER:
                value = int(round(float(value)))
        elif expected_kind == "boolean":
            value = item["value_boolean"]
            if value is None:
                continue
        else:
            value = str(item["value_text"]).strip()
            if not value:
                continue
        if code in accepted and metadata[code]["confidence"] >= confidence:
            continue
        accepted[code] = (expected_kind, value, raw_value)
        metadata[code] = {
            "page_number": page_number,
            "confidence": confidence,
            "method": "ai",
            "input_mode": input_mode,
        }
        confidences.append(confidence)
    return AIExtractionResult(
        specs=accepted,
        metadata=metadata,
        matched_model=matched_model,
        model_evidence=model_evidence,
        model_page=model_page,
        model_confidence=model_confidence,
        average_confidence=(
            sum(confidences) / len(confidences) if confidences else None
        ),
        model_name=selected_model,
        metrics=metrics,
    )
