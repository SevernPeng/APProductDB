from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


SOURCES = {
    "guide": {
        "url": "https://www.dlink.com/bg/bg/-/media/resource-centre/brochures-and-product-guides/nuclias-connect-solution-guide-eu.pdf",
        "version": "Nuclias Connect solution guide, current official copy; accessed 2026-10-14",
        "title": "D-Link Nuclias Connect Solution Guide",
        "type": SourceDocument.DocumentType.SUPPORT,
    },
    "x3060": {
        "url": "https://www.dlink.com/es/es/press-centre/press-releases/2024/november/21/puntos-acceso-wifi-6-exterior-interior",
        "version": "Official D-Link Spain product release dated 2024-11-07; accessed 2026-10-14",
        "title": "D-Link DAP-X3060 / DAP-X3060OU Product Release",
        "type": SourceDocument.DocumentType.SUPPORT,
    },
    "guide2025": {
        "url": "https://www.dlink.com/fr/fr/-/media/resource-centre/brochures-and-product-guides/nuclias-connect-solution-guide-fr-2025.pdf",
        "version": "Nuclias Connect solution guide 2025; accessed 2026-10-23",
        "title": "D-Link Nuclias Connect Solution Guide 2025",
        "type": SourceDocument.DocumentType.SUPPORT,
    },
}


PRODUCTS = {
    "DAP-X2810": {
        "max_clients": (n(150, "150 recommended maximum clients"), "guide", "p. 11, Wi-Fi AP comparison"),
    },
    "DAP-X2850": {
        "max_clients": (n(250, "250 recommended maximum clients"), "guide", "p. 11, Wi-Fi AP comparison"),
    },
    "DAP-X3060": {
        "max_clients": (n(250, "250 recommended maximum clients"), "guide", "p. 11, Wi-Fi AP comparison"),
        "fast_roaming": (t("802.11k/r"), "x3060", "Product highlights, Fast Roaming"),
    },
    "DAP-X3060OU": {
        "max_clients": (n(250, "250 recommended maximum clients"), "guide", "p. 11, Wi-Fi AP comparison"),
        "fast_roaming": (t("802.11k/r"), "x3060", "Product highlights, Fast Roaming"),
    },
    "DAP-E9560": {
        "max_clients": (n(500, "500 recommended maximum clients"), "guide2025", "p. 11, Wi-Fi 7 AP comparison"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link wireless AP specifications (round 12)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, data in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=data["url"], document_version=data["version"],
                defaults={
                    "brand": brand, "product": None, "document_type": data["type"],
                    "title": data["title"], "region": "Worldwide", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )

        written = new = corrected = unchanged = 0
        details = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            model_new = model_corrected = 0
            for code, ((kind, value, raw), source_key, location) in values.items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
                ))
                if not had:
                    old_value = None
                elif old.value_text:
                    old_value = old.value_text
                elif old.value_number is not None:
                    old_value = old.value_number
                else:
                    old_value = old.value_boolean
                source = SOURCES[source_key]
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": source["url"][:200],
                    "source_note": "Manually verified from the cited official D-Link source.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=documents[source_key],
                    source_location=f"{location} - {model}",
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
