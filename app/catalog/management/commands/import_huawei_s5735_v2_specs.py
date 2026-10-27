from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


L_SOURCE_URL = (
    "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/"
    "3dde65015538492bbb10a6e7afd764b9/M3T1A590N1221517367813062776/"
    "Huawei%20CloudEngine%20S5735-L-V2%20Series%202_5GE%20Switches%20Datasheet.pdf"
)
S_PAGE_URL = "https://e.huawei.com/cn/products/switches/campus-switches/s5735-s-c-v2"
S_BROCHURE_URL = (
    "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/"
    "a49550d8660b45328e1672a6a9e0352c/M3T1A590N1165604074751701077/"
    "%E5%8D%8E%E4%B8%BA%20CloudEngine%20S5735-S-C-V2%E7%B3%BB%E5%88%97"
    "%E9%98%B2%E6%8A%A4%E4%B8%93%E6%AC%BE%E4%BA%A4%E6%8D%A2%E6%9C%BA"
    "%E5%BD%A9%E9%A1%B5.pdf"
)

SHORT_SOURCE_URLS = {
    "l": "https://e.huawei.com/en/products/switches/campus-switches/s5735-l-v2-ge",
    "s_page": S_PAGE_URL,
    "s_brochure": "https://e.huawei.com/en/documents/products/enterprise-network/457b3aaa01e4464a866a943f68c57491",
}


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


