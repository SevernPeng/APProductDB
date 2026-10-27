from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL_500 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20500%20Series%20Campus%20Access%20Points-a00081687enw.pdf?contentDisposition=attachment&form=false&hf=regular&id=a00081687enw&isFutureVersion=true&isLinearized=false&preview=false&ver=17"
URL_510 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20510%20Series%20Campus%20Access%20Points-a00058595enw.pdf?deepLink=&form=false&hf=regular&id=a00058595enw&isFutureVersion=true&originalObjectName=a00058595jpn&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=25"
URL_530 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20530%20Series%20Campus%20Access%20Points-a00064816enw.pdf?contentDisposition=attachment&deepLink=&form=false&hf=regular&id=a00064816enw&isFutureVersion=true&isLinearized=false&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=18"
URL_560 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Aruba%20Networking%20560%20Series%20Outdoor%20Access%20Points-a00104819enw.pdf?contentDisposition=attachment&deepLink=&form=false&hf=regular&id=a00104819enw&isFutureVersion=true&isLinearized=false&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=10"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


COMMON = {
    "fast_roaming": t("Wi-Fi Agile Multiband and ClientMatch client steering"),
    "centralized_management": t("HPE Aruba Networking Central; on-premises controller/gateway; standalone operation"),
    "wireless_security": t("WPA, WPA2 and WPA3 Enterprise/Personal; Enhanced Open (OWE); policy enforcement firewall"),
}


