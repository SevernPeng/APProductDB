from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, ProductType, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://webresources.vistancenetworks.com/download/assets/PA-117001.3-EN_RUCKUS%2BICX%2B8200%2BDS_FINAL_LR.pdf/3b4a7128d7a311f0bbd3e674d717417b"
SOURCE_VERSION = "PA-117001.4-EN (07/26)"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "mac_address_table": t("32,768 entries"),
    "packet_buffer_mb": n(4),
    "jumbo_frame_bytes": n(9216),
    "management_methods": t("Web (HTTP/HTTPS); CLI; SSH; Telnet; SNMPv1/v2c/v3; sFlow; SmartZone; RUCKUS One; RUCKUS Unleashed"),
    "vlan_count": n(4095),
    "l2_features": t("MSTP; PVST/PVST+/RPVST; IGMP/MLD snooping; LACP; Q-in-Q; private VLAN; MRP; VSRP; port/VLAN/ACL mirroring"),
    "stp_features": t("STP; RSTP; MSTP; PVST/PVST+/RPVST; BPDU Guard; Root Guard"),
    "acl_security": t("Port and Layer 3/4 ACLs; 802.1X; MAC/Web authentication; DHCP snooping; Dynamic ARP Inspection; Neighbor Discovery Inspection; TPM"),
    "l3_features": t("IPv4/IPv6 static routing, RIP/RIPng and ECMP; OSPFv2/v3, PIM, PBR, VRRP, VRF, GRE, BGP and VXLAN with premium license"),
    "ip_interface_capacity": t("512 virtual Ethernet interfaces"),
    "routing_entry_capacity": t("16K IPv4 routes; 4K IPv6 routes; 8K next-hop addresses"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "multicast_routing": b(),
    "stacking": t("Up to 12 ICX 8200 switches; long-distance stacking up to 10 km"),
    "stacking_bandwidth_gbps": n(1200),
    "stacking_units": n(12),
    "operating_temperature_c": t("0 to 45 °C"),
}


