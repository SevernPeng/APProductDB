from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


S6550_PAGE_URL = (
    "https://www.h3c.com/en/Products_and_Solutions/InterConnect/Switches/Products/"
    "Campus_Network/Aggregation/S6500/H3C_S6550X_HI/"
)
S6550_HARDWARE_URL = "https://www.h3c.com/en/d_202206/1633342_294551_0.htm"
S5570_PAGE_URL = (
    "https://www.h3c.com/en/Products_and_Solutions/InterConnect/Switches/Products/"
    "Campus_Network/Aggregation/S5500/H3C_S5570S-EI/"
)
S5570_HARDWARE_URL = (
    "https://www.h3c.com/en/Support/Resource_Center/EN/Home/Public/00-Public/"
    "Technical_Documents/Product_Literature/Hardware_Information___Specifications/"
    "S5170-EI_S5570S-10802/202511/2690609_294551_0.htm"
)


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


S5570_COMMON = {
    "jumbo_frame_bytes": n(12288),
    "management_methods": t(
        "CLI; console; Telnet; SSH 2.0; SNMP v1/v2c/v3; web NMS; H3C IMC; "
        "SmartMC; RESTful/RESTCONF API; Python; RMON; telemetry/gRPC"
    ),
    "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
    "vlan_count": n(4094),
    "l2_features": t(
        "Static/dynamic/cross-device link aggregation; port/MAC/protocol-based VLAN; "
        "QinQ/selective QinQ; VLAN mapping; Voice VLAN; GVRP; LLDP/LLDP-MED; "
        "Smart Link; RRPP; G.8032 ERPS; IGMP/MLD snooping"
    ),
    "stp_features": t("STP; RSTP; MSTP; PVST/PVST+/RPVST+; BPDU guard; root guard"),
    "acl_security": t(
        "Layer 2-4 packet filtering; time-range, VLAN and bidirectional ACLs; AAA/RADIUS/"
        "HWTACACS+; 802.1X and MAC authentication; port security/isolation; IP Source Guard; "
        "DHCP snooping; dynamic ARP inspection; CPU protection; SSH 2.0; HTTPS"
    ),
    "ip_interface_capacity": t("1022 VLAN interfaces"),
    "routing_entry_capacity": t("12288 IPv4 routes; 8192 IPv6 unicast routes"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "stacking": t(
        "H3C IRF2 through standard Ethernet interfaces; local or remote stacking; "
        "distributed device management, link aggregation, and resilient routing"
    ),
    "stacking_bandwidth_gbps": n(80),
    "operating_temperature_c": t("-5 to 45 °C"),
}


MODELS = {
    "S5570S-28S-EI": {
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(96),
        **{code: value for code, value in S5570_COMMON.items() if not code.startswith("poe_")},
        "max_power_consumption_w": n(45),
        "dimensions_mm": t("440 x 360 x 43.6 mm (W x D x H)"),
    },
    "S5570S-54S-EI": {
        "switching_capacity_gbps": n(216),
        "packet_forwarding_rate_mpps": n(161),
        **{code: value for code, value in S5570_COMMON.items() if not code.startswith("poe_")},
        "max_power_consumption_w": n(61),
        "dimensions_mm": t("440 x 360 x 43.6 mm (W x D x H)"),
    },
    "S5570S-28S-HPWR-EI": {
        **S5570_COMMON,
        # Catalog omits the current official "-A" suffix; the current H3C
        # table lists S5570S-28S-HPWR-EI-A at 128 Gbps / 96 Mpps.
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(96),
        "poe_ports": n(24),
        "poe_budget_w": n(810),
        "max_poe_per_port_w": n(35),
        "max_power_consumption_w": n(873),
        "dimensions_mm": t("440 x 460 x 43.6 mm (W x D x H)"),
    },
    "S5570S-54S-PWR-EI-A": {
        **S5570_COMMON,
        "switching_capacity_gbps": n(216),
        "packet_forwarding_rate_mpps": n(161),
        "poe_ports": n(48),
        "poe_budget_w": n(1680),
        "max_poe_per_port_w": n(35),
        "max_power_consumption_w": n(1935),
        "dimensions_mm": t("440 x 400 x 44 mm (W x D x H)"),
    },
    "S6550X-56HF-HI": {
        "ethernet_interfaces": t("48 x 1/10/25G SFP28; 8 x 40/100G QSFP28"),
        "switching_capacity_gbps": n(4000),
        "packet_forwarding_rate_mpps": n(2800),
        "mac_address_table": t("256K entries maximum"),
        "packet_buffer_mb": n(24),
        "jumbo_frame_bytes": n(10000),
        "power_supply": t(
            "2 removable power-supply slots; supports PSR450-12A, PSR450-12A1, "
            "PSR450-12AHD, and PSR450-12D; 1+1 redundancy supported"
        ),
        "fan_design": t(
            "4 field-replaceable fan trays; forward or reverse airflow selectable by fan-tray model"
        ),
        "management_methods": t(
            "CLI; console; Telnet; SSH 2.0; SNMP v1/v2c/v3; SSL/HTTPS; FTP/TFTP; "
            "H3C IMC; SmartMC; NETCONF; Python; telemetry/gRPC; out-of-band management"
        ),
        "vlan_count": n(4094),
        "l2_features": t(
            "Static/dynamic link aggregation; LACP; LLDP/LLDP-MED; Smart Link; RRPP; "
            "VLANs; DHCP snooping/relay; VXLAN/EVPN; M-LAG; sFlow"
        ),
        "stp_features": t("STP; RSTP; MSTP; PVST+/RPVST+; STP root guard; BPDU guard"),
        "acl_security": t(
            "Layer 2-4 packet filtering; inbound/outbound and VLAN ACLs; AAA/RADIUS/HWTACACS; "
            "802.1X and MAC authentication; IP Source Guard; uRPF; port binding; SSH 2.0; HTTPS/SSL"
        ),
        "l3_features": t(
            "Static routing; RIPv1/v2/RIPng; OSPFv1/v2/v3; BGP/BGP4+; IS-IS/IS-ISv6; "
            "ECMP; VRRP/VRRPv3; IPv4/IPv6 policy-based routing; GRE; MPLS L3VPN; VPLS/VRF"
        ),
        "ip_interface_capacity": t("1K VLAN interfaces"),
        "routing_entry_capacity": t("504K IPv4 routes maximum; 252K IPv6 unicast routes maximum"),
        "ospf_support": b(),
        "rip_support": b(),
        "pbr_support": b(),
        "vrrp_support": b(),
        "multicast_routing": b(),
        "stacking": t(
            "H3C IRF2 through standard Ethernet ports; local and remote stacking; up to 4 members"
        ),
        "stacking_units": n(4),
        "max_power_consumption_w": n(328),
        "dimensions_mm": t("440 x 400 x 43.6 mm (W x D x H)"),
        "operating_temperature_c": t("-5 to 45 °C"),
    },
    "S6550X-32H-HI": {
        "jumbo_frame_bytes": n(10000),
        "management_methods": t(
            "CLI; console; Telnet; SSH 2.0; SNMP v1/v2c/v3; SSL/HTTPS; FTP/TFTP; "
            "H3C IMC; SmartMC; NETCONF; Python; telemetry/gRPC; out-of-band management"
        ),
        "vlan_count": n(4094),
        "l2_features": t(
            "Static/dynamic link aggregation; LACP; LLDP/LLDP-MED; Smart Link; RRPP; "
            "VLANs; DHCP snooping/relay; VXLAN/EVPN; M-LAG; sFlow"
        ),
        "stp_features": t("STP; RSTP; MSTP; PVST+/RPVST+; STP root guard; BPDU guard"),
        "ip_interface_capacity": t("1K VLAN interfaces"),
        "ospf_support": b(),
        "rip_support": b(),
        "pbr_support": b(),
        "stacking": t(
            "H3C IRF2 through standard Ethernet ports; local and remote stacking; up to 4 members"
        ),
        "stacking_units": n(4),
        "max_power_consumption_w": n("410.1"),
        "operating_temperature_c": t("-5 to 45 °C"),
    },
}


S5570_PAGE_CODES = {
    "switching_capacity_gbps",
    "packet_forwarding_rate_mpps",
    "jumbo_frame_bytes",
    "management_methods",
    "poe_standard",
    "vlan_count",
    "l2_features",
    "stp_features",
    "acl_security",
    "ip_interface_capacity",
    "routing_entry_capacity",
    "ospf_support",
    "rip_support",
    "pbr_support",
    "stacking",
    "stacking_bandwidth_gbps",
}


class Command(BaseCommand):
    help = "Import manually verified priority H3C S5570S-EI and S6550X-HI specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="H3C").first()
        if not brand:
            raise CommandError("Brand 'H3C' was not found.")

        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source_rows = {
            "s5570_page": (
                S5570_PAGE_URL,
                "Current official product page accessed 2026-10-12",
                SourceDocument.DocumentType.PRODUCT_PAGE,
                "H3C S5570S-EI Series High Performance Intelligent Ethernet Switch",
            ),
            "s5570_hardware": (
                S5570_HARDWARE_URL,
                "Hardware Information and Specifications, November 2025",
                SourceDocument.DocumentType.DATASHEET,
                "H3C S5170-EI & S5570S-EI Hardware Information and Specifications",
            ),
            "s6550_page": (
                S6550_PAGE_URL,
                "Current official product page accessed 2026-10-12",
                SourceDocument.DocumentType.PRODUCT_PAGE,
                "H3C S6550X-HI Series High-Density Intelligent Switch",
            ),
            "s6550_hardware": (
                S6550_HARDWARE_URL,
                "Hardware Information and Specifications 5W100",
                SourceDocument.DocumentType.DATASHEET,
                "H3C S6550X-HI Hardware Information and Specifications",
            ),
        }
        sources = {}
        for key, (url, version, document_type, title) in source_rows.items():
            sources[key], _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version=version,
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": document_type,
                    "title": title,
                    "region": "Global",
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
                if model.startswith("S6550"):
                    source_key = "s6550_hardware" if code in {
                        "power_supply", "fan_design"
                    } else "s6550_page"
                    note = "Manually verified from H3C's official S6550X-HI product and hardware documentation."
                else:
                    source_key = "s5570_page" if code in S5570_PAGE_CODES else "s5570_hardware"
                    note = (
                        "Manually verified from H3C's current S5570S-EI product page and November 2025 "
                        "hardware specifications. Configuration-dependent PoE and power fields record the "
                        "largest officially listed value for the exact model."
                    )
                source = sources[source_key]
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
                    "raw_value": str(value),
                    "source_url": source.url,
                    "source_note": note,
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
                    source_location=f"Official model/series specification tables and feature lists - {model}",
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
