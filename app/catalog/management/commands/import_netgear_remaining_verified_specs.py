from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


ITEMS = [
    {
        "model": "GS510TP", "code": "jumbo_frame_bytes", "kind": "number", "value": 9216,
        "raw": "Jumbo frame: maximum 9,216 bytes",
        "url": "https://www.downloads.netgear.com/files/GDC/GS510TP/GS510TP_GS110TP-SWA.pdf",
        "title": "NETGEAR GS510TP and GS110TP software administration manual",
        "version": "Official NETGEAR software administration manual; accessed 2026-10-20",
        "location": "Hardware specifications and default values - traffic control",
    },
    {
        "model": "M4100-26G", "code": "fan_design", "kind": "text", "value": "Active cooling; acoustic noise <35.6 dBA at 25 °C",
        "raw": "Acoustic noise (ANSI-S10.12) at 25 °C: <35.6 dBA",
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/M4100.pdf",
        "title": "NETGEAR ProSAFE Intelligent Edge Managed Switches M4100 series datasheet",
        "version": "Official NETGEAR M4100 series datasheet; accessed 2026-10-20",
        "location": "p. 19 - acoustic noise table",
    },
    {
        "model": "M4100-26G-PoE", "code": "fan_design", "kind": "text", "value": "Active cooling; acoustic noise <36.6 dBA at 25 °C",
        "raw": "Acoustic noise (ANSI-S10.12) at 25 °C: <36.6 dBA",
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/M4100.pdf",
        "title": "NETGEAR ProSAFE Intelligent Edge Managed Switches M4100 series datasheet",
        "version": "Official NETGEAR M4100 series datasheet; accessed 2026-10-20",
        "location": "p. 19 - acoustic noise table",
    },
    {
        "model": "AGM734", "code": "accessory_max_distance_km", "kind": "number", "value": 0.1,
        "raw": "Gigabit Ethernet up to 100 m with CAT5E/CAT6 cable",
        "url": "https://www.netgear.com/business/wired/switches/accessories/agm734/",
        "title": "NETGEAR AGM734 official product page",
        "version": "Official product page; accessed 2026-10-20",
        "location": "Features - transmission distance",
    },
]


class Command(BaseCommand):
    help = "Import remaining individually verified NETGEAR specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in={i["code"] for i in ITEMS})}
        if missing := {i["code"] for i in ITEMS} - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        newly_filled = corrected = unchanged = 0
        for item in ITEMS:
            doc_key = (item["url"], item["version"])
            if doc_key not in documents:
                documents[doc_key], _ = SourceDocument.objects.update_or_create(
                    url=item["url"], document_version=item["version"],
                    defaults={
                        "brand": brand, "product": None,
                        "document_type": SourceDocument.DocumentType.DATASHEET if item["url"].endswith(".pdf") else SourceDocument.DocumentType.PRODUCT_PAGE,
                        "title": item["title"], "region": "Global", "published_date": None,
                        "accessed_date": accessed, "active": True,
                    },
                )
            product = Product.objects.filter(brand=brand, model=item["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {item['model']}")
            definition = definitions[item["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None
            ))
            old_status = existing.value_status if existing else None
            old_value = existing.value_text if had and existing.value_text else (existing.value_number if had else None)
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "",
                "value_number": None, "value_boolean": None, "normalized_value": str(item["value"]),
                "unit": definition.unit, "raw_value": item["raw"], "source_url": item["url"][:200],
                "source_note": "Manually verified from the official NETGEAR source.", "verified_date": accessed,
            }
            if item["kind"] == "number":
                new_value = Decimal(str(item["value"])); defaults["value_number"] = new_value
            else:
                new_value = str(item["value"]); defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                newly_filled += 1
            elif old_status != ProductSpec.ValueStatus.PUBLISHED or old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[doc_key], source_location=item["location"],
                defaults={
                    "source_excerpt": item["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
