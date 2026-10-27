from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


UNMANAGED = {
    "management_type": t("Unmanaged; plug-and-play with no management interface"),
    "vlan_support": t("No configurable VLAN features (unmanaged switch)"),
    "link_aggregation": t("Not supported/configurable (unmanaged switch)"),
    "igmp_snooping": t("Not supported/configurable (unmanaged switch)"),
    "port_mirroring": t("Not supported/configurable (unmanaged switch)"),
    "cable_test": t("Not supported; no management interface"),
    "port_isolation": b(False, "No port-isolation control is provided on this unmanaged model"),
    "loop_prevention": b(False, "No loop-prevention control is provided on this unmanaged model"),
}


def poe_unmanaged():
    return {
        **UNMANAGED,
        "extend_mode": b(False, "No extend-mode control is listed in the official interface/features"),
        "poe_auto_recovery": b(False, "No PoE auto-recovery control is listed in the official interface/features"),
    }


PRODUCTS = {
    "TE100-S24D": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=555_TE100-S24D",
        "version": "v1.1R, data sheet dated 2017-05-02",
        "values": {
            **UNMANAGED,
            "ethernet_interfaces": t("24 x 10/100 Mbps Auto-MDIX RJ-45 ports"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("Desktop / compact standalone installation"),
            "max_power_consumption_w": n(4.65),
            "switching_capacity_gbps": n(4.8),
            "packet_forwarding_rate_mpps": n(3.571, "Wire-speed theoretical rate for 24 x 100 Mbps ports; official sheet states 4.8 Gbps fabric"),
            "mac_address_table": t("8K entries"),
            "packet_buffer_mb": n(0.219, "1.75 Mbits RAM data buffer"),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("265 x 122.7 x 41 mm"),
        },
    },
    "TEG-S17D": {
        "url": "https://www.trendnet.com/langen/support/support-detail.asp?prod=135_TEG-S17D",
        "version": "v1.0R, current official support page",
        "values": {
            **UNMANAGED,
            "ethernet_interfaces": t("16 x Gigabit RJ-45 ports"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("Desktop or rack-mount; brackets included"),
            "max_power_consumption_w": n(9.19),
            "switching_capacity_gbps": n(32),
            "packet_forwarding_rate_mpps": n(23.8),
            "mac_address_table": t("8K entries"),
            "packet_buffer_mb": n(0.5, "512 KB"),
            "jumbo_frame_bytes": n(9216, "9 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("216 x 132 x 43 mm"),
        },
    },
    "TEG-S380": {
        "url": "https://downloads.trendnet.com/TEG-S380_%28v2.0R%29/datasheet/EN_intl_datasheet_TEG-S380_%28v2.0R%29.pdf",
        "version": "v2.0R, updated 2023-09-01",
        "values": {
            **UNMANAGED,
            "ethernet_interfaces": t("8 x 2.5G RJ-45 ports (1Gbps/2.5Gbps)"),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("Desktop or wall-mount"),
            "max_power_consumption_w": n(7.26),
            "switching_capacity_gbps": n(40),
            "packet_forwarding_rate_mpps": n(29.76),
            "mac_address_table": t("4K entries"),
            "packet_buffer_mb": n(1, "RAM buffer: 1 MB"),
            "jumbo_frame_bytes": n(12288, "12 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("159 x 110 x 25 mm"),
        },
    },
    "TPE-S44": {
        "url": "https://www.trendnet.com/store/products/PoE/8-Port-10-100Mbps-PoE-Switch-TPE-S44-v4",
        "version": "V4, current official product page",
        "values": {
            **poe_unmanaged(),
            "ethernet_interfaces": t("4 x 10/100 Mbps PoE ports; 4 x 10/100 Mbps non-PoE ports"),
            "poe_standard": t("IEEE 802.3af"),
            "poe_ports": n(4),
            "poe_budget_w": n(30),
            "max_poe_per_port_w": n(15.4),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p QoS; no configurable QoS interface"),
            "installation": t("Desktop; compact fanless metal enclosure"),
            "max_power_consumption_w": n(2.1, "Maximum without a powered device; 30 W PoE budget is separate"),
            "switching_capacity_gbps": n(1.6),
            "packet_forwarding_rate_mpps": n(1.19),
            "mac_address_table": t("2K entries"),
            "packet_buffer_mb": n(0.094, "96 KB"),
            "transmission_method": t("Store-and-forward"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 45 °C"),
            "dimensions_mm": t("150 x 96 x 28 mm"),
        },
    },
    "TPE-S50": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=115_TPE-S50",
        "version": "V3, data sheet dated 2022-01-13",
        "values": {
            **poe_unmanaged(),
            "ethernet_interfaces": t("4 x Fast Ethernet PoE+ ports; 2 x Fast Ethernet non-PoE ports"),
            "poe_standard": t("IEEE 802.3af / 802.3at"),
            "poe_ports": n(4),
            "poe_budget_w": n(60),
            "max_poe_per_port_w": n(30),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("Desktop or wall-mount"),
            "max_power_consumption_w": n(1.5, "Maximum without a powered device; 60 W PoE budget is separate"),
            "switching_capacity_gbps": n(1.2),
            "packet_forwarding_rate_mpps": n(0.89),
            "mac_address_table": t("1K entries"),
            "packet_buffer_mb": n(0.055, "56 KB"),
            "jumbo_frame_bytes": n(15360, "15 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("140 x 75 x 28 mm"),
        },
    },
    "TPE-TG160H": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=225_TPE-TG160H",
        "version": "V2 / v2.0R, data sheet dated 2022-10-20",
        "values": {
            **poe_unmanaged(),
            "ethernet_interfaces": t("16 x Gigabit PoE+ RJ-45 ports"),
            "poe_standard": t("IEEE 802.3af / 802.3at"),
            "poe_ports": n(16),
            "poe_budget_w": n(123),
            "max_poe_per_port_w": n(30),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("1U 19-inch rack-mount or wall-mount; rack brackets included"),
            "max_power_consumption_w": n(12.8, "Maximum without powered devices; 123 W PoE budget is separate"),
            "switching_capacity_gbps": n(32),
            "packet_forwarding_rate_mpps": n(23.8),
            "mac_address_table": t("8K entries"),
            "packet_buffer_mb": n(0.5, "512 KB"),
            "jumbo_frame_bytes": n(10240, "10 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 45 °C"),
            "dimensions_mm": t("286 x 102 x 27 mm"),
        },
    },
    "TPE-TG44g": {
        "url": "https://downloads.trendnet.com/TPE-TG44g_v4/datasheet/EN_datasheet_TPE-TG44g_%28v4.xR%29.pdf",
        "version": "v4.xR, updated 2025-01-10",
        "values": {
            **poe_unmanaged(),
            "ethernet_interfaces": t("4 x Gigabit PoE+ ports; 4 x Gigabit non-PoE ports"),
            "poe_standard": t("IEEE 802.3af / 802.3at"),
            "poe_ports": n(4),
            "poe_budget_w": n(60),
            "max_poe_per_port_w": n(30),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("Desktop or wall-mount"),
            "max_power_consumption_w": n(66.45, "66.45 W maximum; 4.26 W with no powered device"),
            "switching_capacity_gbps": n(16),
            "packet_forwarding_rate_mpps": n(11.9),
            "mac_address_table": t("4K entries"),
            "packet_buffer_mb": n(0.5, "512 KB"),
            "jumbo_frame_bytes": n(9216, "9 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("150 x 98 x 29 mm"),
        },
    },
    "TPE-TG50g": {
        "url": "https://www.trendnet.com/products/PoE/5-Port-Gigabit-PoEplus-Switch-TPE-TG50g-v4",
        "version": "V4, current official product page",
        "values": {
            **poe_unmanaged(),
            "ethernet_interfaces": t("4 x Gigabit PoE+ ports; 1 x Gigabit non-PoE port"),
            "poe_standard": t("IEEE 802.3af / 802.3at"),
            "poe_ports": n(4),
            "poe_budget_w": n(31),
            "max_poe_per_port_w": n(30),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("Desktop or wall-mount"),
            "max_power_consumption_w": n(33.4, "33.4 W full PoE load; 3.1 W with no PoE load"),
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44),
            "mac_address_table": t("2K entries"),
            "packet_buffer_mb": n(0.125, "128 KB"),
            "jumbo_frame_bytes": n(9216, "9 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("105 x 98 x 28 mm"),
        },
    },
    "TPE-TG611": {
        "url": "https://www.trendnet.com/langsp/support/support-detail.asp?prod=220_TPE-TG611",
        "version": "V2, current official support page",
        "values": {
            **poe_unmanaged(),
            "ethernet_interfaces": t("4 x Gigabit PoE+ ports; 1 x Gigabit uplink; 1 x 100/1000 Mbps SFP slot"),
            "poe_standard": t("IEEE 802.3af / 802.3at"),
            "poe_ports": n(4),
            "poe_budget_w": n(65),
            "max_poe_per_port_w": n(30),
            "flow_control": t("IEEE 802.3x flow control"),
            "qos_support": t("IEEE 802.1p CoS and DSCP pass-through; no configurable QoS interface"),
            "installation": t("Desktop or wall-mount; compact metal enclosure"),
            "max_power_consumption_w": n(71.5),
            "switching_capacity_gbps": n(12),
            "packet_forwarding_rate_mpps": n(8.298),
            "mac_address_table": t("2K entries"),
            "packet_buffer_mb": n(0.125, "128 KB"),
            "jumbo_frame_bytes": n(9216, "9 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("193 x 84 x 26 mm"),
        },
    },
    "TPE-TG81g": {
        "url": "https://www.trendnet.com/support/support-detail.asp?prod=210_TPE-TG81g",
        "version": "v2.2R, data sheet dated 2026-06-29",
        "values": {
            **poe_unmanaged(),
            "ethernet_interfaces": t("8 x Gigabit PoE/PoE+ RJ-45 ports"),
            "poe_standard": t("IEEE 802.3af / 802.3at"),
            "poe_ports": n(8),
            "poe_budget_w": n(110),
            "max_poe_per_port_w": n(30),
            "flow_control": t("IEEE 802.3x flow control"),
            "vlan_support": t("IEEE 802.1Q frame support; no configurable VLAN interface"),
            "qos_support": t("No configurable QoS (unmanaged switch)"),
            "installation": t("19-inch rack-mount; rack kit included"),
            "max_power_consumption_w": n(130),
            "switching_capacity_gbps": n(16),
            "packet_forwarding_rate_mpps": n(11.9),
            "mac_address_table": t("4K entries"),
            "packet_buffer_mb": n(0.188, "192 KB"),
            "jumbo_frame_bytes": n(9216, "9 KB jumbo frames"),
            "fanless": b(True),
            "operating_temperature_c": t("0 to 40 °C"),
            "dimensions_mm": t("265 x 183 x 44 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified TRENDnet unmanaged switch specifications from current official sources."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="TRENDnet").first()
        if not brand:
            raise CommandError("Missing brand: TRENDnet")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for item in PRODUCTS.values():
            doc_type = SourceDocument.DocumentType.DATASHEET if item["url"].lower().endswith(".pdf") else SourceDocument.DocumentType.PRODUCT_PAGE
            documents[item["url"]], _ = SourceDocument.objects.update_or_create(
                url=item["url"], document_version=item["version"],
                defaults={
                    "brand": brand, "product": None, "document_type": doc_type,
                    "title": "TRENDnet official unmanaged switch specifications", "region": "Global",
                    "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing TRENDnet product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_signature = None if not existing else (
                    existing.value_status, existing.value_text, existing.value_number, existing.value_boolean
                )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value).lower() if kind == "boolean" else str(value),
                    "unit": definition.unit, "raw_value": raw, "source_url": item["url"][:200],
                    "source_note": f"Manually verified from current official source ({item['version']}).",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)
                new_signature = (
                    defaults["value_status"], defaults["value_text"], defaults["value_number"], defaults["value_boolean"]
                )
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if old_signature is None:
                    newly_filled += 1; model_new += 1
                elif old_signature != new_signature:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=documents[item["url"]],
                    source_location=f"Specifications - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
