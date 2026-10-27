from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "GS205": {
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/200-Series_DS.pdf",
        "title": "NETGEAR 200 Series Home/Office Ethernet Switches Data Sheet",
        "version": "Official data sheet DS-200Series-16Dec20; accessed 2026-10-21",
        "type": SourceDocument.DocumentType.DATASHEET,
    },
    "CATALOG": {
        "url": "https://www.downloads.netgear.com/files/netgear/documents/netgear-interactive-catalog_19apr21.pdf",
        "title": "NETGEAR Product Catalog — Unmanaged Switches",
        "version": "Official NETGEAR product catalog, 19 April 2021; accessed 2026-10-21",
        "type": SourceDocument.DocumentType.CATALOG,
    },
    "WAC": {
        "url": "https://kb.netgear.com/ja/000053040/",
        "title": "NETGEAR Business Wireless Product Comparison Table",
        "version": "Official NETGEAR support comparison table; accessed 2026-10-21",
        "type": SourceDocument.DocumentType.SUPPORT,
    },
}


ITEMS = [
    {"model": "GS205", "code": "fanless", "kind": "boolean", "value": True, "source": "GS205", "raw": "Ideal for Home Networks — Fanless for silent operation", "location": "p. 1 — Ideal for Home Networks"},
    {"model": "GS205", "code": "qos_support", "kind": "text", "value": "IEEE 802.1p QoS", "source": "GS205", "raw": "Standards: IEEE 802.1p QoS (applies to GS205 and GS208)", "location": "p. 2 — Standards"},
    {"model": "GS205", "code": "dimensions_mm", "kind": "text", "value": "110 x 71 x 23 mm", "source": "GS205", "raw": "GS205 width x depth x height: 110 x 71 x 23 mm", "location": "p. 2 — Physical Specifications"},
    {"model": "GS205", "code": "max_power_consumption_w", "kind": "number", "value": 2.34, "source": "GS205", "raw": "GS205 power consumption (max / standby): 2.34W / 0.45W", "location": "p. 2 — Energy Efficiency"},
    {"model": "JGS516", "code": "fanless", "kind": "boolean", "value": True, "source": "CATALOG", "raw": "Unmanaged Switches comparison — JGS516 — Fan(s): None", "location": "Unmanaged Switches comparison table — JGS516 physical specifications"},
    {"model": "JGS524", "code": "fanless", "kind": "boolean", "value": True, "source": "CATALOG", "raw": "Unmanaged Switches comparison — JGS524 — Fan(s): None", "location": "Unmanaged Switches comparison table — JGS524 physical specifications"},
    {"model": "WAC730", "code": "mesh_support", "kind": "boolean", "value": False, "source": "WAC", "raw": "Business wireless product comparison — WAC730 — Instant Mesh: –", "location": "Business wireless comparison table — Instant Mesh row"},
]


class Command(BaseCommand):
    help = "Import late-round manually verified NETGEAR switch and access-point gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        codes = {item["code"] for item in ITEMS}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        newly_filled = corrected = unchanged = 0
        for item in ITEMS:
            src = SOURCES[item["source"]]
            key = (src["url"], src["version"])
            if key not in documents:
                documents[key], _ = SourceDocument.objects.update_or_create(
                    url=src["url"], document_version=src["version"],
                    defaults={
                        "brand": brand, "product": None, "document_type": src["type"],
                        "title": src["title"], "region": "Global", "published_date": None,
                        "accessed_date": accessed, "active": True,
                    },
                )
            product = Product.objects.filter(brand=brand, model=item["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {item['model']}")
            definition = definitions[item["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
            ))
            if item["kind"] == "number":
                old_value = existing.value_number if had else None
                new_value = Decimal(str(item["value"]))
            elif item["kind"] == "boolean":
                old_value = existing.value_boolean if had else None
                new_value = bool(item["value"])
            else:
                old_value = existing.value_text if had else None
                new_value = str(item["value"])
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "", "value_number": None, "value_boolean": None,
                "normalized_value": str(item["value"]), "unit": definition.unit,
                "raw_value": item["raw"], "source_url": src["url"][:200],
                "source_note": "Manually verified from the official NETGEAR source; latest identifiable model data was preferred.",
                "verified_date": accessed,
            }
            if item["kind"] == "number":
                defaults["value_number"] = new_value
            elif item["kind"] == "boolean":
                defaults["value_boolean"] = new_value
            else:
                defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                newly_filled += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec, source_document=documents[key], source_location=item["location"],
                defaults={"source_excerpt": item["raw"], "evidence_level": SpecEvidence.EvidenceLevel.A, "verified_at": timezone.now()},
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
