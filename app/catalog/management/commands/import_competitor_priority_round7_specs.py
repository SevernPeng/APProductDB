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


UBIQUITI_URL = "https://techspecs.ui.com/unifi/switching/usw-enterprise-24-poe"
DLINK_URL = "https://www.dlink.com/en/-/media/business_products/dgs/dgs-3000/datasheet/dgs3000seriesdatasheetv400ww.pdf"
HUAWEI_URL = (
    "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/"
    "ff1febef8ee34c8aabbbaca7c8ae4cc1/M2T1A590N1002264988344000526/"
    "%E5%8D%8E%E4%B8%BA%20CloudEngine%20S5731-S%E7%B3%BB%E5%88%97%E5%A4%9A%E9%80%9F%E7%8E%87%E4%BA%A4%E6%8D%A2%E6%9C%BA%E5%BD%A9%E9%A1%B5.pdf"
)
HUAWEI_PORTFOLIO_URL = (
    "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/"
    "e3699311f3ee423da9628e7929e7e0ed/M2T1A669N960182480692273433/"
    "Intelligent%20Cloud-Network.pdf"
)
TRENDNET_URL = "https://www.trendnet.com/langen/support/support-detail.asp?prod=260_TI-PG50"
DAHUA_4210_URL = "https://www.dahuasecurity.com/uk/products/Transmission/PoE-Switches/Industrial-PoE-Switch/PFS4210-8GT-DP"
DAHUA_4207_URL = "https://www.dahuasecurity.com/it/products/transmission/poe-switches/industrial-poe-switch/pfs4207-4gt-dp"
DAHUA_3211_URL = "https://transmission.dahuasecurity.com/en/product-list/Business/Switches/PoESwitchForSecurity/PFS3211-8GT-120"


