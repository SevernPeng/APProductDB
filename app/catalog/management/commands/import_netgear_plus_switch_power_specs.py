from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "gs305e": {
        "url": "https://www.downloads.netgear.com/files/GDC/GS305E/GS305E_UM_EN.pdf",
        "title": "NETGEAR GS305E Gigabit Ethernet Easy Smart Managed Essentials Switch user manual",
        "version": "Official NETGEAR GS305E user manual, copyright 2026; accessed 2026-10-20",
    },
    "gs305e_gs308e": {
        "url": "https://www.downloads.netgear.com/files/GDC/GS308Ev4/GS305E_GS308E_DS.pdf",
        "title": "NETGEAR GS305E and GS308E Plus Gigabit Ethernet Switches datasheet",
        "version": "D-GS305E/GS308E-24May24; accessed 2026-10-20",
    },
    "gs305_308_poe": {
        "url": "https://www.downloads.netgear.com/files/GDC/GS305EP/GS305EP-EPP_GS308EP-EPP_UM_EN.pdf",
        "title": "NETGEAR GS305EP/EPP and GS308EP/EPP user manual",
        "version": "Official NETGEAR user manual, copyright 2026; accessed 2026-10-20",
    },
    "gs316_poe": {
        "url": "https://www.downloads.netgear.com/files/GDC/GS316EP/GS316EP_GS316EPP_UM_EN.pdf",
        "title": "NETGEAR GS316EP and GS316EPP user manual",
        "version": "Official NETGEAR user manual; accessed 2026-10-20",
    },
}


PRODUCTS = {
    "GS305E": ("gs305e", 2.6, "2.6 W maximum"),
    "GS308E": ("gs305e_gs308e", 3.7, "3.7 W maximum"),
    "GS305EP": ("gs305_308_poe", 74.7, "4.9 W without PoE; 74.7 W with maximum PoE"),
    "GS308EPP": ("gs305_308_poe", 141.4, "5.9 W without PoE; 141.4 W with maximum PoE"),
    "GS316EP": ("gs316_poe", 198.7, "10.1 W without PoE; 198.7 W with maximum PoE"),
    "GS316EPP": ("gs316_poe", 250.6, "10.2 W without PoE; 250.6 W with maximum PoE"),
}


class Command(BaseCommand):
    help = "Import manually verified maximum power consumption for NETGEAR Plus switches."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        definition = SpecDefinition.objects.filter(code="max_power_consumption_w").first()
        if not definition:
            raise CommandError("Missing definition: max_power_consumption_w")
        accessed = timezone.localdate()
        documents = {}
        for key, source_data in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=source_data["url"], document_version=source_data["version"],
                defaults={
                    "brand": brand, "product": None,
                    "document_type": SourceDocument.DocumentType.SUPPORT if key != "gs305e_gs308e" else SourceDocument.DocumentType.DATASHEET,
                    "title": source_data["title"], "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
        newly_filled = corrected = unchanged = 0
        for model, (source_key, value, raw) in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and existing.value_number is not None)
            old_status = existing.value_status if existing else None
            old_value = existing.value_number if had else None
            new_value = Decimal(str(value))
            source_data = SOURCES[source_key]
            spec, _ = ProductSpec.objects.update_or_create(
                product=product, definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "",
                    "value_number": new_value, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": source_data["url"][:200],
                    "source_note": "Manually verified from the official NETGEAR technical-specifications table.",
                    "verified_date": accessed,
                },
            )
            if not had:
                newly_filled += 1
            elif old_status != ProductSpec.ValueStatus.PUBLISHED or old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[source_key],
                source_location=f"Technical specifications - {model} - power consumption",
                defaults={
                    "source_excerpt": f"Maximum power consumption: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(PRODUCTS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
