from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL_300 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20300%20Series%20Access%20Points-c05273540.pdf?contentDisposition=attachment&form=false&hf=regular&id=c05273540.pdf&isFutureVersion=true&isLinearized=false&preview=false&ver=14"
URL_500H = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20500H%20Series%20Unified%20Hospitality%20Access%20Points%20QuickSpecs-a00056117enw.pdf?deepLink=&form=false&hf=regular&id=a00056117enw.pdf&isFutureVersion=true&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=20"
URL_720 = "https://www.hpe.com/us/en/collaterals/collateral.a50009236enw.html"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


def na(raw="Not applicable"):
    return "not_applicable", None, raw


def u(raw="Not published by the verified official source"):
    """Clear a demonstrably incorrect scraped value without inventing a replacement."""
    return "unknown", None, raw


PRODUCTS = {
    "AP-305": {
        "url": URL_300,
        "page": "1-3, 9-11",
        "title": "HPE Aruba Networking 300 Series Access Points QuickSpecs, version 14",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(300, "2.4 GHz: up to 300 Mbps with 2SS HT40"),
            "rate_5g_mbps": n(1300, "5 GHz: up to 1,300 Mbps with 3SS VHT80"),
            "total_spatial_streams": n(5, "2 spatial streams at 2.4 GHz plus 3 at 5 GHz"),
            "mimo_2g": t("2x2 SU-MIMO"),
            "mimo_5g": t("3x3 SU-MIMO; 2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80, "VHT20/40/80"),
            "max_clients": n(255, "Up to 255 associated client devices per radio"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T RJ45; USB 2.0 host; serial console"),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(13, "Maximum worst-case: 13 W PoE or 12 W DC, excluding USB load"),
            "dimensions_mm": t("165 x 165 x 38 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
            "antenna_type": t("Three integrated dual-band downtilt omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.9 dBi; 5 GHz: 5.4 dBi"),
            "centralized_management": t("Aruba Mobility Controller or controller-less Aruba Instant mode"),
            "mesh_support": b(True, "Secure enterprise mesh / wireless mesh connections are supported"),
            "fast_roaming": t("Enhanced ClientMatch with MU-MIMO-aware client steering and dynamic roaming policies"),
        },
    },
    "AP-505H": {
        "url": URL_500H,
        "page": "2-5, 11-17",
        "title": "HPE Aruba Networking 500H Series Unified Hospitality Access Points QuickSpecs, version 20",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574, "802.11ax 2.4 GHz: up to 574 Mbps with 2SS HE40; 287 Mbps with typical HE20"),
            "rate_5g_mbps": n(1201, "802.11ax 5 GHz: up to 1,201 Mbps with 2SS HE80"),
            "total_spatial_streams": n(4, "Two spatial streams on each service radio"),
            "mimo_2g": t("2x2 SU-MIMO and MU-MIMO"),
            "mimo_5g": t("2x2 SU-MIMO and MU-MIMO"),
            "max_channel_width_mhz": n(80, "HE20/40/80"),
            "max_clients": n(256, "Up to 256 associated client devices per radio"),
            "max_ssids": n(16, "Up to 16 BSSIDs per radio"),
            "ethernet_interfaces": t("1 x 100/1000/2500BASE-T Smart Rate uplink; 4 x 10/100/1000BASE-T local RJ45; USB 2.0 host; micro-USB console"),
            "poe_output": t("E1/E2 support dual IEEE 802.3af PoE output, or single IEEE 802.3at output on E1"),
            "power_method": t("48 V DC or IEEE 802.3af/at/bt PoE"),
            "max_power_consumption_w": n(14, "AP-only maximum without USB/PSE loads: 14 W on DC, 802.3bt or 802.3at"),
            "dimensions_mm": t("86 x 47 x 150 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "centralized_management": t("HPE Aruba Networking Central cloud/on-premises or gateway; standalone operation supported"),
            "fast_roaming": t("AI-powered ClientMatch client steering"),
            "wireless_security": t("WPA, WPA2 and WPA3 Enterprise/Personal; Enhanced Open (OWE); WPA2-MPSK"),
        },
    },
    "AP-725": {
        "url": URL_720,
        "page": "Technical Specifications; current HTML revision",
        "title": "HPE Aruba Networking 720 Series Campus Access Points QuickSpecs",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz / 6 GHz"),
            "rate_2g_mbps": n(344, "2.4 GHz: up to 344 Mbps with 2SS EHT20"),
            "rate_5g_mbps": n(1440, "5 GHz: up to 1.44 Gbps with 2SS EHT80"),
            "rate_6g_mbps": n(2880, "6 GHz: up to 2.88 Gbps with 2SS EHT160"),
            "total_spatial_streams": n(6, "Two spatial streams on each of three concurrent radios"),
            "mimo_2g": t("2x2 SU-MIMO and UL/DL MU-MIMO"),
            "mimo_5g": t("2x2 SU-MIMO and UL/DL MU-MIMO"),
            "mimo_6g": t("2x2 SU-MIMO and UL/DL MU-MIMO"),
            "max_channel_width_mhz": n(160, "EHT160 maximum on 6 GHz"),
            "max_clients": n(512, "Up to 512 associated client devices per radio in the current revision"),
            "ethernet_interfaces": t("1 x 100/1000/2500BASE-T RJ45; USB 2.0 host; micro-B USB serial console"),
            "power_method": t("IEEE 802.3af/at PoE; unrestricted operation with 802.3at class 4"),
            "max_power_consumption_w": n(17.1, "Maximum worst-case without USB load: 17.1 W; 22.8 W with USB load"),
            "dimensions_mm": t("200 x 200 x 48 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Integrated downtilt omnidirectional antennas for 2x2 MIMO"),
            "antenna_gain_dbi": t("2.4 GHz: 5.1 dBi; 5 GHz: 5.4 dBi; 6 GHz: 5.4 dBi"),
            "centralized_management": t("HPE Aruba Networking Central with cloud-native AOS-10; standalone or gateway operation"),
            "fast_roaming": t("AI-powered ClientMatch steering and AirMatch enhanced roaming"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Aruba AP-305, AP-505H, and AP-725 specifications."
    products = PRODUCTS
    document_version = "Official HPE Aruba Networking QuickSpecs; accessed 2026-10-16"
    brand_name = "Aruba"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name=self.brand_name).first()
        if not brand:
            raise CommandError(f"Missing brand: {self.brand_name}")
        codes = {code for item in self.products.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in self.products.values():
            if item["url"] in documents:
                continue
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version=self.document_version,
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": item["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in self.products.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing {self.brand_name} product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_status = existing.value_status if existing else None
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": f"Manually verified from {item['title']}, {item['page']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                elif kind in {"not_applicable", "unknown"}:
                    new_value = None
                    defaults["value_status"] = (
                        ProductSpec.ValueStatus.NOT_APPLICABLE
                        if kind == "not_applicable"
                        else ProductSpec.ValueStatus.UNKNOWN
                    )
                    defaults["normalized_value"] = ""
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if (
                    existing
                    and old_status == defaults["value_status"]
                    and not had
                    and kind in {"not_applicable", "unknown"}
                ):
                    unchanged += 1
                elif not had and kind not in {"not_applicable", "unknown"}:
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"{item['page']} - {model} specifications - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(self.products)}"
        ))
        self.stdout.write("; ".join(per_model))
