from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


PRODUCTS = {
    "RG-NBS3200-24SFP": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/l2-managed-switch/rg-nbs3200-24sfp-8gt4xs/",
        "title": "RG-NBS3200-24SFP/8GT4XS Official Product Page and Datasheet",
        "version": "Official product page current 2026-10-21; paired with V1.5 installation guide",
        "location": "Key Specifications and software specification tables",
        "values": {
            "packet_forwarding_rate_mpps": n(95.23, "Forwarding rate: 95.23 Mpps"),
            "jumbo_frame_bytes": n(9216, "Jumbo frame length (MTU): 9216 bytes"),
            "vlan_count": n(4094, "Maximum VLAN support: 4094"),
            "stp_features": t(
                "STP, RSTP, MSTP",
                "Current RG-NBS/NIS configuration guide: supports STP, RSTP, and MSTP; MSTP requires ReyeeOS 2.320 or later",
            ),
            "link_aggregation": t("Supported"),
            "igmp_snooping": t("Supported"),
            "vlan_support": t("Supported; VLAN configuration through Ruijie Cloud App"),
            "l2_features": t("Link aggregation; IGMP snooping; VLAN; port isolation; broadcast storm control"),
            "acl_security": t("Port isolation; broadcast storm control; multiple security policies"),
            "management_methods": t("Ruijie Cloud web portal and mobile app; local web management"),
        },
    },
    "RGNBS5200-24SFP/8GT4XS": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/l3-managed-switch/rg-nbs5200-24sfp-8gt4xs/",
        "title": "RG-NBS5200-24SFP/8GT4XS Official Product Page and Datasheet",
        "version": "Exact-model official datasheet 2025-10-28 and current product page",
        "location": "Hardware, system, interface, and Layer 3 specification tables",
        "values": {
            "flash_memory": t("256 MB"),
            "dimensions_mm": t("440 x 267.5 x 43.6 mm (W x D x H)"),
            "fan_design": t("2 x fixed fans; left-to-right airflow"),
            "max_power_consumption_w": n(41.8, "Maximum power consumption: 41.8 W"),
            "power_supply": t(
                "Fixed AC power supply, 100-240 V, 50/60 Hz, maximum input current 2 A"
            ),
            "packet_buffer_mb": n(1.5, "Packet buffer: 12 Mbit (1.5 MB)"),
            "mac_address_table": t("16K", "MAC address table: 16,000 entries"),
            "vlan_count": n(4094, "Maximum VLAN support: 4094"),
            "stacking": t("Virtual Cluster Switching (VCS) hot standby"),
            "stacking_units": n(2, "Only two switches can form a VCS hot-standby group"),
            "routing_entry_capacity": t(
                "IPv4 routing table: 6000 entries; IPv4 static routes: 500"
            ),
        },
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_number is not None:
        return spec.value_number
    if spec.value_boolean is not None:
        return spec.value_boolean
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import manually verified Reyee NBS fiber-switch specs (round 31)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        if not brand:
            raise CommandError("Missing brand: Reyee")
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version=row["version"],
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": row["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                new_value = Decimal(str(value)) if kind == "number" else str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "" if kind == "number" else str(value),
                        "value_number": new_value if kind == "number" else None,
                        "value_boolean": None,
                        "normalized_value": str(value),
                        "unit": definition.unit,
                        "raw_value": raw,
                        "source_url": row["url"][:200],
                        "source_note": "Manually verified from the official exact-model product page, datasheet, and current configuration guide.",
                        "verified_date": accessed,
                    },
                )
                if old_value is None:
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=row["location"],
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            details.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
                f"unchanged={unchanged} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(details))