PRODUCTS = {
    ("Ubiquiti", "USW-Enterprise-24-PoE"): {
        "source": "ubiquiti",
        "values": {
            "power_supply": t("Internal 550 W AC/DC power supply; 100-240 V AC; USP RPS DC backup input"),
            "poe_standard": t("PoE and PoE+ output (up to PoE+)"),
            "poe_ports": n(24),
            "poe_budget_w": n(400),
            "max_poe_per_port_w": n(32),
            "vlan_count": n(1000),
            "l2_features": t(
                "LACP; STP/RSTP; QoS; advanced IGMP configuration and snooping; 802.1X; "
                "DHCP snooping and guarding; flow/storm control; port mirroring and isolation; "
                "LLDP-MED; voice VLAN; loop protection"
            ),
            "stp_features": t("STP and RSTP"),
            "acl_security": t(
                "128 IPv4 ACLs and 128 MAC ACLs; 802.1X; DHCP snooping and guarding; "
                "device/network isolation; MAC blocking and port restriction"
            ),
            "l3_features": t("DHCP server and relay; inter-VLAN routing; IPv4 static routing"),
            "routing_entry_capacity": t("256 IPv4 static routes"),
        },
    },
    ("D-Link", "DGS-3000-28XMP"): {
        "source": "dlink",
        "values": {
            "jumbo_frame_bytes": n(9216),
            "power_supply": t("Internal 100-240 V AC, 50/60 Hz power supply; redundant power supply supported"),
            "fan_design": t("2 x Smart Fan"),
            "management_methods": t(
                "Web GUI; CLI; console; Telnet; SSH v1/v2; SNMP v1/v2c/v3; RMON; "
                "D-Link Single IP Management; D-Link Network Assistant; Zero Touch Provisioning"
            ),
            "poe_ports": n(24),
            "max_poe_per_port_w": n(30),
            "vlan_count": n(4094),
            "l2_features": t(
                "802.1Q; GVRP; QinQ; private, voice, MAC-, protocol- and port-based VLANs; "
                "802.1AX/802.3ad link aggregation; ERPS; L2 protocol tunneling; IGMP/MLD snooping; "
                "port/RSPAN/flow mirroring"
            ),
            "l3_features": t("IPv4/IPv6 static routing; ARP and IPv6 Neighbor Discovery"),
            "routing_entry_capacity": t("16 IPv4 static routes and 16 IPv6 static routes"),
            "stacking": t("D-Link Single IP Management virtual stacking"),
            "stacking_units": n(32),
            "operating_temperature_c": t("-5 to 50 °C"),
        },
    },
    ("Huawei", "S5731-S24UN4X2Q"): {
        "source": "huawei",
        "values": {
            "management_methods": t(
                "Huawei cloud management and local management; SNMP v1/v2c/v3; RMON; web management; Netconf"
            ),
            "poe_standard": t("PoE++ (up to 90 W per port)"),
            "poe_ports": n(24),
            "poe_budget_w": n(2268),
            "max_poe_per_port_w": n(90),
            "vlan_count": n(4094),
            "l2_features": t(
                "LACP/E-Trunk; LLDP; GVRP; MUX, guest, voice, MAC-, protocol-, IP-subnet-, "
                "policy- and port-based VLANs; VLAN mapping; RRPP; SmartLink; SEP; ERPS; "
                "IGMP/MLD snooping"
            ),
            "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; BPDU, root and loop protection"),
            "acl_security": t(
                "Layer 2-Layer 4 ACLs; 802.1X, AAA, RADIUS and HWTACACS; IP/MAC/port/VLAN binding; "
                "port isolation and security; DoS/ARP/ICMP attack protection; SSH v2 and HTTPS"
            ),
            "ospf_support": b(),
            "rip_support": b(),
            "pbr_support": b(),
            "stacking": t("Intelligent iStack; up to 9 devices"),
            "stacking_units": n(9),
            "max_power_consumption_w": n(2571),
            "dimensions_mm": t("442 x 420 x 43.6 mm"),
        },
    },
    ("TRENDnet", "TI-PG50"): {
        "source": "trendnet",
        "values": {
            "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44),
            "mac_address_table": t("2000 entries"),
            "packet_buffer_mb": n(0.122),
            "jumbo_frame_bytes": n(9216),
            "power_supply": t(
                "Dual redundant 48-56 V DC inputs; external TI-S15052 power supply sold separately"
            ),
            "management_methods": t("Unmanaged; no management interface and not configurable"),
            "poe_configuration": t("4 x Gigabit PoE+ ports; 60-120 W total PoE budget"),
            "poe_standard": t("IEEE 802.3af/802.3at"),
            "poe_ports": n(4),
            "poe_budget_w": n(120),
            "max_poe_per_port_w": n(30),
            "max_power_consumption_w": n(2.24),
            "dimensions_mm": t("113 x 82 x 31 mm"),
            "operating_temperature_c": t("-40 to 75 °C"),
        },
    },
    ("Other", "Dahua PFS4210-8GT-DP"): {
        "source": "dahua_4210",
        "values": {
            "switching_capacity_gbps": n(28),
            "packet_forwarding_rate_mpps": n(14.88),
            "mac_address_table": t("8000 entries"),
            "packet_buffer_mb": n(0.5),
            "jumbo_frame_bytes": n(9000),
            "power_supply": t("48-57 V DC input; power adapter not included; redundant power input"),
            "management_methods": t("Web (HTTP/HTTPS); SNMP v1/v2c/v3; CLI; SSH; RMON"),
            "poe_configuration": t("8 x Gigabit PoE ports; ports 1-2 up to 90 W, ports 3-8 up to 30 W; 120 W total"),
            "poe_standard": t("IEEE 802.3af/802.3at/802.3bt and Hi-PoE"),
            "poe_ports": n(8),
            "poe_budget_w": n(120),
            "max_poe_per_port_w": n(90),
            "l2_features": t("802.1Q VLAN; static aggregation and LACP; port mirroring; flow control; multicast; DHCP client/server/snooping; ERPS"),
            "stp_features": t("ERPS ring protection; loop protection"),
            "acl_security": t("ACL; 802.1X; HTTPS/SSH; SNMPv3; IP source guard; static/dynamic ARP inspection; user management"),
            "max_power_consumption_w": n(120),
            "dimensions_mm": t("125.4 x 53.5 x 175 mm"),
            "operating_temperature_c": t("-40 to 75 °C"),
        },
    },
    ("Dahua", "PFS4207-4GT-DP"): {
        "source": "dahua_4207",
        "values": {
            "mac_address_table": t("4000 entries"),
            "packet_buffer_mb": n(0.219),
            "power_supply": t("48-57 V DC input; external DRL-48V120W1AA supply sold separately; redundant power input"),
            "management_methods": t("Web; SNMP v1/v2c/v3; CLI; SSH; HTTPS"),
            "poe_configuration": t("4 x Gigabit PoE ports; ports 1-2 up to 90 W, remaining PoE ports up to 30 W; 120 W total"),
            "poe_budget_w": n(120),
            "l2_features": t("802.1Q VLAN; static aggregation and LACP; port mirroring; flow control; multicast; DHCP client/server/snooping; ERPS"),
            "stp_features": t("ERPS ring protection; loop protection"),
            "dimensions_mm": t("94.4 x 53.5 x 135 mm"),
        },
    },
    ("Other", "Dahua PFS3211-8GT-120"): {
        "source": "dahua_3211",
        "values": {
            "switching_capacity_gbps": n(33),
            "packet_forwarding_rate_mpps": n(16.37),
            "packet_buffer_mb": n(0.219),
            "power_supply": t("48-57 V DC input"),
            "management_methods": t("Unmanaged switch"),
            "poe_configuration": t("8 x Gigabit PoE ports; ports 1-2 up to 90 W, ports 3-8 up to 30 W; 120 W total"),
            "poe_standard": t("IEEE 802.3af/802.3at/802.3bt and Hi-PoE"),
            "poe_ports": n(8),
            "poe_budget_w": n(120),
            "max_poe_per_port_w": n(90),
            "max_power_consumption_w": n(120),
            "dimensions_mm": t("150 x 110 x 42 mm"),
            "operating_temperature_c": t("-30 to 65 °C"),
        },
    },
}


