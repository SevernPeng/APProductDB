from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.ruckusnetworks.com/globalassets/digizuite/61729-ds-icx-7150.pdf"
SOURCE_VERSION = "PA-114000.6 (01/26)"


def n(value):
    return "number", value


def t(value):
    return "text", value


def b(value=True):
    return "boolean", value


COMMON = {
    "mac_address_table": t("16,384 entries"),
    "jumbo_frame_bytes": n(9216),
    "management_methods": t("Web (HTTP/HTTPS); CLI; SSH; Telnet; SNMPv1/v2c/v3; sFlow; SmartZone; RUCKUS Cloud; RUCKUS Unleashed"),
    "vlan_count": n(4095),
    "l2_features": t("802.1s MSTP; PVST/PVST+/RPVST; IGMP/MLD snooping; LACP; Q-in-Q; private VLAN; port/VLAN/ACL mirroring"),
    "stp_features": t("STP; RSTP; MSTP; PVST/PVST+/RPVST; BPDU Guard; Root Guard"),
    "acl_security": t("Port and Layer 3/4 ACLs; 802.1X; MAC/Web authentication; DHCP snooping; Dynamic ARP Inspection; IP Source Guard"),
    "l3_features": t("IPv4/IPv6 static routing, RIP/RIPng and ECMP; OSPFv2/v3, PIM, PBR and VRRP available with premium L3 license"),
    "ip_interface_capacity": t("382 virtual Ethernet interfaces"),
    "routing_entry_capacity": t("1,000 IPv4 routes and 1,000 IPv6 routes in hardware; 4,094 next hops"),
    "ospf_support": b(),
    "rip_support": b(),
    "pbr_support": b(),
    "vrrp_support": b(),
    "multicast_routing": b(),
    "stacking": t("Up to 12 mixed ICX 7150 switches; long-distance stacking up to 10 km"),
    "stacking_bandwidth_gbps": n(480),
    "stacking_units": n(12),
    "operating_temperature_c": t("0 to 45 °C"),
}


