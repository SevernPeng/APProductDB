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
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/est100/",
        "version": "Current RG-EST100-E official global product page, accessed 2026-10-21",
        "values": {
            "supported_bands": t("2.4 GHz", "Single-radio; Radio 1: 2.4 GHz, 2 spatial streams"),
            "max_channel_width_mhz": n(40, "2.4 GHz channel width: Auto/20/40 MHz"),
            "centralized_management": t(
                "Ruijie Cloud; Ruijie Reyee App",
                "Ruijie Cloud remote monitoring; restarting through Ruijie Reyee App: Yes",
            ),
        },
    },
    "RG-EST310": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est310v2/",
        "version": "Current RG-EST310 V2 official global product page, accessed 2026-10-21",
        "values": {
            "max_channel_width_mhz": n(80, "5 GHz channel width: Auto/20/40/80 MHz"),
            "centralized_management": t(
                "Ruijie Cloud; Ruijie Reyee App",
                "Cloud management; restarting through Ruijie Reyee App: Yes",
            ),
            "operating_temperature_c": t("-30 to 55 °C", "Operating temperature: -30°C to +55°C"),
        },
    },
    "RG-EST350G": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est350g/",
        "version": "Current RG-EST350G official global product page, accessed 2026-10-21",
        "values": {
            "max_channel_width_mhz": n(80, "2.4 GHz: Auto/20/40 MHz; 5 GHz: Auto/20/40/80 MHz"),
            "centralized_management": t(
                "Ruijie Cloud; Ruijie Reyee App",
                "Cloud monitoring and configuration; restarting through Ruijie Reyee App: Yes",
            ),
            "antenna_type": t("Integrated directional antenna", "16 dBi; H: 31°, V: 14°"),
            "poe_input": t(
                "Passive PoE or IEEE 802.3af/at PoE; 12 V DC also supported",
                "Support 3 Power Supply Options: 12 V DC, Passive PoE, 802.3af/at",
            ),
        },
    },
    "RG-EST450G": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless-bridge/est-series/rg-est450g/",
        "version": "Current RG-EST450G official global product page, accessed 2026-10-21",
        "values": {
            "max_channel_width_mhz": n(80, "2.4 GHz: Auto/20/40 MHz; 5 GHz: Auto/20/40/80 MHz"),
            "centralized_management": t(
                "Ruijie Cloud; Ruijie Reyee App",
                "Cloud monitoring and configuration; restarting through Ruijie Reyee App: Yes",
            ),
            "antenna_type": t("Built-in sector antenna", "15 dBi with 120° built-in antenna"),
            "poe_input": t(
                "Passive PoE or IEEE 802.3af/at PoE; 12 V DC also supported",
                "Support 3 Power Supply Options: 12 V DC, Passive PoE, 802.3af/at",
            ),
        },
    },
}


class Command(BaseCommand):
    help = "Import/correct manually verified Reyee EST-series product-page specifications (round 21)."

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
                old_value = None if not had else (old.value_number if kind == "number" else old.value_text)
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
                        "source_note": "Manually verified from the current official Reyee product page.",
                        "verified_date": accessed,
                    },
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
                    source_location=f"Features / Key Specifications - {model}",
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