L_COMMON = {
    "management_methods": t(
        "CLI; SSH v2; SNMP v1/v2c/v3; web NMS/HTTPS; RMON; Telnet; "
        "NETCONF/YANG cloud management; eSight; telemetry"
    ),
    "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
    "max_poe_per_port_w": n(30),
    "vlan_count": n(4094),
    "l2_features": t(
        "Voice/MUX VLAN; VLAN stacking and mapping; GVRP; LACP/Eth-Trunk; "
        "LLDP/LLDP-MED; Smart Link; ERPS G.8032; SEP; IGMP/MLD snooping"
    ),
    "stp_features": t(
        "STP; RSTP; MSTP; VBST; BPDU protection; root protection; loop protection; BPDU tunnel"
    ),
    "acl_security": t(
        "IPv4/IPv6 ACLs; Layer 2-4 packet filtering; 802.1X/Portal/MAC authentication; "
        "AAA/RADIUS/HWTACACS/NAC; DHCP snooping; port security; DoS/ARP/ICMP defense"
    ),
    "ip_interface_capacity": t("1024 VLANIF interfaces"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "stacking": t("Huawei iStack; two dedicated 12GE stack ports; up to 9 devices"),
    "stacking_bandwidth_gbps": n(80),
    "stacking_units": n(9),
    "dimensions_mm": t("442 x 420 x 43.6 mm (W x D x H)"),
    "operating_temperature_c": t(
        "-5 to 45 °C at 0-1800 m; maximum temperature derates 1 °C per 220 m above 1800 m"
    ),
}


MODELS = {
    "S5735-L24PN4XE-A-V2": {
        **L_COMMON,
        "poe_ports": n(24),
        "poe_budget_w": n(400),
        "max_power_consumption_w": n("517.3"),
    },
    "S5735-L48LPN4XE-A-V2": {
        **L_COMMON,
        "poe_ports": n(48),
        "poe_budget_w": n(360),
        "max_power_consumption_w": n("512.5"),
    },
    "S5735-S24T4XE-C-V2": {
        "switching_capacity_gbps": n(1360),
        "packet_forwarding_rate_mpps": n(291),
        "management_methods": t(
            "NETCONF/YANG cloud management; SNMP v1/v2c/v3; RMON; NMS; SSH v2; HTTPS; local and cloud management"
        ),
        "vlan_count": n(4094),
        "l2_features": t(
            "Voice/MUX VLAN; basic and flexible QinQ; Smart Link; ERPS G.8032; LLDP; "
            "IGMP/MLD snooping; LACP; port mirroring"
        ),
        "stp_features": t("STP; RSTP; MSTP; VBST; BPDU protection; root protection; loop protection"),
        "acl_security": t(
            "Layer 2-4 packet filtering and ACLs; 802.1X/MAC authentication; AAA/RADIUS/HWTACACS/NAC; "
            "DHCP snooping; port security; DoS/ARP/ICMP defense; CPU protection"
        ),
        "routing_entry_capacity": t("8192 IPv4 FIB entries; 3072 IPv6 FIB entries"),
        "ospf_support": b(),
        "rip_support": b(),
        "pbr_support": b(),
        "vrrp_support": b(),
        "stacking": t("Huawei iStack supported; two dedicated 12GE stack ports"),
        "max_power_consumption_w": n("33.1"),
        "dimensions_mm": t("442 x 420 x 43.6 mm (W x D x H)"),
        "operating_temperature_c": t("-5 to 50 °C at 0-1800 m; industrial optical modules required"),
    },
}


L_LOCATIONS = {
    "management_methods": "Easy O&M and functions table, pp. 2-7",
    "poe_standard": "Power supply table and standards list, pp. 2 and 15",
    "poe_ports": "Models and appearances, p. 1",
    "poe_budget_w": "Power supply configurations, p. 2",
    "max_poe_per_port_w": "Power supply configurations, p. 2",
    "vlan_count": "Functions and features, p. 4",
    "l2_features": "Functions and features, pp. 4-5",
    "stp_features": "Functions and features, p. 5",
    "acl_security": "Functions and features, pp. 5-6",
    "ip_interface_capacity": "Functions and features, p. 4",
    "ospf_support": "IP routing, p. 5",
    "rip_support": "IP routing, p. 5",
    "pbr_support": "IP routing, p. 5",
    "stacking": "iStack and management, pp. 3 and 6",
    "stacking_bandwidth_gbps": "Management and maintenance, p. 6",
    "stacking_units": "Management and maintenance, p. 6",
    "max_power_consumption_w": "Hardware specifications, p. 8",
    "dimensions_mm": "Hardware specifications, p. 7",
    "operating_temperature_c": "Hardware specifications, p. 8",
}


S_PAGE_CODES = {"switching_capacity_gbps", "packet_forwarding_rate_mpps", "vlan_count"}
S_LOCATIONS = {
    "switching_capacity_gbps": "Current product specifications table",
    "packet_forwarding_rate_mpps": "Current product specifications table",
    "management_methods": "Management and maintenance, brochure pp. 7-8",
    "vlan_count": "Current product specifications table",
    "l2_features": "Service features, brochure pp. 5-8",
    "stp_features": "Service features, brochure p. 5",
    "acl_security": "Service features, brochure pp. 6-7",
    "routing_entry_capacity": "IP routing, brochure p. 6",
    "ospf_support": "IP routing, brochure pp. 2 and 5-6",
    "rip_support": "IP routing, brochure p. 5",
    "pbr_support": "IP routing, brochure p. 5",
    "vrrp_support": "IP routing, brochure pp. 2 and 5",
    "stacking": "Model description and management, brochure pp. 1 and 7",
    "max_power_consumption_w": "Hardware specifications, brochure p. 4",
    "dimensions_mm": "Hardware specifications, brochure p. 4",
    "operating_temperature_c": "Hardware specifications, brochure p. 4",
}


class Command(BaseCommand):
    help = "Import manually verified Huawei CloudEngine S5735-L/S-C V2 specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Huawei").first()
        if not brand:
            raise CommandError("Brand 'Huawei' was not found.")

        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        sources = {}
        source_rows = (
            (
                "l",
                L_SOURCE_URL,
                "2026 official datasheet",
                SourceDocument.DocumentType.DATASHEET,
                "Huawei CloudEngine S5735-L-V2 Series 2.5GE Switches Datasheet",
                "Global",
            ),
            (
                "s_page",
                S_PAGE_URL,
                "Current product page accessed 2026-10-12",
                SourceDocument.DocumentType.PRODUCT_PAGE,
                "Huawei CloudEngine S5735-S-C-V2 Series Product Page",
                "China",
            ),
            (
                "s_brochure",
                S_BROCHURE_URL,
                "Official brochure, copyright 2023",
                SourceDocument.DocumentType.DATASHEET,
                "Huawei CloudEngine S5735-S-C-V2 Series Guarding Switches Brochure",
                "China",
            ),
        )
        for key, url, version, document_type, title, region in source_rows:
            sources[key], _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version=version,
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": document_type,
                    "title": title,
                    "region": region,
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        updated = 0
        newly_filled = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            for code, (kind, value) in values.items():
                definition = definitions[code]
                if model.startswith("S5735-L"):
                    source_key = "l"
                    location = L_LOCATIONS[code]
                    note = "Manually verified from Huawei's 2026 official S5735-L-V2 2.5GE series datasheet."
                elif code in S_PAGE_CODES:
                    source_key = "s_page"
                    location = S_LOCATIONS[code]
                    note = (
                        "Manually verified from Huawei's current official product page. For slash-separated "
                        "performance values, the first published model value is recorded."
                    )
                else:
                    source_key = "s_brochure"
                    location = S_LOCATIONS[code]
                    note = "Manually verified from Huawei's official S5735-S-C-V2 series brochure."

                source = sources[source_key]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": str(value),
                    "source_url": SHORT_SOURCE_URLS[source_key],
                    "source_note": note,
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                else:
                    defaults["value_text"] = str(value)

                spec, created = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                newly_filled += int(created)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"{location} - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {value}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={updated} newly_filled={newly_filled} "
                f"models={len(MODELS) - len(missing_models)}"
            )
        )
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
