from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


ZYXEL_RGS_URL = "https://download.zyxel.com/RGS200-12P/datasheet/RGS200-12P_4.pdf"
ZYXEL_GS1350_URL = "https://download.zyxel.com/GS1350-26HP/datasheet/GS1350-26HP_6.pdf"
ZYXEL_GS1200_URL = "https://www.zyxel.com/us/en-us/products/switch/gs1200-poe-series/specifications"
RUCKUS_T350_URL = "https://www.ruckusnetworks.com/globalassets/digizuite/915764-ds-ruckus-t350-es.pdf"
DAHUA_4207_URL = "https://www.dahuasecurity.com/it/products/transmission/poe-switches/industrial-poe-switch/pfs4207-4gt-dp"


GS1350_COMMON = {
    "power_supply": t("Internal 100-240 V AC, 50/60 Hz power supply"),
    "management_methods": t(
        "Nebula cloud or standalone management; Web GUI; CLI via Telnet/SSHv2; "
        "SNMP v1/v2c/v3; RMON; ZON Utility"
    ),
    "poe_standard": t("IEEE 802.3af/802.3at PoE+"),
    "max_poe_per_port_w": n(30),
    "vlan_count": n(256),
    "l2_features": t(
        "802.1Q and port-, voice-, MAC- and vendor-ID-based VLANs; VLAN trunking; "
        "802.3ad LACP; port mirroring; IGMP snooping v1/v2/v3; LLDP/LLDP-MED; "
        "QoS, storm control and flow control"
    ),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; loop guard"),
    "acl_security": t(
        "Layer 2 MAC filtering; port isolation and security; MAC freeze; RADIUS; "
        "DHCP snooping; SSHv2 and HTTPS"
    ),
    "operating_temperature_c": t("-20 to 50 °C"),
}


