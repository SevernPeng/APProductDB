from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "7750": {
        "url": "https://webresources.vistancenetworks.com/download/assets/Ruckus%2BICX%2B7750%2BSwitch%2BData%2BSheet/7b08946ad7ae11f08029be274297c0a4",
        "version": "PA-113853.1-EN (04/20)",
        "title": "RUCKUS ICX 7750 Enterprise-Class Aggregation/Core Switch Data Sheet",
    },
    "7850": {
        "url": "https://webresources.vistancenetworks.com/download/assets/Ruckus%2BICX%2B7850%2BSwitch%2BData%2BSheet/3b8386cad7a311f0b2dbfa7a03f65a78",
        "version": "PA-113851.6-EN (08/26)",
        "title": "RUCKUS ICX 7850 Enterprise Aggregation/Core Stackable Switch Data Sheet",
    },
}


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON_FEATURES = {
    "management_methods": t("Web (HTTP/HTTPS); CLI; SSH; Telnet; SNMPv1/v2c/v3; sFlow; SmartZone; RUCKUS One; RUCKUS Unleashed"),
    "l2_features": t("MSTP; PVST/PVST+/PVRST; IGMP/MLD snooping; LACP; Q-in-Q; private VLAN; MRP; VSRP; VXLAN; port/VLAN/ACL mirroring"),
    "stp_features": t("STP; RSTP; MSTP; PVST/PVST+/PVRST; BPDU Guard; Root Guard"),
    "acl_security": t("Port and Layer 3/4 ACLs; 802.1X; MAC/Web authentication; DHCP snooping; Dynamic ARP Inspection; TPM"),
    "l3_features": t("IPv4/IPv6 static routing, RIP/RIPng and ECMP; OSPF, PIM, PBR, VRRP, BGP and VRF with advanced L3 entitlement"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "multicast_routing": b(),
    "stacking_units": n(12),
}


FAMILY_VALUES = {
    "7750": {
        **COMMON_FEATURES,
        "mac_address_table": t("96,000 in switch profile; 32,000 in router profile"),
        "packet_buffer_mb": n(12.2),
        "jumbo_frame_bytes": n(9216),
        "power_supply": t("Up to 2 x 500 W hot-swappable AC or DC power supplies"),
        "fan_design": t("Four hot-swappable fans with reversible airflow"),
        "vlan_count": n(4096),
        "ip_interface_capacity": t("512 virtual Ethernet interfaces"),
        "routing_entry_capacity": t("Up to 128K IPv4 routes, 7K IPv6 routes, and 16K next-hop addresses"),
        "stacking": t("Up to 12 ICX 7750 switches; up to 10 km between switches"),
        "stacking_bandwidth_gbps": n(5760),
        "operating_temperature_c": t("-5 to 45 °C; up to 50 °C at sea level"),
    },
    "7850": {
        **COMMON_FEATURES,
        "mac_address_table": t("Up to 288,000 entries; multiple hardware profiles available"),
        "packet_buffer_mb": n(32),
        "jumbo_frame_bytes": n(9216),
        "power_supply": t("2 x 650 W hot-swappable, load-sharing power supplies"),
        "fan_design": t("Hot-swappable fan assemblies with reversible front-to-back or back-to-front airflow"),
        "vlan_count": n(4095),
        "ip_interface_capacity": t("512 virtual Ethernet interfaces"),
        "routing_entry_capacity": t("Up to 300K IPv4 routes, 35K IPv6 routes, and 62K next-hop addresses"),
        "stacking": t("Up to 12 ICX 7850 switches; up to 10 km between switches"),
        "stacking_bandwidth_gbps": n(9600),
        "operating_temperature_c": t("0 to 45 °C"),
    },
}


MODELS = {
    "ICX 7750-48F": ("7750", {
        "ethernet_interfaces": t("48 x 1/10GbE SFP+; 6 x 40GbE QSFP+; one modular interface slot"),
        "switching_capacity_gbps": n(1920),
        "packet_forwarding_rate_mpps": n(1440),
        "max_power_consumption_w": n(327),
        "dimensions_mm": t("440 x 406.4 x 43.6 mm"),
    }),
    "ICX 7850-32Q": ("7850", {
        "ethernet_interfaces": t("32 x 40/100GbE QSFP28 ports; breakout to 4 x 10GbE or 4 x 25GbE"),
        "switching_capacity_gbps": n(6400),
        "packet_forwarding_rate_mpps": n(4000),
        "max_power_consumption_w": n(479.6),
        "dimensions_mm": t("440 x 444.5 x 43.7 mm"),
    }),
    "ICX 7850-48F": ("7850", {
        "ethernet_interfaces": t("48 x 1/10/25GbE SFP28; 8 x 40/100GbE QSFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(4000),
        "packet_forwarding_rate_mpps": n(4000),
        "max_power_consumption_w": n(396.2),
        "dimensions_mm": t("440 x 444.5 x 43.7 mm"),
    }),
}


POE_CODES = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


class Command(BaseCommand):
    help = "Import manually verified RUCKUS ICX 7750 and ICX 7850 core-switch specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Brand 'RUCKUS' was not found.")
        codes = POE_CODES | {code for values in FAMILY_VALUES.values() for code in values}
        codes |= {code for _, values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        documents = {}
        for family, source_data in SOURCES.items():
            documents[family], _ = SourceDocument.objects.update_or_create(
                url=source_data["url"],
                document_version=source_data["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": source_data["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        updated = not_applicable = 0
        missing_models = []
        for model, (family, model_values) in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            source_data = SOURCES[family]
            values = {**FAMILY_VALUES[family], **model_values}
            for code, (kind, data) in values.items():
                definition = definitions[code]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(data),
                    "unit": definition.unit,
                    "raw_value": str(data),
                    "source_url": source_data["url"][:200],
                    "source_note": f"Manually verified from official RUCKUS data sheet {source_data['version']}.",
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
                    source_document=documents[family],
                    source_location=f"Feature/model comparison and specifications - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

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
                        "raw_value": "Not a PoE model",
                        "source_url": source_data["url"][:200],
                        "source_note": "The official model comparison identifies this core switch as non-PoE.",
                        "verified_date": accessed,
                    },
                )
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[family],
                    source_location=f"Feature/model comparison - {model}",
                    defaults={
                        "source_excerpt": "Non-PoE interface configuration",
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
