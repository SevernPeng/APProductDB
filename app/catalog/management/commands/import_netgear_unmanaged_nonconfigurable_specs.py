from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


MODELS = [
    "GS108LP", "GS205", "GS305", "GS305P", "GS308", "GS308P", "GS316", "GS316P",
    "GS324", "GS348", "GS608", "JGS516", "JGS524", "XS505M", "XS508M",
]

NONCONFIGURABLE_FIELDS = {
    "vlan_support": "Not applicable: unmanaged plug-and-play switch with no software or configuration",
    "link_aggregation": "Not applicable: unmanaged plug-and-play switch with no software or configuration",
    "port_mirroring": "Not applicable: unmanaged plug-and-play switch with no software or configuration",
    "cable_test": "Not applicable: unmanaged plug-and-play switch with no management or diagnostic configuration",
}


class Command(BaseCommand):
    help = "Mark configurable management features not applicable on verified NETGEAR unmanaged switches."
    catalog_url = "https://www.downloads.netgear.com/files/netgear/documents/netgear-interactive-catalog_14jan21.pdf"
    document_version = "Official NETGEAR catalog: Unmanaged Switches - Plug-and-Play, No Configuration; accessed 2026-10-20"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=NONCONFIGURABLE_FIELDS)}
        if missing := NONCONFIGURABLE_FIELDS.keys() - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=self.catalog_url, document_version=self.document_version,
            defaults={
                "brand": brand, "product": None,
                "document_type": SourceDocument.DocumentType.CATALOG,
                "title": "NETGEAR product catalog - Unmanaged Switches: Plug-and-Play, No Configuration",
                "region": "Global", "published_date": None, "accessed_date": accessed, "active": True,
            },
        )
        written = newly_classified = corrected = unchanged = 0
        for model in MODELS:
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            for code, raw in NONCONFIGURABLE_FIELDS.items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_status = existing.value_status if existing else None
                had_published = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                if had_published:
                    raise CommandError(
                        f"Refusing to replace published data: {model}.{code}. Review the model classification first."
                    )
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.NOT_APPLICABLE,
                        "value_text": "", "value_number": None, "value_boolean": None,
                        "normalized_value": "", "unit": definition.unit, "raw_value": raw,
                        "source_url": (product.official_url or self.catalog_url)[:200],
                        "source_note": (
                            "NETGEAR officially classifies this model as an unmanaged plug-and-play switch; "
                            "configurable management and diagnostic features are therefore not applicable."
                        ),
                        "verified_date": accessed,
                    },
                )
                if old_status in {None, ProductSpec.ValueStatus.UNKNOWN}:
                    newly_classified += 1
                elif old_status != ProductSpec.ValueStatus.NOT_APPLICABLE:
                    corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"Unmanaged switch classification - {model} - {code}",
                    defaults={
                        "source_excerpt": "Unmanaged Switches - Plug-and-Play, No Configuration",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_classified={newly_classified} corrected={corrected} "
            f"unchanged={unchanged} models={len(MODELS)}"
        ))
