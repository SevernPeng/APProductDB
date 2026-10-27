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
    "RG-POE-AF15": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-accessories/rgpoeaf15/",
        "values": {
            "accessory_interface_type": t("1000BASE-T RJ45", "1-Port PoE Injector (1000Base-T)"),
            "accessory_data_rate_gbps": n(1, "1000Base-T"),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz; 0.5 A max"),
            "accessory_poe_standard": t(
                "Passive PoE; 2-pair powering on pins 4,5 (+) and 7,8 (-)"
            ),
            "accessory_power_w": n(15.6, "52 V DC @ 0.3 A; 15.6 W"),
            "accessory_compatibility": t(
                "RG-RAP1200(F), RG-RAP1201, RG-RAP1200(P), RG-RAP2200(F), "
                "RG-RAP2200(E), RG-RAP6202(G)"
            ),
            "accessory_mounting_type": t("Inline PoE injector", "1-Port PoE Injector"),
        },
    },
    "RG-POE-AT30": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-accessories/rgpoeat30/",
        "values": {
            "accessory_interface_type": t("1000BASE-T RJ45", "1-Port PoE Injector (1000Base-T)"),
            "accessory_data_rate_gbps": n(1, "1000Base-T"),
            "accessory_input_power": t("100-240 V AC, 50/60 Hz; 0.7 A max"),
            "accessory_poe_standard": t(
                "Passive PoE; 2-pair powering on pins 4,5 (+) and 7,8 (-)"
            ),
            "accessory_power_w": n(31.2, "52 V +5% DC @ 0.6 A; 31.2 W"),
            "accessory_compatibility": t(
                "RG-RAP1200(F), RG-RAP1201, RG-RAP1200(P), RG-RAP1261, RG-RAP1260, "
                "RG-RAP2200(F), RG-RAP2200(E), RG-RAP2260(G), RG-RAP2260, RG-RAP2266, "
                "RG-RAP2260(E), RG-RAP6202(G), RG-RAP6262(G), RG-RAP6262, RG-RAP6260(G)"
            ),
            "accessory_mounting_type": t("Inline PoE injector", "1-Port PoE Injector"),
        },
    },
    "RG-POE-50-60W-MG": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-accessories/poe5060wmg/",
        "values": {
            "accessory_interface_type": t("2500BASE-T RJ45", "1-Port PoE Injector (2500Base-T)"),
            "accessory_data_rate_gbps": n(2.5, "2500Base-T"),
            "accessory_input_power": t(
                "100-240 V AC, 50/60 Hz; 1.5 A @ 120 V AC, 1.2 A @ 240 V AC"
            ),
            "accessory_poe_standard": t(
                "Passive PoE; 4-pair powering on pins 1,2,4,5 (+) and 3,6,7,8 (-)"
            ),
            "accessory_power_w": n(60, "56 V, 60 W"),
            "accessory_compatibility": t(
                "RG-RAP2260(H), RG-RAP6260(H), RG-RAP6260(H)-D"
            ),
            "accessory_mounting_type": t("Inline PoE injector", "1-Port PoE Injector"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Reyee passive PoE-injector product-page specifications (round 19)."

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
                document_version="Current official global product page, accessed 2026-10-21",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"{model} official product page",
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
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None
                    or old.value_boolean is not None
                ))
                old_value = None
                if had:
                    old_value = old.value_number if kind == "number" else old.value_text
                new_value = Decimal(str(value)) if kind == "number" else str(value)
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "" if kind == "number" else str(value),
                    "value_number": new_value if kind == "number" else None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": "Manually verified from the current official Reyee product page.",
                    "verified_date": accessed,
                }
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
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
                    source_location=f"Model summary / Features / Products Compatible - {model}",
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