PRODUCTS = {
    ("Zyxel", "RGS200-12P"): {
        "source": "zyxel_rgs",
        "values": {
            "switching_capacity_gbps": n(24),
            "packet_forwarding_rate_mpps": n(17.86),
            "packet_buffer_mb": n(0.512),
            "jumbo_frame_bytes": n(9216),
            "power_supply": t("Dual 12-58 V DC inputs; PoE/PoE+ requires at least 48/54 V DC"),
            "fan_design": t("Fanless"),
            "management_methods": t(
                "Web GUI; HTTP/HTTPS; CLI via console or Telnet; SNMP v1/v2c/v3; "
                "RMON; Syslog; TFTP/Web firmware and configuration management"
            ),
            "poe_configuration": t("8 x Gigabit PoE+ ports; up to 30 W per port; 240 W total budget"),
            "poe_standard": t("IEEE 802.3af/802.3at PoE+"),
            "poe_ports": n(8),
            "poe_budget_w": n(240),
            "max_poe_per_port_w": n(30),
            "vlan_count": n(1024),
            "l2_features": t(
                "802.1Q and GVRP; static aggregation and 802.3ad LACP; port isolation; "
                "storm control; IGMP snooping v1/v2/v3; MLD snooping/proxy; LLDP/LLDP-MED"
            ),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; fast ring failover"),
            "acl_security": t(
                "IPv4/IPv6 ACL; IP/MAC access control; 802.1X; port security; RADIUS/TACACS+; "
                "HTTPS; IP source guard and ARP inspection"
            ),
            "transmission_method": t("Store-and-forward"),
            "max_power_consumption_w": n(255),
            "dimensions_mm": t("77 x 127.3 x 154 mm"),
            "operating_temperature_c": t("-40 to 75 °C"),
        },
    },
    ("Zyxel", "GS1350-18HP"): {
        "source": "zyxel_gs1350",
        "values": {
            **GS1350_COMMON,
            "switching_capacity_gbps": n(36),
            "packet_forwarding_rate_mpps": n(26.7),
            "fan_design": t("Active cooling; 39 dBA acoustic noise at 25 °C"),
            "poe_ports": n(16),
            "poe_budget_w": n(250),
            "max_power_consumption_w": n(300.9),
            "dimensions_mm": t("330 x 230 x 44 mm"),
        },
    },
    ("Zyxel", "GS1350-26HP"): {
        "source": "zyxel_gs1350",
        "values": {
            **GS1350_COMMON,
            "mac_address_table": t("8K entries"),
            "packet_buffer_mb": n(0.525),
            "fan_design": t("Active cooling; 40.1 dBA acoustic noise at 25 °C"),
            "poe_ports": n(24),
            "poe_budget_w": n(375),
            "max_power_consumption_w": n(448.9),
            "dimensions_mm": t("441 x 270 x 44 mm"),
        },
    },
    ("Zyxel", "GS1200-5HP"): {
        "source": "zyxel_gs1200",
        "values": {
            "switching_capacity_gbps": n(10),
            "jumbo_frame_bytes": n(9216),
            "power_supply": t("External 55 V / 1.3 A power supply"),
            "fan_design": t("Fanless"),
            "management_methods": t("Web GUI"),
            "poe_standard": t("IEEE 802.3af/802.3at PoE+"),
            "poe_ports": n(4),
            "poe_budget_w": n(60),
            "max_poe_per_port_w": n(30),
            "l2_features": t(
                "802.1Q VLAN; link aggregation; IGMP snooping v1/v2/v3; port mirroring; "
                "loop detection/prevention; QoS, storm control and 802.3x flow control"
            ),
            "max_power_consumption_w": n(72),
            "dimensions_mm": t("193 x 84 x 26 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    ("RUCKUS", "T350se"): {
        "source": "ruckus_t350",
        "values": {
            "total_spatial_streams": n(4),
            "rate_2g_mbps": n(574),
            "rate_5g_mbps": n(1200),
            "max_channel_width_mhz": n(80),
            "ethernet_interfaces": t("1 x 1GbE RJ45 with 802.3at PoE input"),
            "power_method": t("802.3at PoE Class 4 or 12 V DC terminal block (7-20 V DC)"),
            "max_clients": n(512),
            "ip_rating": t("IP67"),
            "antenna_type": t("Internal 120° sector BeamFlex+ antenna plus external N-type female connectors"),
            "centralized_management": t("SmartZone, ZoneDirector, Unleashed, RUCKUS Cloud, or standalone"),
            "mesh_support": b(),
            "fast_roaming": t("802.11r/k/v and SmartRoam"),
            "wireless_security": t(
                "WPA/WPA2/WPA3 Personal and Enterprise; AES; 802.11i; Dynamic PSK; OWE; WIPS/WIDS"
            ),
            "dimensions_mm": t("209.1 x 261.7 x 102.5 mm"),
            "operating_temperature_c": t("-40 to 65 °C"),
        },
    },
    ("Other", "Dahua PFS4207-4GT-DP"): {
        "source": "dahua_4207",
        "values": {
            "switching_capacity_gbps": n(14),
            "packet_forwarding_rate_mpps": n(10.42),
            "mac_address_table": t("4000 entries"),
            "packet_buffer_mb": n(0.219),
            "jumbo_frame_bytes": n(9000),
            "power_supply": t("48-57 V DC input; external DRL-48V120W1AA supply sold separately; redundant power input"),
            "management_methods": t("Web; SNMP v1/v2c/v3; CLI; SSH; HTTPS"),
            "poe_configuration": t("4 x Gigabit PoE ports; ports 1-2 up to 90 W; remaining ports up to 30 W; 120 W total"),
            "poe_standard": t("IEEE 802.3af/802.3at/802.3bt"),
            "poe_ports": n(4),
            "poe_budget_w": n(120),
            "max_poe_per_port_w": n(90),
            "l2_features": t(
                "802.1Q VLAN; static aggregation and LACP; port mirroring; flow control; "
                "multicast; DHCP client/server/snooping; ERPS"
            ),
            "stp_features": t("ERPS ring protection; loop protection"),
            "acl_security": t("802.1X"),
            "max_power_consumption_w": n(90),
            "dimensions_mm": t("94.4 x 53.5 x 135 mm"),
            "operating_temperature_c": t("-40 to 75 °C"),
        },
    },
}


SOURCES = {
    "zyxel_rgs": {
        "brand": "Zyxel",
        "url": ZYXEL_RGS_URL,
        "version": "Official datasheet version 4, published 2023-02-23",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel RGS200-12P Datasheet",
        "region": "Global",
        "location": "Specifications and feature lists, pp. 1-4",
        "note": (
            "Manually verified from Zyxel's official version 4 datasheet for the exact model. "
            "The 512 K packet buffer is stored as 0.512 MB and 9 K jumbo frame as 9216 bytes."
        ),
    },
    "zyxel_gs1350": {
        "brand": "Zyxel",
        "url": ZYXEL_GS1350_URL,
        "version": "Official datasheet version 6, released 2024-05-14; includes V4.90 features",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel GS1350 Series Datasheet",
        "region": "Global",
        "location": "Model specifications and feature lists, pp. 4-6",
        "note": (
            "Manually verified from Zyxel's official version 6 datasheet. Model-specific table columns "
            "were used for GS1350-18HP and GS1350-26HP; family feature rows apply to both models."
        ),
    },
    "zyxel_gs1200": {
        "brand": "Zyxel",
        "url": ZYXEL_GS1200_URL,
        "version": "Current official specifications page for GS1200-5HP v2 (accessed 2026-10-14)",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel GS1200 PoE Series Specifications",
        "region": "United States/Global model",
        "location": "GS1200-5HP v2 column in current specification table",
        "note": (
            "The database row omits the hardware suffix; values were manually verified against Zyxel's "
            "current GS1200-5HP v2 specification column, following the preference for the newer version."
        ),
    },
    "ruckus_t350": {
        "brand": "RUCKUS",
        "url": RUCKUS_T350_URL,
        "version": "Official T350 series datasheet, 2021 edition linked by current product page",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "RUCKUS T350 Outdoor Wi-Fi 6 Access Point Datasheet",
        "region": "Global/Spanish edition",
        "location": "Wi-Fi, RF, network, physical and model-difference tables, pp. 3-4",
        "note": (
            "Manually verified from the official T350 series datasheet's T350se column. Antenna gain and "
            "maximum power remain blank because the manufacturer marks the T350se values as TBD."
        ),
    },
    "dahua_4207": {
        "brand": "Other",
        "url": DAHUA_4207_URL,
        "version": "Current official product page; linked datasheet dated 2023-12-26",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Dahua PFS4207-4GT-DP Official Specifications",
        "region": "Italy/Global model",
        "location": "Official hardware, performance, function and general specification tables",
        "note": (
            "Manually verified from Dahua's official exact-model page and applied to the duplicate product "
            "record currently classified under Other. Packet buffer converts 1.75 Mbits to 0.219 MB."
        ),
    },
}


RAW_VALUES = {
    ("Zyxel", "RGS200-12P", "packet_buffer_mb"): "512 K bytes",
    ("Zyxel", "RGS200-12P", "jumbo_frame_bytes"): "9 K bytes",
    ("Zyxel", "GS1350-26HP", "packet_buffer_mb"): "525 K bytes",
    ("Zyxel", "GS1200-5HP", "jumbo_frame_bytes"): "Up to 9 KB",
    ("Other", "Dahua PFS4207-4GT-DP", "packet_buffer_mb"): "1.75 Mbits",
}


class Command(BaseCommand):
    help = "Import manually verified priority competitor specifications (round 8)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand_names = {brand for brand, _model in PRODUCTS}
        brands = {brand.name: brand for brand in Brand.objects.filter(name__in=brand_names)}
        if missing := brand_names - brands.keys():
            raise CommandError(f"Missing brands: {', '.join(sorted(missing))}")

        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source_documents = {}
        for key, row in SOURCES.items():
            source_documents[key], _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version=row["version"],
                defaults={
                    "brand": brands[row["brand"]],
                    "product": None,
                    "document_type": row["type"],
                    "title": row["title"],
                    "region": row["region"],
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        updated = newly_filled = 0
        missing_models = []
        per_model = []
        for (brand_name, model), item in PRODUCTS.items():
            product = Product.objects.filter(
                brand=brands[brand_name], model=model, is_published=True
            ).first()
            if not product:
                missing_models.append(f"{brand_name} {model}")
                continue
            source = source_documents[item["source"]]
            source_meta = SOURCES[item["source"]]
            model_new = 0
            for code, (kind, value) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had_value = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((existing.value_text or "").strip())
                        or existing.value_number is not None
                        or existing.value_boolean is not None
                    )
                )
                raw_value = RAW_VALUES.get((brand_name, model, code), str(value))
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw_value,
                    "source_url": source.url[:200],
                    "source_note": source_meta["note"],
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)

                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had_value:
                    newly_filled += 1
                    model_new += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{source_meta['location']} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw_value}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1
            per_model.append(f"{brand_name} {model}:+{model_new}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={updated} newly_filled={newly_filled} "
                f"models={len(PRODUCTS) - len(missing_models)}"
            )
        )
        self.stdout.write("; ".join(per_model))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
