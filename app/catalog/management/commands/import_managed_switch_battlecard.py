import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from catalog.models import (
    Category,
    Product,
    ProductSpec,
    SourceDocument,
    SpecDefinition,
    SpecEvidence,
    normalize_model_key,
)
from comparison.models import ProductMatch

SOURCE_NAME = "Omada managed Switch comparison-20260318.pptx"
SOURCE_PATH = (
    "C:/Users/admin/Desktop/Mexico dirty work/产品资料/Battlecard/"
    "Omada managed Switch comparison-20260318.pptx"
)

ROW_MAP = {
    "console port": "console_interfaces",
    "console ports": "console_interfaces",
    "management port": "management_interfaces",
    "management ports": "management_interfaces",
    "usb port": "switch_usb_interfaces",
    "usb ports": "switch_usb_interfaces",
    "switching capacity": "switching_capacity_gbps",
    "packet forwarding rate": "packet_forwarding_rate_mpps",
    "forwarding rate": "packet_forwarding_rate_mpps",
    "mac address table": "mac_address_table",
    "mac address": "mac_address_table",
    "packet buffer": "packet_buffer_mb",
    "packet buffer memory": "packet_buffer_mb",
    "flash": "flash_memory",
    "flash memory": "flash_memory",
    "dram": "dram_memory",
    "ram": "dram_memory",
    "cpu": "cpu",
    "power supply": "power_supply",
    "redundant power supply": "power_supply",
    "fan": "fan_design",
    "fan design": "fan_design",
    "poe": "poe_configuration",
    "poe ports": "poe_configuration",
    "poe budget": "poe_configuration",
    "stacking bandwidth": "stacking_bandwidth_gbps",
    "stacking number": "stacking_units",
    "stacking count": "stacking_units",
    "stacking ports": "stacking_ports",
    "ip interfaces": "ip_interface_capacity",
    "ip interface": "ip_interface_capacity",
    "arp entries": "arp_entry_capacity",
    "arp entry": "arp_entry_capacity",
    "hardware routes entries": "routing_entry_capacity",
    "hardware route entries": "routing_entry_capacity",
    "routing entries": "routing_entry_capacity",
    "routing entry": "routing_entry_capacity",
    "igmp groups": "igmp_group_capacity",
    "igmp group": "igmp_group_capacity",
    "lag groups": "lag_group_capacity",
    "lag group": "lag_group_capacity",
    "sdn support": "sdn_support",
    "dhcp": "dhcp_features",
    "stp": "stp_features",
    "erps": "erps_support",
    "mld snooping": "mld_snooping",
    "ospf": "ospf_support",
    "rip": "rip_support",
    "pbr": "pbr_support",
    "policy based routing": "pbr_support",
    "vrrp": "vrrp_support",
    "bfd": "bfd_support",
    "macsec": "macsec_support",
    "secure boot": "secure_boot",
    "vxlan": "vxlan_support",
    "m lag": "m_lag_support",
    "mlag": "m_lag_support",
    "ptp": "ptp_support",
    "mpls": "mpls_support",
    "netconf": "netconf_support",
    "configuration rollback": "configuration_rollback",
    "hot patching": "hot_patching",
    "multicast routing": "multicast_routing",
    "segment routing": "segment_routing",
    "dcb": "dcb_support",
    "data center bridging": "dcb_support",
    "gre tunnel": "gre_tunnel",
    "isp feature": "isp_features",
    "isp features": "isp_features",
    "l3 routing": "l3_features",
    "acl": "acl_security",
}

BOOLEAN_CODES = {
    "sdn_support",
    "erps_support",
    "mld_snooping",
    "ospf_support",
    "rip_support",
    "pbr_support",
    "vrrp_support",
    "bfd_support",
    "macsec_support",
    "secure_boot",
    "vxlan_support",
    "m_lag_support",
    "ptp_support",
    "mpls_support",
    "netconf_support",
    "configuration_rollback",
    "hot_patching",
    "multicast_routing",
    "segment_routing",
    "dcb_support",
    "gre_tunnel",
}

BRAND_ALIASES = {
    "omada": "tplink",
    "omadapro": "tplink",
    "tplink": "tplink",
    "ubnt": "ubiquiti",
    "unifi": "ubiquiti",
    "netgear": "netgear",
    "ruckus": "ruckus",
    "trendnet": "trendnet",
    "ruijiereyee": "reyee",
}


