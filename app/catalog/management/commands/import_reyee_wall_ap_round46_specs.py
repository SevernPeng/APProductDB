from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP62-Wall": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/3/11/RG-RAP62-Wall_Datasheet_Official_2026-03-11.pdf",
        "values": {
            "max_ssids": ("number", 8, "Maximum number of SSIDs: 8"),
        },
    },
    "RG-RAP72-Wall": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2026/3/11/RG-RAP72-Wall_Datasheet_Official_2026-03-11.pdf",
        "values": {
            "max_ssids": ("number", 8, "Maximum number of SSIDs: 8"),
            "fast_roaming": (
                "text",
                "802.11k/v, 802.11r, Layer 2/Layer 3 roaming, and AI roaming",
                "802.11k/v roaming: Yes; Fast transition (802.11r): Yes; Layer 2 roaming: Yes; Layer 3 roaming: Yes; AI roaming: Yes",
            ),
            "wireless_security": (
                "text",
                "WPA-PSK, WPA2-PSK, WPA/WPA2-PSK, OWE, WPA3-SAE, WPA2-PSK/WPA3-SAE",
                "Encryption modes: WPA-PSK, WPA2-PSK, WPA/WPA2-PSK, OWE (Enhanced Open), WPA3-SAE, WPA2-PSK/WPA3-SAE",
            ),
        },
    },
}


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_number is not None:
        return spec.value_number
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import RG-RAP62-Wall/RG-RAP72-Wall SSID, roaming, and security gaps (round 46)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        codes = {code for row in PRODUCTS.values() for code in row["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if not brand or len(definitions) != len(codes):
            raise CommandError("Missing Reyee brand or wall-AP definitions")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for model, row in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Official datasheet dated 2026-03-11",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"{model} Official Datasheet",
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
                new_value = Decimal(str(value)) if kind == "number" else value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "" if kind == "number" else value,
                        "value_number": new_value if kind == "number" else None,
                        "value_boolean": None,
                        "normalized_value": str(value),
                        "unit": definition.unit,
                        "raw_value": raw,
                        "source_url": row["url"][:200],
                        "source_note": "Manually verified from the latest official March 2026 exact-model datasheet.",
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
                    source_location="Software Specifications table",
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
