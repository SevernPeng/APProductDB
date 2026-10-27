from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SERIES_SOURCE_URL = "https://www.hpe.com/psnow/doc/a00097415enw.pdf"
SERIES_SOURCE_VERSION = "a00097415ENW Rev. 2 (2025)"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "mac_address_table": t("32,768 entries"),
    "packet_buffer_mb": n(8),
    "jumbo_frame_bytes": n(9198),
    "fan_design": t("Fixed fans"),
    "management_methods": t("HPE Aruba Networking Central; Web GUI; CLI; CX Mobile App; Switch Multi-Edit; REST API; SNMPv2c/v3; RMON; sFlow"),
    "vlan_count": n(2048),
    "l2_features": t("4094 VLAN IDs / 2048 simultaneous VLANs; LACP; IGMP/MLD snooping; QinQ; MVRP; RPVST+; port mirroring; VXLAN"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP; RPVST+; Root Guard"),
    "acl_security": t("IPv4/IPv6/MAC ACLs; 802.1X; MAC authentication; DHCP snooping; Dynamic ARP Protection; IP Source Lockdown; port security"),
    "l3_features": t("IPv4/IPv6 static routing; OSPFv2/v3; RIP/RIPng; PBR; VRRP; PIM-SM/SSM; ECMP"),
    "ip_interface_capacity": t("256 dual-stack switched virtual interfaces"),
    "routing_entry_capacity": t("2,048 IPv4 unicast routes; 1,024 IPv6 unicast routes"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "multicast_routing": b(),
    "stacking": t("Virtual Switching Framework (VSF), up to 8 members and 10 km between members"),
    "stacking_bandwidth_gbps": n(40),
    "stacking_units": n(8),
    "hot_patching": b(),
    "operating_temperature_c": t("0 to 45 °C up to 1,524 m; derate 1 °C per 305 m to 3,048 m"),
}


MODELS = {
    "6200F 24G 4SFP+ Switch (JL724A)": {
        "source_url": "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%20CX%206200F%2024G%204SFP%2B%20Switch%20Digital%20Data%20Sheet-PSN1012748960IEEN.pdf",
        "values": {
            "ethernet_interfaces": t("24 x 10/100/1000BASE-T; 4 x 1/10G SFP+; USB-C console; USB-A host; OOBM; Bluetooth adapter"),
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(95.2),
            "power_supply": t("Fixed 200 W AC power supply"),
            "max_power_consumption_w": n(59),
            "dimensions_mm": t("442 x 327 x 43.9 mm"),
        },
        "poe": False,
    },
    "6200F (JL725A)": {
        "source_url": "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%20CX%206200F%2024G%20Class4%20PoE%204SFP%2B%20370W%20Switch%20Digital%20Data%20Sheet-PSN1012749064ESEN.pdf",
        "values": {
            "ethernet_interfaces": t("24 x 10/100/1000BASE-T Class 4 PoE; 4 x 1/10G SFP+; USB-C console; USB-A host; OOBM; Bluetooth adapter"),
            "switching_capacity_gbps": n(128),
            "packet_forwarding_rate_mpps": n(95.2),
            "power_supply": t("Fixed 500 W AC power supply"),
            "poe_configuration": t("24 Class 4 PoE ports; 370 W PoE budget"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(24),
            "poe_budget_w": n(370),
            "max_poe_per_port_w": n(30),
            "max_power_consumption_w": n(65),
            "dimensions_mm": t("442 x 327 x 43.9 mm"),
        },
        "poe": True,
    },
    "6200F (JL726A)": {
        "source_url": "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%20CX%206200F%2048G%204SFP%2B%20Switch%20Digital%20Data%20Sheet-PSN1012749072PLEN.pdf",
        "values": {
            "ethernet_interfaces": t("48 x 10/100/1000BASE-T; 4 x 1/10G SFP+; USB-C console; USB-A host; OOBM; Bluetooth adapter"),
            "switching_capacity_gbps": n(176),
            "packet_forwarding_rate_mpps": n(130.9),
            "power_supply": t("Fixed 200 W AC power supply"),
            "max_power_consumption_w": n(68),
            "dimensions_mm": t("442 x 327 x 43.9 mm"),
        },
        "poe": False,
    },
    "6200F (JL728A)": {
        "source_url": "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%20CX%206200F%2048G%20Class4%20PoE%204SFP%2B%20740W%20Switch%20Digital%20Data%20Sheet-PSN1012748962ECEN.pdf",
        "values": {
            "ethernet_interfaces": t("48 x 10/100/1000BASE-T Class 4 PoE; 4 x 1/10G SFP+; USB-C console; USB-A host; OOBM; Bluetooth adapter"),
            "switching_capacity_gbps": n(176),
            "packet_forwarding_rate_mpps": n(130.9),
            "power_supply": t("Fixed 950 W AC power supply"),
            "poe_configuration": t("48 Class 4 PoE ports; 740 W PoE budget"),
            "poe_standard": t("IEEE 802.3af/at"),
            "poe_ports": n(48),
            "poe_budget_w": n(740),
            "max_poe_per_port_w": n(30),
            "max_power_consumption_w": n(76),
            "dimensions_mm": t("442 x 327 x 43.9 mm"),
        },
        "poe": True,
    },
}


POE_CODES = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


class Command(BaseCommand):
    help = "Import manually verified Aruba CX 6200F JL724A/JL725A/JL726A/JL728A specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Aruba").first()
        if not brand:
            raise CommandError("Brand 'Aruba' was not found.")
        codes = set(COMMON) | POE_CODES | {
            code for model_data in MODELS.values() for code in model_data["values"]
        }
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        series_source, _ = SourceDocument.objects.update_or_create(
            url=SERIES_SOURCE_URL,
            document_version=SERIES_SOURCE_VERSION,
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "HPE Aruba Networking CX 6200 Switch Series Data Sheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        updated = not_applicable = 0
        missing_models = []
        for model, model_data in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            model_source, _ = SourceDocument.objects.update_or_create(
                url=model_data["source_url"],
                document_version="Current digital data sheet (2026)",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"HPE Aruba Networking CX 6200F {model.split('(')[-1].rstrip(')')} Digital Data Sheet",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            values = {**COMMON, **model_data["values"]}
            model_specific = set(model_data["values"]) | {"operating_temperature_c", "management_methods", "stacking_units"}
            for code, (kind, data) in values.items():
                definition = definitions[code]
                source = model_source if code in model_specific else series_source
                source_url = model_data["source_url"] if source == model_source else SERIES_SOURCE_URL
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(data),
                    "unit": definition.unit,
                    "raw_value": str(data),
                    "source_url": source_url[:200],
                    "source_note": "Manually verified from current official HPE product and series data sheets; routing feature support reflects current AOS-CX 6200 documentation.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(data))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(data)
                else:
                    defaults["value_text"] = str(data)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=(
                        f"Technical specifications - {model}"
                        if source == model_source
                        else f"Features and technical capacity tables - CX 6200 series ({model})"
                    ),
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

            if not model_data["poe"]:
                for code in POE_CODES:
                    definition = definitions[code]
                    spec, _ = ProductSpec.objects.update_or_create(
                        product=product,
                        definition=definition,
                        defaults={
                            "value_status": ProductSpec.ValueStatus.NOT_APPLICABLE,
                            "value_text": "",
                            "value_number": None,
                            "value_boolean": None,
                            "normalized_value": "",
                            "unit": definition.unit,
                            "raw_value": "Non-PoE model",
                            "source_url": model_data["source_url"][:200],
                            "source_note": "The current official HPE digital data sheet identifies this SKU as non-PoE.",
                            "verified_date": accessed,
                        },
                    )
                    SpecEvidence.objects.update_or_create(
                        product_spec=spec,
                        source_document=model_source,
                        source_location=f"Technical specifications - {model}",
                        defaults={
                            "source_excerpt": "PoE capability: Non-PoE model",
                            "evidence_level": SpecEvidence.EvidenceLevel.A,
                            "verified_at": timezone.now(),
                        },
                    )
                    not_applicable += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={updated} not_applicable={not_applicable} models={len(MODELS) - len(missing_models)}"
        ))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
