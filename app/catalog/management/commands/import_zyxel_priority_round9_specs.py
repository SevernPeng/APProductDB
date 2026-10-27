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


FWA710_URL = "https://download.zyxel.com/Nebula_FWA710/datasheet/Nebula%20FWA710_3.pdf"
VPN300_URL = "https://www.zyxel.com/library/download/Firewall-Comparison-Matrix.pdf"
VPN300_GUIDE_URL = "https://download.zyxel.com/VPN300/user_guide/VPN300_V5.37_Ed2.pdf"
WAX650S_URL = "https://download.zyxel.com/WAX650S/datasheet/WAX650S_8.pdf"
GS1350_URL = "https://download.zyxel.com/GS1350-26HP/datasheet/GS1350-26HP_6.pdf"
GS1200_URL = "https://www.zyxel.com/us/en-us/products/switch/gs1200-poe-series/specifications"
XMG1930_URL = "https://download.zyxel.com/XMG1930-30HP/datasheet/XMG1930-30HP_5.pdf"


GS1350_L2 = t(
    "802.1Q, port-, voice-, MAC- and vendor-ID-based VLANs; VLAN trunking; "
    "802.3ad LACP; port mirroring; IGMP snooping v1/v2/v3; LLDP/LLDP-MED; "
    "QoS, storm control and flow control"
)
GS1350_MANAGEMENT = t(
    "Nebula cloud or standalone management; standard/surveillance Web GUI; "
    "CLI via Telnet/SSHv2; SNMP v1/v2c/v3; RMON; ZON Utility"
)
GS1350_SECURITY = t(
    "Layer 2 MAC filtering; port isolation and security; MAC freeze; RADIUS; "
    "DHCP snooping; SSHv2 and HTTPS"
)

GS1200_L2 = t(
    "802.1Q VLAN; link aggregation; IGMP snooping v1/v2/v3; port mirroring; "
    "loop detection/prevention; QoS, broadcast storm control and 802.3x flow control"
)

XMG_L2 = t(
    "802.1Q static/dynamic, port- and voice VLANs; VLAN trunking and GVRP; "
    "802.3ad LACP; IGMP snooping v1/v2/v3; port mirroring; LLDP/LLDP-MED; "
    "QoS, storm control and flow control"
)
XMG_MANAGEMENT = t(
    "Nebula cloud or standalone management; Web; Telnet; SNMP v1/v2c/v3; "
    "RMON; Syslog; Zyxel iStacking and ZON Utility"
)
XMG_SECURITY = t(
    "IPv4/IPv6 ACL packet filtering; 802.1X; port security and isolation; "
    "MAC authentication; RADIUS; SSL/HTTPS; static ARP and CPU protection"
)