PRODUCTS = {
    "AP-505": {
        "url": URL_500,
        "page": "5-7",
        "title": "HPE Aruba Networking 500 Series Campus Access Points data sheet",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574, "Up to 574 Mbps (HE40); 287 Mbps at HE20"),
            "rate_5g_mbps": n(1201, "Up to 1,201 Mbps with 2SS HE80"),
            "total_spatial_streams": n(4, "2 spatial streams on each of the two service radios"),
            "mimo_2g": t("2x2 MIMO"),
            "mimo_5g": t("2x2 MIMO"),
            "max_channel_width_mhz": n(80),
            "max_clients": n(256, "Up to 256 associated client devices per radio (512 total)"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T RJ45; USB 2.0 Type-A; micro-B USB console"),
            "power_method": t("12 V DC or IEEE 802.3af/at PoE"),
            "max_power_consumption_w": n(11, "PoE powered maximum without attached USB device: 11.0 W"),
            "dimensions_mm": t("160 x 161 x 37 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
            "antenna_type": t("Two integrated dual-band downtilt omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4.9 dBi; 5 GHz: 5.7 dBi"),
            **COMMON,
        },
    },
    "AP-515": {
        "url": URL_510,
        "page": "4-7",
        "title": "HPE Aruba Networking 510 Series Campus Access Points data sheet, Rev. 4",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574, "Up to 574 Mbps with 2SS HE40"),
            "rate_5g_mbps": n(4803, "Up to 4,803 Mbps with 4SS HE160"),
            "total_spatial_streams": n(6, "2x2 on 2.4 GHz plus 4x4 on 5 GHz"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("4x4 MU-MIMO; 2x2 typical at HE80"),
            "max_channel_width_mhz": n(160),
            "max_clients": n(512, "Up to 512 associated client devices per radio"),
            "ethernet_interfaces": t("1 x 100/1000/2500BASE-T Smart Rate RJ45; 1 x 10/100/1000BASE-T RJ45; USB 2.0 Type-A; micro-B USB console"),
            "power_method": t("12 V DC or IEEE 802.3af/at/bt PoE"),
            "max_power_consumption_w": n(20.8, "PoE powered maximum without attached USB device: 20.8 W"),
            "dimensions_mm": t("200 x 200 x 46 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
            "antenna_type": t("Four integrated dual-band downtilt omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 4.2 dBi; 5 GHz: 7.5 dBi"),
            **COMMON,
        },
    },
    "AP-535": {
        "url": URL_530,
        "page": "4-6",
        "title": "HPE Aruba Networking 530 Series Campus Access Points data sheet, Rev. 4",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(1147, "Up to 1,147 Mbps with 4SS HE40"),
            "rate_5g_mbps": n(2402, "Up to 2,402 Mbps with 4SS HE80 or 2SS HE160"),
            "total_spatial_streams": n(8, "4x4 on 2.4 GHz plus 4x4 on 5 GHz"),
            "mimo_2g": t("4x4 MU-MIMO"),
            "mimo_5g": t("4x4 MU-MIMO; 2x2 at 160 MHz"),
            "max_channel_width_mhz": n(160),
            "max_clients": n(1024, "Up to 1,024 associated client devices per radio (2,048 total)"),
            "ethernet_interfaces": t("2 x 100/1000/2500/5000BASE-T Smart Rate RJ45; USB 2.0 Type-A; micro-B USB console"),
            "power_method": t("48 V DC; IEEE 802.3at/bt PoE; dual 802.3at PoE supported"),
            "max_power_consumption_w": n(26.4, "PoE powered maximum without attached USB device: 26.4 W"),
            "dimensions_mm": t("240 x 240 x 57 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
            "antenna_type": t("Four integrated dual-band downtilt omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.5 dBi; 5 GHz: 5.4 dBi"),
            **COMMON,
        },
    },
    "AP-565": {
        "url": URL_560,
        "page": "4-6",
        "title": "HPE Aruba Networking 560 Series Outdoor Access Points data sheet, Rev. 4",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574, "Up to 574 Mbps with 2SS HE40"),
            "rate_5g_mbps": n(1201, "Up to 1.2 Gbps with 2SS HE80"),
            "total_spatial_streams": n(4, "2 spatial streams on each of the two service radios"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80),
            "max_clients": n(256, "Up to 256 associated client devices per radio (512 total)"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T RJ45; USB-C console"),
            "power_method": t("IEEE 802.3at PoE+; IEEE 802.3af reduced mode with IPM"),
            "max_power_consumption_w": n(15.6),
            "dimensions_mm": t("165 x 165 x 130 mm"),
            "operating_temperature_c": t("-40 to 55 °C with full solar loading"),
            "ip_rating": t("IP66/IP67"),
            "antenna_type": t("Built-in omnidirectional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 3.2 dBi; 5 GHz: 5.4 dBi"),
            **COMMON,
        },
    },
    "AP-567": {
        "url": URL_560,
        "page": "4-6",
        "title": "HPE Aruba Networking 560 Series Outdoor Access Points data sheet, Rev. 4",
        "values": {
            "supported_bands": t("2.4 GHz / 5 GHz"),
            "rate_2g_mbps": n(574, "Up to 574 Mbps with 2SS HE40"),
            "rate_5g_mbps": n(1201, "Up to 1.2 Gbps with 2SS HE80"),
            "total_spatial_streams": n(4, "2 spatial streams on each of the two service radios"),
            "mimo_2g": t("2x2 MU-MIMO"),
            "mimo_5g": t("2x2 MU-MIMO"),
            "max_channel_width_mhz": n(80),
            "max_clients": n(256, "Up to 256 associated client devices per radio (512 total)"),
            "ethernet_interfaces": t("1 x 10/100/1000BASE-T RJ45; USB-C console"),
            "power_method": t("IEEE 802.3at PoE+; IEEE 802.3af reduced mode with IPM"),
            "max_power_consumption_w": n(15.6),
            "dimensions_mm": t("165 x 165 x 130 mm"),
            "operating_temperature_c": t("-40 to 55 °C with full solar loading"),
            "ip_rating": t("IP66/IP67"),
            "antenna_type": t("Built-in 90° H x 90° V directional antennas"),
            "antenna_gain_dbi": t("2.4 GHz: 7.1 dBi; 5 GHz: 6.8 dBi"),
            **COMMON,
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Aruba AP-505/515/535/565/567 specifications from official HPE data sheets."

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
                had = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((existing.value_text or "").strip())
                        or existing.value_number is not None
                        or existing.value_boolean is not None
                    )
                )
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
                    new_value = Decimal(str(value))
                    defaults["value_number"] = new_value
                else:
                    new_value = str(value)
                    defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
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
