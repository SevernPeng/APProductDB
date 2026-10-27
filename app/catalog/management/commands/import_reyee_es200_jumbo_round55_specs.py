from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SECURITY_VALUE = (
    "Port isolation; broadcast, multicast, and unknown-unicast storm control; "
    "DHCP snooping; CPU Protection Policy"
)
SECURITY_RAW = (
    "Security: Port isolation Yes; Broadcast storm control Yes; Multicast storm control Yes; "
    "Unknown unicast storm control Yes; DHCP snooping Yes; CPU Protection Policy Yes"
)

PRODUCTS = {
    "RG-ES205GC": 9216,
    "RG-ES205GC-P": 9216,
    "RG-ES208GC": 9216,
    "RG-ES216GC": 10000,
    "RG-ES218GC-P": 10000,
    "RG-ES224GC": 10000,
    "RG-ES226GC-P": 10000,
}


def source_url(model):
    release_date = "2026-05-15" if model == "RG-ES205GC-P" else "2026-05-13"
    path_date = "2026/5/15" if model == "RG-ES205GC-P" else "2026/5/13"
    return (
        f"https://eo-sgp-cos.ruijie.com/Document/pdf/{path_date}/"
        f"{model}_Datasheet_Official_{release_date}.pdf"
    )


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_number is not None:
        return spec.value_number
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import exact-model Reyee ES200 jumbo-frame and security gaps (round 55)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definitions = {
            definition.code: definition
            for definition in SpecDefinition.objects.filter(
                code__in={"jumbo_frame_bytes", "acl_security"}
            )
        }
        if not brand or set(definitions) != {"jumbo_frame_bytes", "acl_security"}:
            raise CommandError("Missing Reyee brand or required switch definitions")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, jumbo_bytes in PRODUCTS.items():
            product = Product.objects.filter(
                brand=brand, model=model, is_published=True
            ).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")

            url = source_url(model)
            source, _ = SourceDocument.objects.update_or_create(
                url=url,
                document_version=(
                    "Official 2026-05-15 release"
                    if model == "RG-ES205GC-P"
                    else "Official 2026-05-13 release (document date 2026.5.12)"
                ),
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"{model} Official Datasheet",
                    "region": "Global",
                    "published_date": date(
                        2026, 5, 15 if model == "RG-ES205GC-P" else 13
                    ),
                    "accessed_date": accessed,
                    "active": True,
                },
            )

            values = {
                "jumbo_frame_bytes": (
                    jumbo_bytes,
                    f"Jumbo frame length (MTU): {jumbo_bytes} bytes",
                    "Software Specifications - Interface",
                ),
                "acl_security": (
                    SECURITY_VALUE,
                    SECURITY_RAW,
                    "Software Specifications - Security",
                ),
            }
            model_new = model_corrected = 0
            for code, (value, raw, location) in values.items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(
                    product=product, definition=definition
                ).first()
                old_value = actual(old)
                is_number = definition.data_type in {"integer", "decimal"}
                new_value = Decimal(str(value)) if is_number else value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "" if is_number else value,
                        "value_number": new_value if is_number else None,
                        "value_boolean": None,
                        "normalized_value": str(value),
                        "unit": definition.unit,
                        "raw_value": raw,
                        "source_url": url[:200],
                        "source_note": (
                            "Manually verified from the current official exact-model Reyee datasheet."
                        ),
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
                    source_location=location,
                    defaults={
                        "source_excerpt": raw,
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
