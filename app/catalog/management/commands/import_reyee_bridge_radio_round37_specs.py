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
    "RG-EST100-E": {
        "url": "https://eo-sgp-cos.ruijie.com/Document/pdf/2025/12/8/product-psti-251208.pdf",
        "version": "Exact-model official datasheet 2025-12-04",
        "values": {
            "antenna_gain_dbi": t("8 dBi", "2.4 GHz antenna gain: 8 dBi"),
            "rate_2g_mbps": n(300, "2.4 GHz wireless data rate: 300 Mbps"),
            "max_bridge_pairs": n(1, "Maximum PTMP connections: 1"),
        },
    },
    "RG-EST310": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est310v2/",
        "version": "RG-EST310 V2 exact-model official datasheet 2025-12-04",
        "values": {
            "antenna_gain_dbi": t("10 dBi", "5 GHz antenna gain: 10 dBi"),
            "max_bridge_pairs": n(5, "Maximum PTMP connections: 5"),
        },
    },
    "RG-EST350": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est350v2/",
        "version": "RG-EST350 V2 exact-model official datasheet 2025-12-04",
        "values": {
            "antenna_gain_dbi": t("15 dBi", "5 GHz antenna gain: 15 dBi"),
            "max_bridge_pairs": n(3, "Maximum PTMP connections: 3"),
        },
    },
    "RG-EST350G": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est350g/",
        "version": "Exact-model official datasheet 2026-01-27",
        "values": {"max_bridge_pairs": n(16, "Maximum PTMP connections: 16")},
    },
    "RG-EST450G": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est450g/",
        "version": "Exact-model official datasheet 2026-01-27",
        "values": {"max_bridge_pairs": n(32, "Maximum PTMP connections: 32")},
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
    help = "Import manually verified Reyee wireless-bridge antenna and PTMP specs (round 37)."

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
                url=row["url"], document_version=row["version"],
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
                        "value_boolean": None,
                        "normalized_value": str(value), "unit": definition.unit,
                        "raw_value": raw, "source_url": row["url"][:200],
                        "source_note": "Manually verified from the newest available official exact-model product page and datasheet.",
                        "verified_date": accessed,
                    },
                )
                if old_value is None:
                    new += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location="Hardware antenna table and software WLAN/PTMP table",
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
