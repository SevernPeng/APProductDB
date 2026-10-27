from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


PRODUCTS = {
    "RG-RAP62-Wall": {
        "url": "https://reyee.ruijie.com/en-global/products/sme/wireless/rg-rap62-wall/",
        "title": "RG-RAP62-Wall official product page",
        "values": {
            "dimensions_mm": t("86 x 23.5 x 125 mm (W x D x H; excluding mounting bracket)"),
            "ethernet_interfaces": t("5 x 10/100/1000BASE-T (1 WAN + 4 LAN); LAN4 supports PoE output"),
            "poe_output": t("10 W PoE budget when powered by IEEE 802.3at"),
            "fast_roaming": t("AI Roaming"),
            "centralized_management": t("Ruijie Cloud"),
            "max_channel_width_mhz": n(160, "160 MHz"),
            "wireless_security": t("WPA3; VLAN-based service isolation"),
        },
        "locations": {
            "max_channel_width_mhz": "Official launch article, Core Highlights section",
            "wireless_security": "Official launch article, Enterprise-Grade Reliability section",
        },
    },
    "RG-RAP72-Wall": {
        "url": "https://reyee.ruijie.com/en-global/products/sme/wireless/rg-rap72-wall/",
        "title": "RG-RAP72-Wall official product page",
        "values": {
            "dimensions_mm": t("86 x 24 x 124 mm (W x D x H; excluding mounting bracket)"),
            "centralized_management": t("Ruijie Cloud"),
        },
    },
    "RG-RAP73Pro": {
        "url": "https://reyee.ruijie.com/en-global/products/sme/wireless/rg-rap73pro/",
        "title": "RG-RAP73Pro official product page",
        "values": {
            "dimensions_mm": t("220 x 220 x 45 mm (W x D x H; excluding mounting bracket)"),
            "fast_roaming": t("Supported; official lab scenario reports roaming latency below 60 ms"),
            "centralized_management": t("Ruijie Cloud"),
        },
    },
    "RG-RAP73HD": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-indoor-ap/rap73hd/",
        "title": "RG-RAP73HD official product page",
        "values": {
            "dimensions_mm": t("258 x 258 x 59.5 mm (W x D x H; excluding mounting bracket)"),
            "ethernet_interfaces": t("1 x 1 GbE RJ45 + 1 x 100M/1G/2.5G/5G/10GBASE-T RJ45 + 1 x 10GE SFP+"),
            "centralized_management": t("Ruijie Cloud; remote monitoring, maintenance and firmware upgrade"),
        },
    },
}

LAUNCH_URL = "https://reyee.ruijie.com/fr-fr/about/news/rg-rap62-wall-series-launch-news/"


class Command(BaseCommand):
    help = "Import manually verified current Reyee AP product-page specifications (round 16)."

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
            page_source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Current official global product page, accessed 2026-10-21",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": row["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            launch_source = None
            if model == "RG-RAP62-Wall":
                launch_source, _ = SourceDocument.objects.update_or_create(
                    url=LAUNCH_URL,
                    document_version="Official launch article dated 2025-08-14",
                    defaults={
                        "brand": brand,
                        "product": product,
                        "document_type": SourceDocument.DocumentType.SUPPORT,
                        "title": "RG-RAP62-Wall Series Launch",
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
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
                ))
                old_value = None if not had else old.value_text if old.value_text else old.value_number
                source = launch_source if code in {"max_channel_width_mhz", "wireless_security"} else page_source
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": source.url[:200],
                    "source_note": "Manually verified from the current official Reyee product page or official launch article.",
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
                    new += 1
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                location = row.get("locations", {}).get(code, "Official product page, features/key specifications")
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=location,
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
