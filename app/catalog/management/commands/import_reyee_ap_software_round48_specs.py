from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


CONFIG_URL = (
    "https://reyee.ruijie.com/en-global/support/documents/"
    "slide_rg-rap-series-access-points-reyeeos-2-320-configuration-guide/"
)
SECURITY_VALUE = "WPA-PSK, WPA2-PSK, WPA/WPA2-PSK, OWE, WPA3-SAE, WPA2-PSK/WPA3-SAE"
SECURITY_RAW = (
    "Supported encryption modes include WPA-PSK, WPA2-PSK, WPA/WPA2-PSK, "
    "OWE (Enhanced Open), WPA3-SAE, and WPA2-PSK/WPA3-SAE."
)

ENTRIES = []
for model in ["RG-RAP62-OD", "RG-RAP6260(G)", "RG-RAP6262", "RG-RAP6262(G)", "RG-RAP72Pro-OD"]:
    ENTRIES.append({
        "model": model,
        "code": "wireless_security",
        "value": SECURITY_VALUE,
        "raw": SECURITY_RAW,
        "url": CONFIG_URL,
        "version": f"ReyeeOS 2.380[360][320] Configuration Guide V1.7: {model}",
        "title": f"Ruijie Reyee RG-RAP Series Configuration Guide - {model}",
        "location": "Wi-Fi encryption modes and supported AP models",
    })

ENTRIES.extend([
    {
        "model": "RG-RAP2260(G)",
        "code": "fast_roaming",
        "value": "802.11k/v roaming and fast transition (802.11r)",
        "raw": "802.11r is supported on RG-RAP2260(G); 802.11k/v roaming optimization is supported.",
        "url": CONFIG_URL,
        "version": "ReyeeOS 2.380[360][320] Configuration Guide V1.7: RG-RAP2260(G)",
        "title": "Ruijie Reyee RG-RAP Series Configuration Guide - RG-RAP2260(G)",
        "location": "Configuring 802.11r and 802.11k/v roaming optimization",
    },
    {
        "model": "RG-RAP6260(G)",
        "code": "wireless_range",
        "value": "2.4 GHz: max 150 m, recommended 50 m; 5 GHz: max 400 m, recommended 200 m",
        "raw": "Coverage range: 5 GHz max 400 m, recommended 200 m; 2.4 GHz max 150 m, recommended 50 m (ideal unobstructed environment).",
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_ruijie-reyee-rg-rap6260-g-access-point-hardware-installation-and-reference-guide-en/",
        "version": "Installation Guide V1.5",
        "title": "Ruijie Reyee RG-RAP6260(G) Access Point Installation Guide",
        "location": "Technical Specifications - Coverage range",
    },
    {
        "model": "RG-RAP72Pro-OD",
        "code": "wireless_range",
        "value": "2.4 GHz: max 100 m, recommended 50 m; 5 GHz: max 300 m, recommended 150 m",
        "raw": "Coverage range: 5 GHz max 300 m, recommended 150 m; 2.4 GHz max 100 m, recommended 50 m (ideal unobstructed environment).",
        "url": "https://reyee.ruijie.com/en-global/support/documents/slide_rg-rap72pro-od-access-point-installation-guide/",
        "version": "Installation Guide V1.1",
        "title": "Ruijie Reyee RG-RAP72Pro-OD Access Point Installation Guide",
        "location": "Technical Specifications - Coverage range",
    },
])


def actual(spec):
    if not spec or spec.value_status != ProductSpec.ValueStatus.PUBLISHED:
        return None
    return spec.value_text if (spec.value_text or "").strip() else None


class Command(BaseCommand):
    help = "Import official outdoor-AP security, roaming, and range gaps (round 48)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Reyee").first()
        codes = {entry["code"] for entry in ENTRIES}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if not brand or len(definitions) != len(codes):
            raise CommandError("Missing Reyee brand or AP software definitions")

        accessed = timezone.localdate()
        written = new = corrected = unchanged = 0
        details = []
        for entry in ENTRIES:
            model = entry["model"]
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published Reyee product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=entry["url"],
                document_version=entry["version"],
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.SUPPORT,
                    "title": entry["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            definition = definitions[entry["code"]]
            old = ProductSpec.objects.filter(product=product, definition=definition).first()
            old_value = actual(old)
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": entry["value"],
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": entry["value"],
                    "unit": definition.unit,
                    "raw_value": entry["raw"],
                    "source_url": entry["url"][:200],
                    "source_note": "Manually verified from the current official exact-model guide or supported-model configuration guide.",
                    "verified_date": accessed,
                },
            )
            if old_value is None:
                new += 1
                detail = "+1"
            elif old_value != entry["value"]:
                corrected += 1
                detail = "corrected:1"
            else:
                unchanged += 1
                detail = "unchanged:1"
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=source,
                source_location=entry["location"],
                defaults={
                    "source_excerpt": entry["raw"],
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )
            written += 1
            details.append(f"{model}.{entry['code']}:{detail}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len({entry['model'] for entry in ENTRIES})}"
        ))
        self.stdout.write("; ".join(details))
