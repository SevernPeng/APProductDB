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
    "RG-NIS2100-4GT2SFP-HP": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/industrial-switch/rg-nis2100-4gt2sfp-hp/",
        "values": {
            "mac_address_table": t("8K", "MAC address table: 8K (8,000 entries)"),
            "packet_buffer_mb": n(0.513, "Packet buffer: 4.1 Mbit (0.5125 MB; stored as 0.513 MB)"),
            "jumbo_frame_bytes": n(10000, "Jumbo frame: 10,000 bytes"),
            "vlan_count": n(16, "Maximum VLANs: 16"),
        },
    },
    "RG-NIS2100-8GT2SFP-HP": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-switch/industrial-switch/rg-nis2100-8gt2sfp-hp/",
        "values": {
            "mac_address_table": t("8K", "MAC address table: 8K (8,000 entries)"),
            "packet_buffer_mb": n(0.513, "Packet buffer: 4.1 Mbit (0.5125 MB; stored as 0.513 MB)"),
            "jumbo_frame_bytes": n(10000, "Jumbo frame: 10,000 bytes"),
            "vlan_count": n(16, "Maximum VLANs: 16"),
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
    help = "Import manually verified Reyee NIS2100 switching-table specs (round 38)."

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
                url=row["url"], document_version="Exact-model official datasheet 2025-10-24",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"{model} Official Product Page and Datasheet",
                    "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = actual(old)
                new_value = Decimal(str(value)) if kind == "number" else str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "" if kind == "number" else str(value),
                        "value_number": new_value if kind == "number" else None,
                        "value_boolean": None, "normalized_value": str(value),
                        "unit": definition.unit, "raw_value": raw,
                        "source_url": row["url"][:200],
                        "source_note": "Manually verified from the newest available official exact-model datasheet.",
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
                    product_spec=spec, source_document=source,
                    source_location="Hardware specifications and software specifications tables",
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
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