HARDWARE = {
    "24": {
        "switching_capacity_gbps": n(132),
        "packet_forwarding_rate_mpps": n(98),
        "packet_buffer_mb": n(2),
        "power_supply": t("Integrated 36 W AC power supply"),
        "fan_design": t("Fanless"),
        "max_power_consumption_w": n(24),
        "dimensions_mm": t("440 x 280 x 43.65 mm"),
    },
    "48": {
        "switching_capacity_gbps": n(180),
        "packet_forwarding_rate_mpps": n(134),
        "packet_buffer_mb": n(4),
        "power_supply": t("Integrated 65 W AC power supply"),
        "fan_design": t("Fanless"),
        "max_power_consumption_w": n(39),
        "dimensions_mm": t("440 x 370 x 43.65 mm"),
    },
    "24P": {
        "switching_capacity_gbps": n(132),
        "packet_forwarding_rate_mpps": n(98),
        "packet_buffer_mb": n(2),
        "power_supply": t("Integrated 525 W AC power supply"),
        "fan_design": t("Side-to-back airflow; configurable silent mode"),
        "max_power_consumption_w": n(472),
        "dimensions_mm": t("440 x 280 x 43.65 mm"),
        "poe_configuration": t("24 x 10/100/1000 Mbps PoE+ ports; 370 W PoE budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(24),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
    },
    "48P": {
        "switching_capacity_gbps": n(180),
        "packet_forwarding_rate_mpps": n(134),
        "packet_buffer_mb": n(4),
        "power_supply": t("Integrated 525 W AC power supply"),
        "fan_design": t("Side-to-back airflow; configurable silent mode"),
        "max_power_consumption_w": n(491),
        "dimensions_mm": t("440 x 370 x 43.65 mm"),
        "poe_configuration": t("48 x 10/100/1000 Mbps PoE+ ports; 370 W PoE budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
    },
    "48PF": {
        "switching_capacity_gbps": n(180),
        "packet_forwarding_rate_mpps": n(134),
        "packet_buffer_mb": n(4),
        "power_supply": t("Integrated 880 W AC power supply"),
        "fan_design": t("Side-to-back airflow"),
        "max_power_consumption_w": n(893),
        "dimensions_mm": t("440 x 370 x 43.65 mm"),
        "poe_configuration": t("48 x 10/100/1000 Mbps PoE+ ports; 740 W PoE budget"),
        "poe_standard": t("IEEE 802.3af/at"),
        "poe_ports": n(48),
        "poe_budget_w": n(740),
        "max_poe_per_port_w": n(30),
    },
    "48ZP": {
        "switching_capacity_gbps": n(304),
        "packet_forwarding_rate_mpps": n(226),
        "packet_buffer_mb": n(4),
        "power_supply": t("Up to 2 x 920 W hot-swappable, load-sharing AC power supplies"),
        "fan_design": t("Up to 2 hot-swappable fans; front-to-back airflow"),
        "max_power_consumption_w": n(932),
        "dimensions_mm": t("440 x 332 x 44 mm"),
        "poe_configuration": t("32 x GbE PoE+ and 16 x multigigabit PoH/802.3bt-ready ports; 740 W with one PSU, 1,480 W with two"),
        "poe_standard": t("IEEE 802.3af/at; PoH; 802.3bt-ready"),
        "poe_ports": n(48),
        "poe_budget_w": n(1480),
        "max_poe_per_port_w": n(90),
    },
}


MODEL_HARDWARE = {
    "ICX 7150-24": "24",
    "ICX 7150-24P": "24P",
    "ICX 7150-48": "48",
    "ICX 7150-48ZP": "48ZP",
    "ICX7150-24P-2X10G": "24P",
    "ICX7150-24P-4X10GR": "24P",
    "ICX7150-48P": "48P",
    "ICX7150-48PF-4X10R": "48PF",
    "ICX7150-48PF-4X1G": "48PF",
    "ICX7150-48ZP-E": "48ZP",
    "ICX7150-48ZP-ER": "48ZP",
}


INTERFACES = {
    "ICX 7150-24": "24 x GbE RJ45; 2 x GbE RJ45 uplinks; 4 x 1/10GbE SFP/SFP+ uplink/stacking ports",
    "ICX 7150-24P": "24 x GbE PoE+ RJ45; 2 x GbE RJ45 uplinks; 4 x 1/10GbE SFP/SFP+ uplink/stacking ports",
    "ICX 7150-48": "48 x GbE RJ45; 2 x GbE RJ45 uplinks; 4 x 1/10GbE SFP/SFP+ uplink/stacking ports",
    "ICX 7150-48ZP": "32 x GbE PoE+ RJ45; 16 x 100M/1G/2.5G PoH RJ45; 8 x 1/10GbE SFP/SFP+ uplink/stacking ports",
    "ICX7150-24P-2X10G": "24 x GbE PoE+ RJ45; 2 x GbE RJ45 uplinks; 2 x 1GbE SFP and 2 x 10GbE SFP+ uplink/stacking ports",
    "ICX7150-24P-4X10GR": "24 x GbE PoE+ RJ45; 2 x GbE RJ45 uplinks; 4 x 10GbE SFP+ uplink/stacking ports",
    "ICX7150-48P": "48 x GbE PoE+ RJ45; 2 x GbE RJ45 uplinks; 4 x 1/10GbE SFP/SFP+ uplink/stacking ports",
    "ICX7150-48PF-4X10R": "48 x GbE PoE+ RJ45; 2 x GbE RJ45 uplinks; 4 x 10GbE SFP+ uplink/stacking ports",
    "ICX7150-48PF-4X1G": "48 x GbE PoE+ RJ45; 2 x GbE RJ45 uplinks; 4 x 1GbE SFP uplink ports",
    "ICX7150-48ZP-E": "32 x GbE PoE+ RJ45; 16 x 100M/1G/2.5G PoH RJ45; up to 8 x 10GbE SFP+ uplink/stacking ports",
    "ICX7150-48ZP-ER": "32 x GbE PoE+ RJ45; 16 x 100M/1G/2.5G PoH RJ45; up to 8 x 10GbE SFP+ uplink/stacking ports",
}


POE_CODES = {"poe_configuration", "poe_standard", "poe_ports", "poe_budget_w", "max_poe_per_port_w"}


class Command(BaseCommand):
    help = "Import manually verified RUCKUS ICX 7150 specifications from the January 2026 official datasheet."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="RUCKUS").first()
        if not brand:
            raise CommandError("Brand 'RUCKUS' was not found.")
        all_values = {**COMMON}
        for values in HARDWARE.values():
            all_values.update(values)
        codes = set(all_values) | {"ethernet_interfaces"} | POE_CODES
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
                "title": "RUCKUS ICX 7150 Enterprise-Class Stackable Access Switch Data Sheet",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        updated = not_applicable = 0
        missing_models = []
        for model, hardware_key in MODEL_HARDWARE.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            values = {**COMMON, **HARDWARE[hardware_key], "ethernet_interfaces": t(INTERFACES[model])}
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
                    "source_note": "Manually verified from the January 2026 official RUCKUS datasheet; SKU suffixes were matched through its ordering table.",
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

            if hardware_key in {"24", "48"}:
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
            f"{mode}: spec_values={updated} not_applicable={not_applicable} models={len(MODEL_HARDWARE) - len(missing_models)}"
        ))
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
