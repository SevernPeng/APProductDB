from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL_303 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20303%20Series%20Access%20Points%20Data%20Sheet-a00059875enw.pdf?contentDisposition=attachment&deepLink=&form=false&hf=regular&id=a00059875enw.pdf&isFutureVersion=true&isLinearized=false&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver="
URL_303H = "https://www.hpe.com/psnow/downloadDoc/AP-303H%20Access%20Point%20Data%20Sheet-a00059878enw.pdf?contentDisposition=attachment&form=false&hf=regular&id=a00059878enw&isFutureVersion=true&isLinearized=false&preview=false&ver=9"
URL_360 = "https://www.hpe.com/psnow/downloadDoc/HPE%2BAruba%2BNetworking%2B360%2BSeries%2BOutdoor%2BAccess%2BPoints-c05348011.pdf?contentDisposition=attachment&form=false&hf=regular&id=c05348011.pdf&isFutureVersion=true&isLinearized=false&preview=false&ver=12"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


COMMON = {
    "mesh_support": b(True, "Secure enterprise mesh / wireless mesh connections are supported"),
    "fast_roaming": t("ClientMatch client steering and controller-optimized roaming"),
    "centralized_management": t("HPE Aruba Networking Central, AirWave, or Mobility Controller; Instant controller-less mode"),
    "wireless_security": t("WPA, WPA2 and WPA3 Enterprise/Personal; Enhanced Open (OWE); policy enforcement firewall"),
}


PRODUCTS = {
    "AP-303": {
        "url": URL_303,
        "page": "2-5",
        "title": "HPE Aruba Networking 303 Series Campus Access Points data sheet, Rev. 1",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(300, "Up to 300 Mbps with 2SS HT40"),
            "rate_5g_mbps": n(867, "Up to 867 Mbps with 2SS VHT80"),
            "total_spatial_streams": n(4, "2 spatial streams on each service radio"),
            "mimo_2g": t("2x2 SU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80),
            "max_clients": n(256, "Up to 256 associated client devices per radio"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T RJ45; micro-USB serial console"),
            "power_method": t("12 V DC or IEEE 802.3af PoE"),
            "max_power_consumption_w": n(10.1, "Maximum worst-case: 10.1 W PoE or 8.8 W DC"),
            "dimensions_mm": t("150 x 150 x 35 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Two integrated dual-band downtilt omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.3 dBi; 5 GHz: 5.8 dBi"),
            **COMMON,
        },
    },
    "AP-303H": {
        "url": URL_303H,
        "page": "3-5",
        "title": "HPE Aruba Networking 303H Hospitality Access Point data sheet",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(300, "Up to 300 Mbps with 2SS HT40"),
            "rate_5g_mbps": n(867, "Up to 867 Mbps with 2SS VHT80"),
            "total_spatial_streams": n(4, "2 spatial streams on each service radio"),
            "mimo_2g": t("2x2 SU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80),
            "max_clients": n(256, "Up to 256 associated client devices per radio"),
            "ethernet_interfaces": t("1 x Gigabit uplink; 3 x Gigabit local RJ45; passive pass-through; USB 2.0 host; USB console"),
            "poe_output": t("1 x IEEE 802.3af PoE output local port; disabled when AP input is 802.3af"),
            "power_method": t("48 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(9.7, "Maximum worst-case excluding attached USB and PoE-PD loads: 9.7 W"),
            "dimensions_mm": t("86 x 40 x 150 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
            "antenna_type": t("Two integrated dual-band moderately directional antennas; about 120° horizontal beamwidth"),
            "antenna_gain_dbi": t("2.4 GHz: 4.3 dBi; 5 GHz: 6.2 dBi"),
            **COMMON,
        },
    },
    "AP-365": {
        "url": URL_360,
        "page": "1-3, 8-9",
        "title": "HPE Aruba Networking 360 Series Outdoor Access Points QuickSpecs, version 12",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(400, "2.4 GHz radio: 400 Mbps maximum"),
            "rate_5g_mbps": n(866, "5 GHz radio: 866 Mbps maximum"),
            "total_spatial_streams": n(4, "2 spatial streams on each service radio"),
            "mimo_2g": t("2x2 MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80, "Technical specification lists VHT20/40/80"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T RJ45; micro-USB serial console"),
            "power_method": t("IEEE 802.3af PoE"),
            "max_power_consumption_w": n(12.5),
            "dimensions_mm": t("165 x 165 x 110 mm"),
            "operating_temperature_c": t("-40 to 55 °C ambient in full sun"),
            "ip_rating": t("IP66/IP67"),
            "antenna_type": t("Integrated H/V-polarized omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 2.7 dBi; 5 GHz: 4.3 dBi"),
            **COMMON,
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Aruba AP-303, AP-303H, and AP-365 specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Aruba").first()
        if not brand:
            raise CommandError("Missing brand: Aruba")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            if item["url"] in documents:
                continue
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Official HPE Aruba Networking data sheet; accessed 2026-10-16",
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
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Aruba product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
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
                    "source_note": f"Manually verified from {item['title']}, pages {item['page']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[item["url"]],
                    source_location=f"pp. {item['page']} - {model} specifications - {code}",
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
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
