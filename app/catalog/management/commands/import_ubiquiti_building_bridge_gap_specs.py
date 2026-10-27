from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


MODELS = {
    "Building Bridge": {
        "url": "https://dl.ui.com/ds/ubb_ds",
        "values": {
            "antenna_type": t("Highly directional integrated 5 GHz and 60 GHz antennas"),
            "beamwidth": t("60 GHz elevation: 30°; azimuthal coverage: ±60°"),
            "lightning_protection_kv": t("±24 kV contact/air", "ESD/EMP protection: ±24 kV contact/air"),
            "max_bridge_pairs": n(1, "Two pre-paired endpoint devices form one point-to-point link"),
        },
    },
    "Building Bridge XG": {
        "url": "https://dl.ui.com/ds/ubb-xg_ds.pdf",
        "values": {
            "max_bridge_pairs": n(1, "Operating mode: PtP; supplied as a pre-paired bridge kit"),
        },
    },
    "UBB-XG": {
        "url": "https://dl.ui.com/ds/ubb-xg_ds.pdf",
        "values": {
            "max_bridge_pairs": n(1, "Operating mode: PtP; supplied as a pre-paired bridge kit"),
        },
    },
    "Wave MLO6": {
        "url": "https://techspecs.ui.com/uisp/wireless/wave-mlo6",
        "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "values": {
            "max_bridge_pairs": n(1, "Operating mode: PtP"),
        },
    },
}


class Command(BaseCommand):
    help = "Import official Ubiquiti Building Bridge antenna and PtP gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Missing brand: Ubiquiti")
        codes = {code for item in MODELS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Ubiquiti product: {model}")
            document, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Official exact-model Ubiquiti source, verified 2026-10-22",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": item.get(
                        "document_type", SourceDocument.DocumentType.DATASHEET
                    ),
                    "title": f"Ubiquiti {model} official specifications",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            documents[model] = document
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (bool((existing.value_text or "").strip()) or existing.value_number is not None)
                )
                old_value = existing.value_text or existing.value_number if had else None
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from Ubiquiti's official exact-model source.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=document,
                    source_location=f"Official datasheet RF/specifications table - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={newly_filled} "
                f"corrected={corrected} unchanged={unchanged} models={len(MODELS)}"
            )
        )
        self.stdout.write("; ".join(per_model))
