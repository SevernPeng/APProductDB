from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://webresources.vistancenetworks.com/download/assets/RUCKUS%2BICX%2B7550%2BSwitch%2BData%2BSheet/3b33be4cd7a311f09702fa7a03f65a78"
SOURCE_VERSION = "PA-115092.7-EN (02/26)"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "mac_address_table": t("16,000 (profile 1); 114,000 (profile 2); 32,000 (profile 3)"),
    "packet_buffer_mb": n(8),
    "jumbo_frame_bytes": n(12288),
    "power_supply": t("Two hot-swappable, load-sharing AC or DC power supplies"),
    "fan_design": t("Three hot-swappable fans; reversible front-to-back or back-to-front airflow"),
    "management_methods": t("Web (HTTP/HTTPS); CLI; SSH; Telnet; SNMPv1/v2c/v3; sFlow; SmartZone; RUCKUS One; RUCKUS Unleashed"),
    "vlan_count": n(4095),
    "l2_features": t("MSTP; PVST/PVST+/PVRST; IGMP/MLD snooping; LACP; Q-in-Q; private VLAN; MRP; VSRP; VXLAN; port/ACL/MAC mirroring"),
    "stp_features": t("STP; RSTP; MSTP; PVST/PVST+/PVRST; BPDU Guard; Root Guard"),
    "acl_security": t("Port and Layer 3/4 ACLs; 802.1X; MAC/Web authentication; DHCP snooping; Dynamic ARP Inspection; MACsec with licensed module; TPM"),
    "l3_features": t("IPv4/IPv6 static routing, RIP/RIPng, ECMP and BGP EVPN VXLAN; OSPF, PIM, PBR, VRRP, BGP and VRF with premium license"),
    "ip_interface_capacity": t("512 virtual Ethernet interfaces"),
    "routing_entry_capacity": t("IPv4: up to 97,280; IPv6: up to 17,408, depending on hardware profile"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "multicast_routing": b(),
    "stacking": t("Up to 12 ICX 7550 switches; stacking distance up to 10 km"),
    "stacking_bandwidth_gbps": n(2400),
    "stacking_units": n(12),
    "dimensions_mm": t("440 x 406.4 x 44 mm"),
    "operating_temperature_c": t("0 to 45 °C"),
}


MODEL_VALUES = {
    "ICX7550-24F-E2": {
        "ethernet_interfaces": t("24 x 1/10GbE SFP+; 2 x 40/100GbE QSFP28 uplink/stacking ports; one expansion-module slot"),
        "switching_capacity_gbps": n(1080),
        "packet_forwarding_rate_mpps": n(803),
        "max_power_consumption_w": n(142.7),
    },
    "ICX7550-24XZP": {
        "ethernet_interfaces": t("24 x 100M/1G/2.5G/5G/10GbE PoE RJ45; 2 x 40/100GbE QSFP28 uplink/stacking ports; one expansion-module slot"),
        "switching_capacity_gbps": n(1080),
        "packet_forwarding_rate_mpps": n(803),
        "poe_configuration": t("24 x IEEE 802.3bt ports with perpetual and fast-boot PoE; up to 1,900 W budget"),
        "poe_standard": t("IEEE 802.3af/at/bt"),
        "poe_ports": n(24),
        "poe_budget_w": n(1900),
        "max_poe_per_port_w": n(90),
        "max_power_consumption_w": n(1152),
    },
}


POE_CODES = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


class Command(BaseCommand):
    help = "Import manually verified RUCKUS ICX 7550 specifications from the February 2026 data sheet."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Brand 'RUCKUS' was not found.")
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
                "title": "RUCKUS ICX 7550 Mid-Range Enterprise-Class Stackable Switch Data Sheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        updated = not_applicable = 0
        missing_models = []
        for model, model_values in MODEL_VALUES.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
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
                    "source_note": "Manually verified from the February 2026 official RUCKUS data sheet; the -E2 bundle suffix was matched through the ordering table.",
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
                    source_location=f"Model comparison, specifications, and ordering information - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {data}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

            if model == "ICX7550-24F-E2":
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
                            "source_note": "The official model comparison identifies the 24F fiber model as non-PoE.",
                            "verified_date": accessed,
                        },
                    )
                    SpecEvidence.objects.update_or_create(
                        product_spec=spec,
                        source_document=source,
                        source_location=f"Model comparison - {model}",
                        defaults={
                            "source_excerpt": "Fiber model without PoE interfaces",
                            "evidence_level": SpecEvidence.EvidenceLevel.A,
                            "verified_at": timezone.now(),
                        },
                    )
                    not_applicable += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={updated} not_applicable={not_applicable} models={len(MODEL_VALUES) - len(missing_models)}"
        ))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
