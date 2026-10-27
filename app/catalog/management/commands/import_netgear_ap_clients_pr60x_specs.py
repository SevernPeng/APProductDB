from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "WAC730": {
        "url": "https://www.netgear.com/images/pdf/NETGEAR_Catalog_V5-25.pdf",
        "title": "NETGEAR product catalog - Wireless Access Points comparison",
        "version": "Official NETGEAR catalog; accessed 2026-10-20",
        "excerpt": "Maximum concurrent clients (standalone): 256",
    },
    "WAX608Y": {
        "url": "https://www.netgear.com/business/wifi/access-points/wax608y/",
        "title": "NETGEAR WAX608Y official product page",
        "version": "Official product page; accessed 2026-10-20",
        "excerpt": "Maximum users: 250",
    },
    "WBE718": {
        "url": "https://kb.netgear.com/000066242",
        "title": "NETGEAR WBE718 firmware feature specification",
        "version": "Official NETGEAR support article; accessed 2026-10-20",
        "excerpt": "600 concurrent client connections (200 clients per radio)",
    },
    "WBE750": {
        "url": "https://kb.netgear.com/000066050/WBE750-WBE758-Firmware-Version-11-0-1-22",
        "title": "NETGEAR WBE750 and WBE758 firmware feature specification",
        "version": "Official NETGEAR support article; accessed 2026-10-20",
        "excerpt": "600 concurrent client connections (200 clients per radio)",
    },
    "WBE758": {
        "url": "https://kb.netgear.com/000066050/WBE750-WBE758-Firmware-Version-11-0-1-22",
        "title": "NETGEAR WBE750 and WBE758 firmware feature specification",
        "version": "Official NETGEAR support article; accessed 2026-10-20",
        "excerpt": "600 concurrent client connections (200 clients per radio)",
    },
    "PR60X": {
        "url": "https://www.downloads.netgear.com/files/GDC/PR60X/PR60X_DS.pdf",
        "title": "NETGEAR PR60X 10G/multi-gigabit dual WAN Pro Router datasheet",
        "version": "NG_DS_ENT_PR60X-060526; accessed 2026-10-20",
        "excerpt": "LAN-to-WAN throughput: 9.4 Gbps for the 10G WAN port",
    },
}


VALUES = {
    "WAC730": ("max_clients", 256),
    "WAX608Y": ("max_clients", 250),
    "WBE718": ("max_clients", 600),
    "WBE750": ("max_clients", 600),
    "WBE758": ("max_clients", 600),
    "PR60X": ("nat_throughput_mbps", 9400),
}


class Command(BaseCommand):
    help = "Import verified NETGEAR AP client capacities and PR60X NAT throughput."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in={v[0] for v in VALUES.values()})}
        if len(definitions) != 2:
            raise CommandError("Missing max_clients or nat_throughput_mbps definition")
        accessed = timezone.localdate()
        documents = {}
        for model, source_data in SOURCES.items():
            documents[model], _ = SourceDocument.objects.update_or_create(
                url=source_data["url"], document_version=source_data["version"],
                defaults={
                    "brand": brand, "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET if model == "PR60X" else SourceDocument.DocumentType.SUPPORT,
                    "title": source_data["title"], "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
        newly_filled = corrected = unchanged = 0
        for model, (code, value) in VALUES.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            definition = definitions[code]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and existing.value_number is not None)
            old_status = existing.value_status if existing else None
            old_value = existing.value_number if had else None
            new_value = Decimal(str(value))
            source_data = SOURCES[model]
            spec, _ = ProductSpec.objects.update_or_create(
                product=product, definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED, "value_text": "",
                    "value_number": new_value, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit,
                    "raw_value": source_data["excerpt"], "source_url": source_data["url"][:200],
                    "source_note": "Manually verified from an official NETGEAR page or document.",
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
                product_spec=spec, source_document=documents[model],
                source_location=f"Official specification - {model} - {code}",
                defaults={
                    "source_excerpt": source_data["excerpt"],
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(VALUES)} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged}"
        ))
