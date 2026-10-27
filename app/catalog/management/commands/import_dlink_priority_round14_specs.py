from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


SOURCES = {
    "nuclias_2025": {
        "url": "https://www.dlink.com/mx/es/-/media/files/es/catalogos/dlink-catalogo-nuclias-connect-gestion-de-red-gratuita.pdf",
        "version": "Current official Nuclias Connect catalog; crawled 2026-10-15",
        "title": "D-Link Nuclias Connect Unified Network Management Catalog",
        "type": SourceDocument.DocumentType.SUPPORT,
    },
    "business_wifi": {
        "url": "https://www.dlink.com/pt/pt/-/media/files/es/catalogos/dlink-catalogo-pt.pdf",
        "version": "Official Business Wi-Fi catalog; accessed 2026-10-15",
        "title": "D-Link Business Wi-Fi Catalog",
        "type": SourceDocument.DocumentType.SUPPORT,
    },
}


PRODUCTS = {
    "DAP-2622": {
        "fast_roaming": (t("802.11k/r", "802.11k/r fast roaming"), "business_wifi", "AP comparison table"),
        "max_ssids": (n(16, "16 SSIDs (8 per radio)"), "nuclias_2025", "p. 10, Wi-Fi 5 AP comparison"),
        "mimo_2g": (t("2x2 MIMO", "2.4G/5G 2x2"), "nuclias_2025", "p. 10, antenna configuration"),
        "poe_output": (t("PoE output passthrough", "3x Gigabit: PoE in + PoE Out + LAN"), "nuclias_2025", "p. 10, Ethernet interface"),
        "total_spatial_streams": (n(4, "2x2 on 2.4 GHz + 2x2 on 5 GHz = 4 total spatial streams"), "nuclias_2025", "p. 10, antenna configuration"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link wireless AP specifications (round 14)."

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
                    "title": data["title"], "region": "Europe/Latin America",
                    "published_date": None, "accessed_date": accessed, "active": True,
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
                    "source_note": "Manually verified from the cited official D-Link catalog; total streams is the sum of the stated per-band 2x2 configuration.",
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
                        "evidence_level": SpecEvidence.EvidenceLevel.C,
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