SOURCES = {
    "ubiquiti": {
        "brand": "Ubiquiti",
        "url": UBIQUITI_URL,
        "version": "Current official Tech Specs page (accessed 2026-10-12; product marked Vintage)",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Ubiquiti Enterprise 24 PoE (Vintage) Tech Specs",
        "region": "Global",
        "location": "Overview, performance, Layer 2/3 features, hardware",
        "note": "Manually verified from Ubiquiti's current official Tech Specs page for the exact model.",
    },
    "dlink": {
        "brand": "D-Link",
        "url": DLINK_URL,
        "version": "DGS-3000 Series datasheet v4.00 WW, hardware B1, copyright 2020",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "D-Link DGS-3000 Series Managed Gigabit Switches Datasheet",
        "region": "Worldwide",
        "location": "Technical specifications pp. 5-9",
        "note": "Manually verified from D-Link's official DGS-3000 Series v4.00 worldwide datasheet for hardware B1.",
    },
    "huawei": {
        "brand": "Huawei",
        "url": HUAWEI_URL,
        "version": "Current official Chinese brochure, published 2026-05",
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "Huawei CloudEngine S5731-S Series Multi-GE Switches Brochure",
        "region": "China/Global product family",
        "location": "Product specifications and feature tables pp. 1, 5-10",
        "note": (
            "Manually verified primarily from Huawei's May 2026 official S5731-S Multi-GE brochure. "
            "The 90 W per-port PoE++ value is corroborated by Huawei's official Cloud-Network portfolio."
        ),
    },
    "trendnet": {
        "brand": "TRENDnet",
        "url": TRENDNET_URL,
        "version": "TI-PG50 hardware Version V2, official page and datasheet dated 2024-11-15",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "TRENDnet TI-PG50 Version V2 Official Specifications",
        "region": "Global",
        "location": "Version V2 overview and specification table",
        "note": (
            "Manually verified from TRENDnet's current official Version V2 page and linked November 2024 "
            "datasheet. The packet buffer converts 125 KB to 0.122 MiB (rounded to three decimals); "
            "the 9 KB jumbo-frame value is recorded "
            "as 9216 bytes. Device power consumption excludes powered-device output."
        ),
    },
    "dahua_4210": {
        "brand": "Other",
        "url": DAHUA_4210_URL,
        "version": "Current official product page; linked datasheet dated 2023-12-21",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Dahua PFS4210-8GT-DP Official Specifications",
        "region": "UK/Global model",
        "location": "Official hardware, performance, function and general specification tables",
        "note": "Manually verified from Dahua's current official product specification page for the exact model. Packet buffer converts 4 Mbits to 0.5 MB.",
    },
    "dahua_4207": {
        "brand": "Dahua",
        "url": DAHUA_4207_URL,
        "version": "Current official product page; linked datasheet dated 2023-12-26",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Dahua PFS4207-4GT-DP Official Specifications",
        "region": "Italy/Global model",
        "location": "Official hardware, performance, function and general specification tables",
        "note": "Manually verified from Dahua's current official product specification page for the exact model. Packet buffer converts 1.75 Mbits to 0.219 MB (rounded).",
    },
    "dahua_3211": {
        "brand": "Other",
        "url": DAHUA_3211_URL,
        "version": "Current official product page; V2.0 datasheet dated 2023-12-11",
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "Dahua PFS3211-8GT-120 Version 2.0 Official Specifications",
        "region": "Global",
        "location": "Official technical specification table",
        "note": "Manually verified from Dahua's current official page and Version 2.0 datasheet. Packet buffer converts 1.75 Mbits to 0.219 MB (rounded).",
    },
}


