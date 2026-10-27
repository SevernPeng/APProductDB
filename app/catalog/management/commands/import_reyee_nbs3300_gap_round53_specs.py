from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


MODEL = "RG-NBS3300-8MG2XS-P"
URL = "https://eo-sgp-cos.ruijie.com/Document/pdf/2025/12/9/RG-NBS3300-8MG2XS-P_Datasheet_Official_2025-12-09.pdf"
VALUES = {
    "vlan_count": ("number", 4094, "Maximum number of VLANs: 4094"),
    "stp_features": (
        "text",
        "STP, RSTP, MSTP",
        "STP (IEEE 802.1d): Yes; RSTP (IEEE 802.1w): Yes; MSTP (IEEE 802.1s): Yes",
    ),
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
    help = "Import exact official RG-NBS3300-8MG2XS-P VLAN and STP gaps (round 53)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if not brand or set(VALUES) - definitions.keys():
            raise CommandError("Missing Reyee brand or required switch definitions")
        product = Product.objects.filter(brand=brand, model=MODEL, is_published=True).first()
        if not product:
            raise CommandError(f"Missing published Reyee product: {MODEL}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Official exact-model datasheet dated 2025-12-09",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "RG-NBS3300-8MG2XS-P Datasheet Official",
                "region": "Global",
                "published_date": date(2025, 12, 9),
                "accessed_date": accessed,
                "active": True,
            },
        )

        written = new = corrected = unchanged = 0
        details = []
        for code, (kind, value, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            new_value = Decimal(str(value)) if kind == "number" else value
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": value if kind == "text" else "",
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": URL[:200],
                    "source_note": "Manually verified from the current official exact-model datasheet.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
                detail = "+1"
            elif old_value != new_value:
                corrected += 1
                detail = "corrected:1"
            else:
                unchanged += 1
                detail = "unchanged:1"
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location="Software Specifications, Ethernet Switching (pages 11-12)",
                defaults={
                    "source_excerpt": raw,
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
            details.append(f"{code}:{detail}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models=1"
        ))
        self.stdout.write("; ".join(details))
