from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP2260(G)": {
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_ruijie-reyee-rg-rap2260-g-access-point-hardware-installation-and-reference-guide-en/",
        "version": "Installation Guide V1.7",
        "values": {
            "antenna_gain_dbi": (
                "2.4 GHz: 3.00 dBi; 5 GHz: 3.00 dBi",
                "Antenna gain (2.4 GHz): 3.00 dBi; Antenna gain (5 GHz): 3.00 dBi",
            ),
        },
    },
    "RG-RAP6260(G)": {
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_ruijie-reyee-rg-rap6260-g-access-point-hardware-installation-and-reference-guide-en/",
        "version": "Installation Guide V1.5",
        "values": {
            "antenna_gain_dbi": (
                "2.4 GHz: 4.00 dBi; 5 GHz: 6.00 dBi",
                "Antenna gain (2.4 GHz): 4.00 dBi; Antenna gain (5 GHz): 6.00 dBi",
            ),
            "lightning_protection_kv": (
                "±4 kV common mode (Ethernet port)",
                "Surge protection, Ethernet port: ±4 kV for common mode",
            ),
        },
    },
    "RG-RAP72Pro-OD": {
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_rg-rap72pro-od-access-point-installation-guide/",
        "version": "Installation Guide V1.1",
        "values": {
            "antenna_gain_dbi": (
                "2.4 GHz: 3.62 dBi; 5 GHz: 6.28 dBi",
                "Antenna gain (2.4 GHz): 3.62 dBi; Antenna gain (5 GHz): 6.28 dBi",
            ),
            "lightning_protection_kv": (
                "±4 kV common mode (Ethernet port)",
                "Surge protection, Ethernet port: ±4 kV for common mode",
            ),
        },
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import exact antenna gain and surge-protection gaps from official AP installation guides (round 47)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if not brand or len(definitions) != len(codes):
            raise CommandError("Missing Reyee brand or AP RF definitions")

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
                    "document_type": SourceDocument.DocumentType.SUPPORT,
                    "title": f"Ruijie Reyee {model} Access Point Installation Guide",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (value, raw) in row["values"].items():
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
                        "source_url": row["url"][:200],
                        "source_note": f"Manually verified from the latest official {row['version']} exact-model guide.",
                        "verified_date": accessed,
                    },
                )
                if old_value is None:
                    new += 1
                    model_new += 1
                elif old_value != value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location="Technical Specifications table",
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