PRODUCTS = {
    "FWA710": {
        "source": "fwa710",
        "values": {
            "wan_interfaces": t("5G NR/4G LTE cellular WAN via 1 x Micro SIM"),
            "vpn_protocols": t("VPN pass-through"),
            "lan_interfaces": t("1 x 2.5GbE 10/100/1000/2500Base-T PoE port"),
            "uplink_interfaces": t("5G NR/4G LTE cellular uplink; 1 x 2.5GbE PoE Ethernet port"),
            "firewall_features": t(
                "SPI firewall; DoS detection; application-level firewall; MAC/IP/URL filtering"
            ),
            "lightning_protection_kv": t("ITU-T K.21 enhanced mode, 6 kV / 300 A"),
            "max_power_consumption_w": n(15),
            "dimensions_mm": t("255 x 256 x 58 mm"),
            "operating_temperature_c": t("-40 to 60 °C"),
        },
    },
    "VPN300": {
        "source": "vpn300",
        "values": {
            "ethernet_interfaces": t("7 x configurable Gigabit Ethernet RJ45; 1 x SFP"),
            "wan_interfaces": t("7 x configurable Gigabit Ethernet RJ45; 1 x SFP"),
            "vpn_protocols": t("IKEv2, IPsec, SSL VPN and L2TP over IPsec"),
            "controller_management": t(
                "Nebula Orchestrator in SD-WAN mode; standalone Web Configurator and CLI"
            ),
            "lan_interfaces": t("7 x configurable Gigabit Ethernet RJ45; 1 x SFP"),
            "uplink_interfaces": t("1 x SFP plus configurable Gigabit Ethernet RJ45 interfaces"),
            "vpn_throughput_mbps": n(1000),
            "concurrent_sessions": n(2000000),
            "vpn_tunnels": n(300),
            "wan_load_balancing": b(),
            "sd_wan": t(
                "Nebula Orchestrator SD-WAN with Dynamic Path Selection, WAN optimization, "
                "zero-touch provisioning and AutoVPN"
            ),
            "firewall_features": t(
                "DPI firewall; SSL inspection; content filtering; Geo Enforcer; Device HA Pro; "
                "two-factor authentication"
            ),
            "usb_interfaces": t("2 x USB 3.0"),
            "max_power_consumption_w": n(24.1),
            "dimensions_mm": t("300 x 188 x 44 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "WAX650S": {
        "source": "wax650s",
        "values": {
            "total_spatial_streams": n(8),
            "rate_2g_mbps": n(1150),
            "rate_5g_mbps": n(2400),
            "max_channel_width_mhz": n(160),
            "ethernet_interfaces": t("1 x 1/2.5/5GbE PoE port; 1 x 1GbE port"),
            "power_method": t("IEEE 802.3bt PoE (unrestricted) or 12 V DC input"),
            "mimo_2g": t("4x4 MU-MIMO"),
            "mimo_5g": t("4x4 MU-MIMO"),
            "antenna_type": t("4x4 internal Smart Antenna"),
            "antenna_gain_dbi": t("3 dBi at 2.4 GHz; 5.8 dBi at 5 GHz"),
            "centralized_management": t("Nebula cloud, on-premises controller, or standalone"),
            "mesh_support": b(),
            "fast_roaming": t("Pre-authentication, PMK caching and IEEE 802.11k/v/r"),
            "max_power_consumption_w": n(31),
            "dimensions_mm": t("230 x 235 x 53.5 mm"),
            "operating_temperature_c": t("0 to 50 °C"),
        },
    },
    "GS1350-6HP": {
        "source": "gs1350",
        "values": {
            "switching_capacity_gbps": n(12),
            "packet_forwarding_rate_mpps": n(8.9),
            "packet_buffer_mb": n(0.525),
            "power_supply": t("External 52-57 V DC power adapter"),
            "fan_design": t("Fanless"),
            "management_methods": GS1350_MANAGEMENT,
            "poe_configuration": t("5 PoE ports; ports 1-2 support PoE++ up to 60 W; 60 W total budget"),
            "poe_standard": t("IEEE 802.3af/802.3at PoE+; IEEE 802.3bt PoE++ on ports 1-2"),
            "poe_ports": n(5),
            "poe_budget_w": n(60),
            "max_poe_per_port_w": n(60),
            "vlan_count": n(256),
            "l2_features": GS1350_L2,
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; loop guard"),
            "acl_security": GS1350_SECURITY,
            "max_power_consumption_w": n(72),
            "dimensions_mm": t("193 x 84 x 26 mm"),
            "operating_temperature_c": t("-20 to 50 °C"),
        },
    },
    "GS1350-12HP": {
        "source": "gs1350",
        "values": {
            "packet_buffer_mb": n(0.525),
            "power_supply": t("Internal 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("Active cooling; 27.3 dBA acoustic noise at 25 °C"),
            "management_methods": GS1350_MANAGEMENT,
            "poe_configuration": t("8 x Gigabit PoE+ ports; 30 W per port; 130 W total budget"),
            "poe_standard": t("IEEE 802.3af/802.3at PoE+"),
            "poe_ports": n(8),
            "poe_budget_w": n(130),
            "max_poe_per_port_w": n(30),
            "vlan_count": n(256),
            "l2_features": GS1350_L2,
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; loop guard"),
            "acl_security": GS1350_SECURITY,
            "max_power_consumption_w": n(160.3),
            "dimensions_mm": t("267 x 162 x 44 mm"),
            "operating_temperature_c": t("-20 to 50 °C"),
        },
    },
    "GS1200-5": {
        "source": "gs1200",
        "values": {
            "ethernet_interfaces": t("5 x 10/100/1000Base-T RJ45"),
            "switching_capacity_gbps": n(10),
            "jumbo_frame_bytes": n(9216),
            "power_supply": t("External 5 V DC / 1 A power supply"),
            "fan_design": t("Fanless"),
            "management_methods": t("Web GUI"),
            "l2_features": GS1200_L2,
            "max_power_consumption_w": n(2.67),
            "dimensions_mm": t("121 x 75 x 26 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "GS1200-8": {
        "source": "gs1200",
        "values": {
            "switching_capacity_gbps": n(16),
            "jumbo_frame_bytes": n(9216),
            "power_supply": t("External 5 V DC / 1 A power supply"),
            "fan_design": t("Fanless"),
            "management_methods": t("Web GUI"),
            "l2_features": GS1200_L2,
            "max_power_consumption_w": n(4.37),
            "dimensions_mm": t("155 x 85 x 26 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "XMG1930-30": {
        "source": "xmg1930",
        "values": {
            "switching_capacity_gbps": n(240),
            "packet_forwarding_rate_mpps": n(178.5),
            "jumbo_frame_bytes": n(12288),
            "power_supply": t("Internal 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("Active cooling; 26-47.6 dBA acoustic noise at 25 °C"),
            "management_methods": XMG_MANAGEMENT,
            "vlan_count": n(1000),
            "l2_features": XMG_L2,
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; loop guard"),
            "acl_security": XMG_SECURITY,
            "max_power_consumption_w": n(67.1),
            "dimensions_mm": t("441 x 270 x 44 mm"),
            "operating_temperature_c": t("-20 to 50 °C"),
        },
    },
    "XMG1930-30HP": {
        "source": "xmg1930",
        "values": {
            "switching_capacity_gbps": n(240),
            "packet_forwarding_rate_mpps": n(178.5),
            "jumbo_frame_bytes": n(12288),
            "power_supply": t("Internal 100-240 V AC, 50/60 Hz power supply"),
            "fan_design": t("Active cooling; 27.9-51.6 dBA acoustic noise at 25 °C"),
            "management_methods": XMG_MANAGEMENT,
            "poe_configuration": t(
                "28 PoE ports: ports 1-20 PoE+; ports 21-24 2.5GbE PoE++; "
                "ports 25-28 10GbE PoE++; 700 W total budget"
            ),
            "poe_ports": n(28),
            "vlan_count": n(1000),
            "l2_features": XMG_L2,
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; loop guard"),
            "acl_security": XMG_SECURITY,
            "max_power_consumption_w": n(864.1),
            "dimensions_mm": t("441 x 330 x 44 mm"),
            "operating_temperature_c": t("-20 to 50 °C"),
        },
    },
}


SOURCES = {
    "fwa710": {
        "url": FWA710_URL,
        "version": "Official datasheet version 3, released 2024-04-15",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel Nebula FWA710 Datasheet",
        "location": "System, hardware, physical and environmental specifications, pp. 4-5",
        "note": "Manually verified from Zyxel's official exact-model datasheet version 3.",
    },
    "vpn300": {
        "url": VPN300_URL,
        "version": "Official Security Quick Sales Guide; ZLD 4.31 or later",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel Security Portfolio Firewall Comparison Matrix",
        "location": "Advanced ZyWALL VPN Firewalls matrix, pp. 12-13",
        "note": (
            "Manually verified against the official VPN300 comparison matrix and the newer V5.37 "
            f"user guide ({VPN300_GUIDE_URL}) for WAN load balancing behavior."
        ),
    },
    "wax650s": {
        "url": WAX650S_URL,
        "version": "Official datasheet version 8, released 2024-04-08",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel WAX650S Datasheet",
        "location": "Wireless, management, physical and environmental specifications, pp. 4-5",
        "note": (
            "Manually verified from Zyxel's official exact-model datasheet version 8. The official "
            "160 MHz bandwidth replaces the prior 80 MHz database value."
        ),
    },
    "gs1350": {
        "url": GS1350_URL,
        "version": "Official datasheet version 6, released 2024-05-14; includes V4.90 features",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel GS1350 Series Datasheet",
        "location": "Model specification table and feature lists, pp. 4-6",
        "note": "Manually verified from the exact model columns in Zyxel's official series datasheet.",
    },
    "gs1200": {
        "url": GS1200_URL,
        "version": "Current official specifications page, accessed 2026-10-14",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Zyxel GS1200 Series Specifications",
        "location": "GS1200-5 and GS1200-8 columns in the official specification table",
        "note": "Manually verified from Zyxel's current official model comparison table.",
    },
    "xmg1930": {
        "url": XMG1930_URL,
        "version": "Official datasheet version 5, released 2024-04-26; includes V4.80 features",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Zyxel XMG1930 Series Datasheet",
        "location": "Model specification table and feature lists, pp. 5-7",
        "note": (
            "Manually verified from the exact model columns in Zyxel's official version 5 datasheet. "
            "The XMG1930-30HP PoE port count is corrected to the official total of 28."
        ),
    },
}


RAW_VALUES = {
    ("FWA710", "max_power_consumption_w"): "< 15 W (estimated)",
    ("GS1350-6HP", "packet_buffer_mb"): "525 K bytes",
    ("GS1350-12HP", "packet_buffer_mb"): "525 K bytes",
    ("GS1200-5", "jumbo_frame_bytes"): "Up to 9 KB",
    ("GS1200-8", "jumbo_frame_bytes"): "Up to 9 KB",
    ("XMG1930-30", "jumbo_frame_bytes"): "12 K bytes",
    ("XMG1930-30HP", "jumbo_frame_bytes"): "12 K bytes",
}


class Command(BaseCommand):
    help = "Import manually verified Zyxel priority specifications (round 9)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Zyxel").first()
        if not brand:
            raise CommandError("Missing brand: Zyxel")

        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, row in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version=row["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": row["type"],
                    "title": row["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = 0
        per_model = []
        missing_models = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            source = documents[item["source"]]
            source_meta = SOURCES[item["source"]]
            model_new = model_corrected = 0
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
                old_value = None
                if had_value:
                    old_value = (
                        existing.value_text
                        if existing.value_text
                        else existing.value_number
                        if existing.value_number is not None
                        else existing.value_boolean
                    )

                raw_value = RAW_VALUES.get((model, code), str(value))
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
                    new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                    new_value = bool(value)
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)

                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had_value:
                    newly_filled += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1

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
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={newly_filled} "
                f"corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)-len(missing_models)}"
            )
        )
        self.stdout.write("; ".join(per_model))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
