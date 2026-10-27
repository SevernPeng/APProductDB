from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


MODEL = "RG-AirMetro550G-B"
URL = "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/airmetro-series/airmetro550g-b/"
VALUES = {
    "antenna_gain_dbi": (
        "Depends on attached antenna: 13 dBi (RG-ANT13-360), 16 dBi (RG-ANT16S-120), or 20 dBi (RG-ANT20S-90)",
        "Compatible antenna choices: RG-ANT13-360: 5 GHz, 13 dBi; RG-ANT16S-120: 5 GHz, 16 dBi; RG-ANT20S-90: 5 GHz, 20 dBi",
    ),
    "beamwidth": (
        "RG-ANT13-360: H 360°, V 7°; RG-ANT16S-120: H 120°, V 10°; RG-ANT20S-90: H 90°, V 7°",
        "Compatible antenna choices: RG-ANT13-360 H:360° V:7°; RG-ANT16S-120 H:120° V:10°; RG-ANT20S-90 H:90° V:7°",
    ),
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import official external-antenna gain and beamwidth choices for RG-AirMetro550G-B (round 54)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if not brand or set(VALUES) - definitions.keys():
            raise CommandError("Missing Reyee brand or required wireless-bridge definitions")
        product = Product.objects.filter(brand=brand, model=MODEL, is_published=True).first()
        if not product:
            raise CommandError(f"Missing published Reyee product: {MODEL}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Current official product page and antenna compatibility table accessed 2026-10-21",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "RG-AirMetro550G-B Official Product Page",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        written = new = corrected = unchanged = 0
        details = []
        for code, (value, raw) in VALUES.items():
            definition = definitions[code]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": value,
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": value,
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": URL[:200],
                    "source_note": "Manually verified from the current official base-station page and its three exact compatible antenna pages.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
                detail = "+1"
            elif old_value != value:
                corrected += 1
                detail = "corrected:1"
            else:
                unchanged += 1
                detail = "unchanged:1"
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location="Features - Antennas - Triple Devices, Beyond Triple Choices",
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