class Command(BaseCommand):
    help = "Import manually verified priority competitor switch specifications (round 7)."

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

        updated = 0
        newly_filled = 0
        missing_models = []
        for (brand_name, model), item in PRODUCTS.items():
            product = Product.objects.filter(
                brand=brands[brand_name], model=model, is_published=True
            ).first()
            if not product:
                missing_models.append(f"{brand_name} {model}")
                continue
            source_key = item["source"]
            source = source_documents[source_key]
            source_meta = SOURCES[source_key]
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
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": (
                        "4K VLAN"
                        if (brand_name, code) == ("Huawei", "vlan_count")
                        else "125 KB"
                        if (brand_name, code) == ("TRENDnet", "packet_buffer_mb")
                        else "9 KB"
                        if (brand_name, code) == ("TRENDnet", "jumbo_frame_bytes")
                        else str(value)
                    ),
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
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                newly_filled += int(not had_value)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{source_meta['location']} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {defaults['raw_value']}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        # Keep the separate official Huawei portfolio as direct evidence for the 90 W PoE++ claim.
        huawei_product = Product.objects.filter(
            brand=brands["Huawei"], model="S5731-S24UN4X2Q", is_published=True
        ).first()
        if huawei_product:
            portfolio, _ = SourceDocument.objects.update_or_create(
                url=HUAWEI_PORTFOLIO_URL,
                document_version="Official Intelligent Cloud-Network portfolio, published 2024",
                defaults={
                    "brand": brands["Huawei"],
                    "product": huawei_product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": "Huawei Intelligent Cloud-Network Product Portfolio",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            max_poe = ProductSpec.objects.get(
                product=huawei_product, definition=definitions["max_poe_per_port_w"]
            )
            SpecEvidence.objects.update_or_create(
                product_spec=max_poe,
                source_document=portfolio,
                source_location="S5731-S Series product portfolio table - S5731-S24UN4X2Q",
                defaults={
                    "source_excerpt": "PoE++: 90 W per port; maximum PoE budget: 2268 W",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={updated} newly_filled={newly_filled} "
                f"models={len(PRODUCTS) - len(missing_models)}"
            )
        )
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