def clean_text(value):
    value = str(value or "").replace("\v", "\n").replace("\r", "\n")
    value = value.replace("ЁЬ", "Yes").replace("ЁС", "No").replace("Ёё", "•")
    value = value.replace("ĄĖ", "Yes").replace("ĄÁ", "No")
    value = value.replace("ЃЈ", "(").replace("ЃЉ", ")")
    lines = [re.sub(r"\s+", " ", line).strip(" •") for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def normalized_label(value):
    value = clean_text(value).casefold()
    value = value.replace("&", " and ").replace("/", " ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def decimal_number(value):
    match = re.search(r"(?<![\d.])([\d,]+(?:\.\d+)?)", value)
    return Decimal(match.group(1).replace(",", "")) if match else None


def typed_value(code, raw):
    value = clean_text(raw)
    lower = value.casefold()
    if code in BOOLEAN_CODES:
        if value.startswith("√"):
            return "boolean", True
        if value.startswith("×"):
            return "boolean", False
        if re.search(r"\b(yes|support|supported|available)\b", lower):
            return "boolean", True
        if re.search(r"\b(no|not support|unsupported|n/a|developing)\b", lower) or value in {"-", "—"}:
            return "boolean", False
        if "license" in lower:
            return "boolean", True
        return "boolean", True
    if code in {"switching_capacity_gbps", "stacking_bandwidth_gbps"}:
        number = decimal_number(value)
        if number is None:
            return None
        if "tbps" in lower or "tb/s" in lower:
            number *= 1000
        return "number", number
    if code == "packet_forwarding_rate_mpps":
        number = decimal_number(value)
        if number is None:
            return None
        if "bbps" in lower or "billion" in lower:
            number *= 1000
        elif "tpps" in lower or "trillion" in lower:
            number *= 1000000
        return "number", number
    if code == "packet_buffer_mb":
        number = decimal_number(value)
        if number is None:
            return None
        if "kbit" in lower:
            number /= Decimal(8000)
        elif "kb" in lower:
            number /= Decimal(1000)
        elif "mbit" in lower:
            number /= Decimal(8)
        elif "gbit" in lower:
            number *= Decimal(125)
        return "number", number
    if code == "stacking_units":
        number = decimal_number(value)
        return ("number", int(number)) if number is not None else None
    return ("text", value) if value and value not in {"-", "—"} else None


def model_key(value):
    value = clean_text(value)
    value = re.sub(r"\s*\(\d{4}\.\d{1,2}\)\s*$", "", value)
    value = re.sub(r"\s*\(eol\)\s*$", "", value, flags=re.I)
    value = re.sub(r"v\d+(?:\.\d+)*\s*$", "", value, flags=re.I)
    value = re.sub(r"^(?:cloudengine|ekitengine|ekit engine)\s+", "", value, flags=re.I)
    value = re.sub(r"^instant on\s+", "", value, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", normalize_model_key(value).casefold())


def version_key(value):
    numbers = re.findall(r"\d+", value or "")
    return tuple(int(number) for number in numbers)


def latest_version_value(value):
    """Keep only the highest Vx/Vx.y section when a cell contains old and new specs."""
    value = clean_text(value)
    matches = list(
        re.finditer(r"(?im)(?:^|[\n;])\s*(v\d+(?:\.\d+)*)\s*[:：]\s*", value)
    )
    if len(matches) < 2:
        return value
    latest = max(matches, key=lambda match: version_key(match.group(1)))
    latest_index = matches.index(latest)
    end = matches[latest_index + 1].start() if latest_index + 1 < len(matches) else len(value)
    return value[latest.start(1):end].strip()


def model_version(value):
    value = clean_text(value)
    spaced = re.search(r"\s+(v\d+(?:\.\d+)*)\s*$", value, re.I)
    attached = re.search(r"(?<!-)(v\d+(?:\.\d+)*)\s*$", value, re.I)
    match = spaced or attached
    return match.group(1).upper() if match else ""


def brand_key(value):
    key = re.sub(r"[^a-z0-9]", "", clean_text(value).casefold())
    return BRAND_ALIASES.get(key, key)


def split_vendor_model(value):
    lines = clean_text(value).splitlines()
    if len(lines) >= 2:
        return lines[0], " ".join(lines[1:])
    return "", lines[0] if lines else ""


def table_products(rows):
    if not rows:
        return []
    first_label = normalized_label(rows[0][0])
    vendor_row = next((row for row in rows if normalized_label(row[0]) == "vendor"), None)
    model_row = next(
        (row for row in rows if normalized_label(row[0]) in {"model", "vendor and model"}),
        None,
    )
    if model_row is None and first_label in {"model", "vendor and model"}:
        model_row = rows[0]
    if model_row is None:
        return []
    products = []
    for column in range(1, len(model_row)):
        vendor = clean_text(vendor_row[column]) if vendor_row and column < len(vendor_row) else ""
        model = clean_text(model_row[column])
        if not vendor or "\n" in model:
            embedded_vendor, embedded_model = split_vendor_model(model)
            if embedded_model:
                vendor = vendor or embedded_vendor
                model = embedded_model
        if model:
            products.append((column, vendor, model))
    return products


class Command(BaseCommand):
    help = "Import Managed Switch comparison specifications extracted from the 2026-03-18 battlecard."

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True, help="JSON output from the PPT table extractor.")
        parser.add_argument("--report", help="Optional JSON import report.")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--authoritative",
            action="store_true",
            help="Treat the PPT as authoritative, overwrite covered specs, and remove stale PPT specs.",
        )
        parser.add_argument(
            "--sync-matches",
            action="store_true",
            help="Replace legacy Managed Switch matches for PPT anchor products with PPT relationships.",
        )
        parser.add_argument(
            "--latest-only",
            action="store_true",
            help="Keep only the highest Vx/Vx.y section in versioned PPT cells.",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"])
        if not input_path.exists():
            raise CommandError(f"Input JSON does not exist: {input_path}")
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        category = Category.objects.filter(slug="managed-switches").first()
        if not category:
            raise CommandError("The managed-switches category has not been initialized.")

        products = list(Product.objects.filter(category=category).select_related("brand"))
        products_by_id = {product.pk: product for product in products}
        by_key = {}
        for product in products:
            by_key.setdefault(model_key(product.model), []).append(product)

        definitions = {
            code: SpecDefinition.objects.filter(code=code, active=True).first()
            for code in set(ROW_MAP.values()) | {"ethernet_interfaces", "uplink_interfaces"}
        }
        missing_definitions = sorted(code for code, definition in definitions.items() if not definition)
        if missing_definitions:
            raise CommandError(
                "Run initialize_catalog first; missing definitions: "
                + ", ".join(missing_definitions)
            )

        candidates = {}
        unmatched = []
        ambiguous = []
        desired_matches = {}
        anchor_ids = set()
        version_mismatches = []
        ppt_versions_by_product = {}
        invalid_product_ids = set()
        for slide in payload.get("slides", []):
            slide_number = slide.get("slide_number")
            for table in slide.get("tables", []):
                rows = table.get("rows", [])
                resolved_columns = []
                for column, vendor, model in table_products(rows):
                    is_alternative_model = re.search(r"\s+/\s+", model) is not None
                    model_parts = re.split(r"\s+/\s+", model)
                    possible_keys = [model_key(part) for part in model_parts]
                    matches = []
                    for possible_key in possible_keys:
                        matches.extend(by_key.get(possible_key, []))
                    if not matches and "/" in model and not is_alternative_model:
                        base_model, suffix = model.split("/", 1)
                        matches.extend(by_key.get(model_key(base_model), []))
                        suffix_matches = by_key.get(model_key(suffix), [])
                        vendor_key_for_suffix = brand_key(vendor)
                        for suffix_product in suffix_matches:
                            if (
                                not vendor_key_for_suffix
                                or brand_key(suffix_product.brand.name)
                                == vendor_key_for_suffix
                            ):
                                invalid_product_ids.add(suffix_product.pk)
                    matches = list({product.pk: product for product in matches}.values())
                    vendor_key = brand_key(vendor)
                    branded_matches = [
                        product
                        for product in matches
                        if not vendor_key or brand_key(product.brand.name) == vendor_key
                    ]
                    if branded_matches:
                        matches = branded_matches
                    if not matches:
                        record = {"slide": slide_number, "vendor": vendor, "model": model}
                        unmatched.append(record)
                        continue
                    if len(matches) > 1:
                        ambiguous.append(
                            {
                                "slide": slide_number,
                                "vendor": vendor,
                                "model": model,
                                "product_ids": [product.pk for product in matches],
                            }
                        )
                        continue
                    resolved_columns.append((column, vendor, model, matches[0]))
                    ppt_version = model_version(model)
                    database_version = (matches[0].hardware_version or "").upper()
                    if ppt_version and ppt_version != database_version:
                        ppt_versions_by_product[matches[0].pk] = ppt_version
                        version_mismatches.append(
                            {
                                "slide": slide_number,
                                "vendor": vendor,
                                "model": model,
                                "ppt_version": ppt_version,
                                "database_version": database_version,
                            }
                        )

                anchor = next(
                    (
                        item
                        for item in resolved_columns
                        if item[3].brand.is_own_brand
                    ),
                    None,
                )
                if anchor:
                    anchor_product = anchor[3]
                    anchor_ids.add(anchor_product.pk)
                    rank = 0
                    for _, _, _, competitor in resolved_columns:
                        if competitor.pk == anchor_product.pk or competitor.brand.is_own_brand:
                            continue
                        rank += 1
                        desired_matches[(anchor_product.pk, competitor.pk)] = {
                            "slide": slide_number,
                            "rank": rank,
                        }

                for column, _vendor, _model, product in resolved_columns:
                    for row in rows[1:]:
                        if not row or column >= len(row):
                            continue
                        label = normalized_label(row[0])
                        code = ROW_MAP.get(label)
                        raw = clean_text(row[column])
                        if options["latest_only"]:
                            raw = latest_version_value(raw)
                        if not code or not raw:
                            if label == "ports" and raw:
                                candidates[(product.pk, "ethernet_interfaces")] = (
                                    raw,
                                    slide_number,
                                    clean_text(row[0]),
                                )
                                uplinks = [
                                    line
                                    for line in raw.splitlines()
                                    if re.search(r"\b(sfp|qsfp|uplink)\b", line, re.I)
                                ]
                                if uplinks:
                                    candidates[(product.pk, "uplink_interfaces")] = (
                                        "\n".join(uplinks),
                                        slide_number,
                                        clean_text(row[0]),
                                    )
                            continue
                        candidates[(product.pk, code)] = (
                            raw,
                            slide_number,
                            clean_text(row[0]),
                        )

        imported = 0
        retained = 0
        skipped = 0
        stale_specs_deleted = 0
        invalid_specs_deleted = 0
        invalid_matches_deleted = 0
        invalid_products_unpublished = 0
        product_versions_updated = 0
        matches_deleted = 0
        matches_created = 0
        touched_products = set()
        verified_date = date.today()
        source_cache = {}
        source_brand = next(
            (product.brand for product in products if product.brand.is_own_brand),
            products[0].brand if products else None,
        )

        with transaction.atomic():
            if options["authoritative"]:
                if options["latest_only"]:
                    for product_id, ppt_version in ppt_versions_by_product.items():
                        product = products_by_id[product_id]
                        if (product.hardware_version or "").upper() != ppt_version:
                            product.hardware_version = ppt_version
                            product.save(update_fields=("hardware_version", "updated_at"))
                            product_versions_updated += 1

                invalid_specs = ProductSpec.objects.filter(
                    product_id__in=invalid_product_ids
                )
                invalid_specs_deleted = invalid_specs.count()
                invalid_specs.delete()
                invalid_matches = ProductMatch.objects.filter(
                    Q(our_product_id__in=invalid_product_ids)
                    | Q(competitor_product_id__in=invalid_product_ids)
                )
                invalid_matches_deleted = invalid_matches.count()
                invalid_matches.delete()
                invalid_products_unpublished = Product.objects.filter(
                    pk__in=invalid_product_ids,
                    is_published=True,
                ).update(is_published=False)

                candidate_keys = set(candidates)
                candidate_product_ids = {product_id for product_id, _ in candidate_keys}
                stale_specs = ProductSpec.objects.filter(
                    product_id__in=candidate_product_ids,
                    source_note__startswith="Imported from Omada managed Switch",
                ).select_related("definition")
                stale_spec_ids = [
                    spec.pk
                    for spec in stale_specs
                    if (spec.product_id, spec.definition.code) not in candidate_keys
                ]
                stale_specs_deleted = len(stale_spec_ids)
                if stale_spec_ids:
                    ProductSpec.objects.filter(pk__in=stale_spec_ids).delete()

            for (product_id, code), (raw, slide_number, row_label) in candidates.items():
                parsed = typed_value(code, raw)
                if not parsed:
                    skipped += 1
                    continue
                product = products_by_id[product_id]
                definition = definitions[code]
                existing = ProductSpec.objects.filter(
                    product=product, definition=definition
                ).first()
                may_replace = (
                    options["authoritative"]
                    or existing is None
                    or existing.value_status != ProductSpec.ValueStatus.PUBLISHED
                    or existing.source_note.startswith("Automated extraction")
                    or existing.source_note.startswith("Imported from Omada managed Switch")
                )
                if not may_replace:
                    retained += 1
                    continue

                kind, value = parsed
                if kind == "number":
                    value = Decimal(str(value)).quantize(Decimal("0.001"))
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw[:1000],
                    "source_url": "",
                    "source_note": f"Imported from {SOURCE_NAME}, slide {slide_number}.",
                    "verified_date": verified_date,
                }
                defaults[{"text": "value_text", "number": "value_number", "boolean": "value_boolean"}[kind]] = value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                source = source_cache.get("battlecard")
                if not source:
                    source, _ = SourceDocument.objects.update_or_create(
                        url=f"file:///{SOURCE_PATH}",
                        document_version="2026-03-18",
                        defaults={
                            "brand": source_brand,
                            "document_type": SourceDocument.DocumentType.CATALOG,
                            "title": SOURCE_NAME,
                            "region": product.region,
                            "published_date": date(2026, 3, 18),
                            "accessed_date": verified_date,
                            "active": True,
                        },
                    )
                    source_cache["battlecard"] = source
                source_location = f"Slide {slide_number}, row “{row_label}”"
                if options["authoritative"]:
                    SpecEvidence.objects.filter(
                        product_spec=spec,
                        source_document=source,
                    ).exclude(source_location=source_location).delete()
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=source_location,
                    defaults={
                        "source_excerpt": raw[:1000],
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                    },
                )
                imported += 1
                touched_products.add(product_id)

            if options["sync_matches"]:
                legacy_matches = ProductMatch.objects.filter(
                    our_product__category=category,
                )
                matches_deleted = legacy_matches.count()
                legacy_matches.delete()
                for (our_product_id, competitor_product_id), metadata in sorted(
                    desired_matches.items()
                ):
                    our_product = products_by_id[our_product_id]
                    ProductMatch.objects.create(
                        our_product=our_product,
                        competitor_product=products_by_id[competitor_product_id],
                        match_type=ProductMatch.MatchType.DIRECT,
                        match_level=ProductMatch.MatchLevel.CORE,
                        status=ProductMatch.Status.CONFIRMED,
                        region=our_product.region,
                        rank=metadata["rank"],
                        confidence=100,
                        reason=(
                            f"Defined by {SOURCE_NAME}, slide {metadata['slide']}."
                        ),
                        valid_from=date(2026, 3, 18),
                    )
                    matches_created += 1

            report = {
                "source": SOURCE_NAME,
                "slides": payload.get("slide_count", len(payload.get("slides", []))),
                "candidate_specs": len(candidates),
                "imported_specs": imported,
                "retained_specs": retained,
                "skipped_values": skipped,
                "matched_products": len(touched_products),
                "stale_ppt_specs_deleted": stale_specs_deleted,
                "invalid_split_specs_deleted": invalid_specs_deleted,
                "invalid_split_matches_deleted": invalid_matches_deleted,
                "invalid_split_products_unpublished": invalid_products_unpublished,
                "invalid_split_product_ids": sorted(invalid_product_ids),
                "ppt_anchor_products": len(anchor_ids),
                "desired_matches": len(desired_matches),
                "matches_deleted": matches_deleted,
                "matches_created": matches_created,
                "version_mismatches": version_mismatches,
                "product_versions_updated": product_versions_updated,
                "unmatched": unmatched,
                "ambiguous": ambiguous,
                "dry_run": options["dry_run"],
            }
            if options["dry_run"]:
                transaction.set_rollback(True)

        if options.get("report"):
            Path(options["report"]).write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