MODEL_VALUES = {
    "ICX 8200-24": {
        "ethernet_interfaces": t("24 x 10/100/1000 Mbps RJ45; 4 x 1/10/25GbE SFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(248),
        "packet_forwarding_rate_mpps": n(184),
        "power_supply": t("Integrated 65 W AC power supply"),
        "fan_design": t("Fanless"),
        "max_power_consumption_w": n(38),
        "dimensions_mm": t("440 x 280 x 44 mm"),
    },
    "ICX 8200-24P": {
        "ethernet_interfaces": t("24 x 10/100/1000 Mbps PoE+ RJ45; 4 x 1/10/25GbE SFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(248),
        "packet_forwarding_rate_mpps": n(184),
        "power_supply": t("Integrated 525 W AC power supply"),
        "fan_design": t("Front and side-to-back airflow; configurable fanless mode"),
        "poe_configuration": t("24 x PoE+ ports; 370 W PoE budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(24),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(445),
        "dimensions_mm": t("440 x 280 x 44 mm"),
    },
    "ICX 8200-24ZP": {
        "ethernet_interfaces": t("24 x 100/1000/2500 Mbps PoE+++ RJ45; 4 x 1/10/25GbE SFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(320),
        "packet_forwarding_rate_mpps": n(237),
        "power_supply": t("Integrated 950 W AC power supply"),
        "fan_design": t("Front and side-to-back airflow"),
        "poe_configuration": t("24 x multigigabit PoE+++ ports; 740 W PoE budget"),
        "poe_standard": t("IEEE 802.3af/at/bt"),
        "poe_ports": n(24),
        "poe_budget_w": n(740),
        "max_poe_per_port_w": n(90),
        "max_power_consumption_w": n(920),
        "dimensions_mm": t("440 x 280 x 44 mm"),
    },
    "ICX 8200-48": {
        "ethernet_interfaces": t("48 x 10/100/1000 Mbps RJ45; 4 x 1/10/25GbE SFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(296),
        "packet_forwarding_rate_mpps": n(220),
        "power_supply": t("Integrated 100 W AC power supply"),
        "fan_design": t("Fanless"),
        "max_power_consumption_w": n(54),
        "dimensions_mm": t("440 x 370 x 44 mm"),
    },
    "ICX 8200-48PF2": {
        "ethernet_interfaces": t("48 x 10/100/1000 Mbps PoE+ RJ45; 4 x 1/10/25GbE SFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(296),
        "packet_forwarding_rate_mpps": n(220),
        "power_supply": t("Up to 2 x 920 W hot-swappable, load-sharing AC power supplies"),
        "fan_design": t("Dual hot-swappable fans; front-to-back airflow"),
        "poe_configuration": t("48 x PoE+ ports; 840 W with one PSU or 1,480 W with two"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(1480),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(1667),
        "dimensions_mm": t("440 x 370 x 44 mm"),
    },
    "ICX 8200-48ZP2": {
        "ethernet_interfaces": t("32 x 10/100/1000 Mbps PoE+ RJ45; 16 x 100/1000/2500 Mbps PoE+++ RJ45; 4 x 1/10/25GbE SFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(344),
        "packet_forwarding_rate_mpps": n(254),
        "power_supply": t("Up to 2 x 920 W hot-swappable, load-sharing AC power supplies"),
        "fan_design": t("Dual hot-swappable fans; front-to-back airflow"),
        "poe_configuration": t("32 x PoE+ and 16 x multigigabit PoE+++ ports; 800 W with one PSU or 1,480 W with two"),
        "poe_standard": t("IEEE 802.3af/at/bt"),
        "poe_ports": n(48),
        "poe_budget_w": n(1480),
        "max_poe_per_port_w": n(90),
        "max_power_consumption_w": n(1839),
        "dimensions_mm": t("440 x 370 x 44 mm"),
    },
    "ICX8200-24F": {
        "ethernet_interfaces": t("24 x 100/1000 Mbps SFP; 4 x 1/10/25GbE SFP28 uplink/stacking ports"),
        "switching_capacity_gbps": n(248),
        "packet_forwarding_rate_mpps": n(184),
        "power_supply": t("Integrated 100 W AC power supply"),
        "fan_design": t("Front and side-to-back airflow"),
        "max_power_consumption_w": n(78),
        "dimensions_mm": t("440 x 280 x 44 mm"),
    },
    "ICX 8200-24FX": {
        "ethernet_interfaces": t("16 x 1/10GbE SFP+; 8 x 1/10/25GbE SFP28 ports"),
        "switching_capacity_gbps": n(720),
        "packet_forwarding_rate_mpps": n(533),
        "power_supply": t("Integrated 150 W AC power supply"),
        "fan_design": t("Front and side-to-back airflow"),
        "max_power_consumption_w": n(93),
        "dimensions_mm": t("440 x 280 x 44 mm"),
    },
}


POE_MODELS = {"ICX 8200-24P", "ICX 8200-24ZP", "ICX 8200-48PF2", "ICX 8200-48ZP2"}
POE_CODES = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


class Command(BaseCommand):
    help = "Import manually verified RUCKUS ICX 8200 specs from the July 2026 official data sheet."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Brand 'RUCKUS' was not found.")
        product_types = {
            item.code: item
            for item in ProductType.objects.filter(
                category__slug="managed-switches", code__in=("campus_poe", "campus_non_poe")
            )
        }
        if set(product_types) != {"campus_poe", "campus_non_poe"}:
            raise CommandError("Managed-switch campus product types were not found.")
        codes = set(COMMON) | POE_CODES | {code for values in MODEL_VALUES.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version=SOURCE_VERSION,
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "RUCKUS ICX 8200 Enterprise-Class Stackable Access Switch Data Sheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        updated = not_applicable = reclassified = 0
        missing_models = []
        for model, model_values in MODEL_VALUES.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            type_code = "campus_poe" if model in POE_MODELS else "campus_non_poe"
            if product.product_type_id != product_types[type_code].id:
                product.product_type = product_types[type_code]
                product.save(update_fields=("product_type", "updated_at"))
                reclassified += 1

            values = {**COMMON, **model_values}
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
                    "source_url": SOURCE_URL[:200],
                    "source_note": "Manually verified from the July 2026 official RUCKUS data sheet; product rows were matched to its model comparison and ordering tables.",
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
                    source_location=f"Feature/model comparison, specifications, and ordering information - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

            if model not in POE_MODELS:
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
                            "source_url": SOURCE_URL[:200],
                            "source_note": "The official model comparison identifies this hardware model as non-PoE.",
                            "verified_date": accessed,
                        },
                    )
                    SpecEvidence.objects.update_or_create(
                        product_spec=spec,
                        source_document=source,
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
            f"{mode}: spec_values={updated} not_applicable={not_applicable} reclassified={reclassified} models={len(MODEL_VALUES) - len(missing_models)}"
        ))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
