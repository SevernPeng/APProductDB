from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PRODUCTS = {
    "RG-RAP6260(G)": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-outdoor-ap/rap6260g/",
        "version": "Current official product page, accessed 2026-10-21",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Free cloud management; centralized network management; remote monitoring and maintenance"),
            "dimensions_mm": ("298 x 298 x 65 mm", "Product dimensions (W x D x H): 298 mm x 298 mm x 65 mm, excluding mounting bracket"),
            "ethernet_interfaces": ("1 x 10/100/1000BASE-T + 1 x 1GE SFP", "One 10/100/1000BASE-T port and one 1GE SFP port"),
            "fast_roaming": ("Layer 3 fast and seamless roaming", "Layer 3 roaming provides fast and seamless roaming switchover"),
        },
    },
    "RG-RAP6262(G)": {
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_77058/",
        "version": "Installation Guide V1.5, 2025-10-21",
        "values": {
            "antenna_gain_dbi": ("2.4 GHz: 3 dBi; 5 GHz: 3 dBi", "Antenna gain: 3.00 dBi at 2.4 GHz and 3.00 dBi at 5 GHz"),
            "centralized_management": ("RG-WS wireless controller; Ruijie Cloud", "Managed by RG-WS series wireless access controllers; official product page provides free cloud management"),
            "lightning_protection_kv": ("Ethernet: ±4 kV common mode; antenna/power: 6 kV", "Surge protection: Ethernet port ±4 kV common mode; built-in lightning protection supports 6 kV at antenna and power ports"),
            "max_channel_width_mhz": (80, "5 GHz channel width: Auto/20/40/80 MHz"),
        },
    },
    "RG-RAP6262": {
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_77494/",
        "version": "Installation Guide V1.4, accessed 2026-10-21",
        "values": {
            "antenna_gain_dbi": ("2.4 GHz: 3 dBi; 5 GHz: 4 dBi", "Peak antenna gain: 3.00 dBi at 2.4 GHz and 4.00 dBi at 5 GHz"),
            "centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Official product page: free cloud management, remote Wi-Fi management and wireless optimization"),
            "ethernet_interfaces": ("1 x 10/100/1000BASE-T + 1 x 1GE SFP", "One 10/100/1000BASE-T port and one 1GE SFP port"),
            "wireless_range": ("2.4 GHz: radius up to 100 m; 5 GHz: radius up to 300 m", "Official product page: coverage radius 100 m at 2.4 GHz and 300 m at 5 GHz under field-test conditions"),
        },
    },
    "RG-RAP62-OD": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-outdoor-ap/rg-rap62-od/",
        "version": "Current official product page, accessed 2026-10-21",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Cloud management; Reyee Mesh and AI roaming features"),
            "ip_rating": ("IP65", "IP65 weatherproof rating"),
        },
    },
    "RG-RAP72Pro-OD": {
        "url": "https://reyee.ruijie.com/en-global/products/reyee-wireless/reyee-outdoor-ap/rg-rap72pro-od/",
        "version": "Current official product page, accessed 2026-10-21",
        "values": {
            "centralized_management": ("Ruijie Cloud; Ruijie Reyee App", "Official resources and management workflow use Ruijie Cloud and Ruijie Reyee App"),
        },
    },
}


def current_value(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    if spec.value_boolean is not None:
        return spec.value_boolean
    if spec.value_number is not None:
        return spec.value_number
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import/correct manually verified Reyee outdoor AP specifications (round 25)."

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
            doc_type = (
                SourceDocument.DocumentType.SUPPORT
                if "support/documents" in row["url"]
                else SourceDocument.DocumentType.PRODUCT_PAGE
            )
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version=row["version"],
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": doc_type,
                    "title": f"{model} official product specifications",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                old_value = current_value(old)
                new_value = Decimal(str(value)) if isinstance(value, (int, float)) else str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults={
                        "value_status": ProductSpec.ValueStatus.PUBLISHED,
                        "value_text": "" if isinstance(value, (int, float)) else str(value),
                        "value_number": new_value if isinstance(new_value, Decimal) else None,
                        "value_boolean": None,
                        "normalized_value": str(value),
                        "unit": definition.unit,
                        "raw_value": raw,
                        "source_url": row["url"][:200],
                        "source_note": "Manually verified from the current official Reyee page or latest official installation guide.",
                        "verified_date": accessed,
                    },
                )
                if old_value is None:
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
                    source_location="Product features / Key Specifications / Technical Specifications",
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
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
                f"unchanged={unchanged} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(details))
