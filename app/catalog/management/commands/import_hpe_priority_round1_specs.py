from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


VALUES = {
    "ethernet_interfaces": t("4 x 10/100/1000 PoE+ RJ45 + 4 x 10/100/1000 RJ45", "4 PoE+ Gigabit RJ45 ports and 4 non-PoE Gigabit RJ45 ports"),
    "dimensions_mm": t("254 x 159.5 x 43.9 mm", "25.4 x 15.95 x 4.39 cm (W x D x H)"),
    "fan_design": t("Fanless, 0 dB", "Acoustic power: 0 dB, no fan"),
    "fanless": b(True, "Acoustic power: 0 dB, no fan"),
    "jumbo_frame_bytes": n(9216, "Supports up to 9,216-byte frames"),
    "max_power_consumption_w": n(72.9, "Maximum power rating: 72.9 W"),
    "operating_temperature_c": t("0°C to 40°C", "32°F to 104°F (0°C to 40°C)"),
    "packet_forwarding_rate_mpps": n(11.9, "Throughput: up to 11.9 Mpps"),
    "switching_capacity_gbps": n(16, "Routing/switching capacity: 16 Gbps"),
    "cpu": t("ARM Cortex-A9, 400 MHz", "ARM Cortex-A9 @ 400 MHz"),
    "dram_memory": t("256 MB SDRAM"),
    "flash_memory": t("64 MB flash"),
    "routing_entry_capacity": t("32 entries", "Routing table size: 32 entries"),
    "acl_security": t("IPv4/MAC ACLs; 802.1X; RADIUS; port isolation; DoS protection; SSL", "Up to 50 inbound ACL entries plus RADIUS, 802.1X, port isolation, DoS protection, and SSL"),
    "l2_features": t("802.1Q VLAN, STP/RSTP/MSTP, BPDU filtering, LACP, IGMP snooping, LLDP-MED, voice VLAN", "Layer 2 feature set from QuickSpecs"),
    "l3_features": t("Static IPv4 routing (32 routes), ARP/proxy ARP, DHCP relay", "Layer 3 services and routing from QuickSpecs"),
    "management_methods": t("Web GUI (HTTP/HTTPS), SNMP v1/v2c/v3", "Simple Web management with HTTP/HTTPS and SNMP v1/v2c/v3"),
    "max_poe_per_port_w": n(30, "Up to 30 W per PoE+ port"),
    "poe_budget_w": n(65, "PoE power: 65 W PoE+"),
    "poe_ports": n(4, "Ports 1-4 are PoE/PoE+ capable"),
    "poe_standard": t("IEEE 802.3af/802.3at PoE+", "PoE/PoE+; up to 30 W per port"),
    "power_supply": t("External 90 W adapter; 100-240 VAC, 50/60 Hz", "90 W adapter; AC voltage 100-240 VAC, 50/60 Hz"),
    "vlan_count": n(256, "256 VLANs; VLAN ID range 2-4093"),
    "stp_features": t("STP, RSTP, MSTP, BPDU filtering", "IEEE 802.1D STP, 802.1w RSTP, 802.1s MSTP, BPDU filtering"),
}


class Command(BaseCommand):
    help = "Import manually verified HPE OfficeConnect 1920S JL383A specifications (round 1)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="HPE").first()
        model = "1920S 8G PPoE+ 65W Switch"
        product = Product.objects.filter(brand=brand, model=model, is_published=True).first() if brand else None
        if not brand or not product:
            raise CommandError(f"Missing HPE product: {model}")
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if missing := VALUES.keys() - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        url = "https://www.hpe.com/psnow/downloadDoc/HPE%20OfficeConnect%201920S%20Switch%20Series-a00001630enw.pdf?deepLink=&form=false&hf=regular&id=a00001630enw.pdf&isFutureVersion=true&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=4"
        version = "HPE OfficeConnect 1920S Switch Series QuickSpecs v4; current official copy accessed 2026-10-15"
        document, _ = SourceDocument.objects.update_or_create(
            url=url, document_version=version,
            defaults={
                "brand": brand, "product": product,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "HPE OfficeConnect 1920S Switch Series QuickSpecs",
                "region": "Worldwide", "published_date": None,
                "accessed_date": accessed, "active": True,
            },
        )

        new = corrected = unchanged = 0
        for code, (kind, value, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
            ))
            if not had:
                old_value = None
            elif old.value_text:
                old_value = old.value_text
            elif old.value_number is not None:
                old_value = old.value_number
            else:
                old_value = old.value_boolean
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "", "value_number": None, "value_boolean": None,
                "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                "source_url": url[:200],
                "source_note": "Manually verified from the official HPE QuickSpecs; model-specific values use the JL383A technical-specification table.",
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
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                new += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            location = "pp. 14-15, JL383A technical specifications"
            if code in {"acl_security", "l2_features", "l3_features", "management_methods", "max_poe_per_port_w", "poe_ports", "poe_standard", "vlan_count", "stp_features", "jumbo_frame_bytes"}:
                location = "pp. 2-5, series features and benefits"
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=document,
                source_location=f"{location} - {code}",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(VALUES)} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models=1"
        ))
