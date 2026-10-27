from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


ITEMS = [
    {
        "model": "GS205", "code": "max_power_consumption_w", "kind": "number", "value": 3.56,
        "raw": "Power consumption — GS205: 3.56W",
        "url": "https://www.downloads.netgear.com/files/GDC/GS205/GS205_GS208_Combined_IG_20Dec2012.pdf",
        "title": "NETGEAR GS205/GS208 Installation Guide",
        "version": "Official installation guide, December 2012; accessed 2026-10-20",
        "location": "p. 2 - Specifications",
    },
    {
        "model": "GS205", "code": "operating_temperature_c", "kind": "text", "value": "0 to 40 °C",
        "raw": "Operating temperature: 0°–40° C (32°–104° F)",
        "url": "https://www.downloads.netgear.com/files/GDC/GS205/GS205_GS208_Combined_IG_20Dec2012.pdf",
        "title": "NETGEAR GS205/GS208 Installation Guide",
        "version": "Official installation guide, December 2012; accessed 2026-10-20",
        "location": "p. 2 - Specifications",
    },
    {
        "model": "GS205", "code": "installation", "kind": "text",
        "value": "Desktop installation: position switch, connect equipment and power, then check status LEDs",
        "raw": "Step 1. Position switch; Step 2. Connect equipment; Step 3. Connect power; Step 4. Check status",
        "url": "https://www.downloads.netgear.com/files/GDC/GS205/GS205_GS208_Combined_IG_20Dec2012.pdf",
        "title": "NETGEAR GS205/GS208 Installation Guide",
        "version": "Official installation guide, December 2012; accessed 2026-10-20",
        "location": "p. 1 - Installation steps",
    },
    {
        "model": "GS608", "code": "fanless", "kind": "boolean", "value": True,
        "raw": "Fanless design for quiet operation",
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/GS605v3-GS608.pdf",
        "title": "NETGEAR GS605v3/GS608 Data Sheet",
        "version": "Official datasheet D-GS605v3/GS608-2; accessed 2026-10-20",
        "location": "p. 1 - Product highlights",
    },
    {
        "model": "GS608", "code": "installation", "kind": "text", "value": "Plug-and-play desktop installation",
        "raw": "Plug-and-play installation delivers ease of use",
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/GS605v3-GS608.pdf",
        "title": "NETGEAR GS605v3/GS608 Data Sheet",
        "version": "Official datasheet D-GS605v3/GS608-2; accessed 2026-10-20",
        "location": "p. 1 - Product highlights",
    },
    {
        "model": "GS608", "code": "qos_support", "kind": "text", "value": "IEEE 802.1p priority tags",
        "raw": "Standards Compliance — IEEE 802.1p priority tags",
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/GS605v3-GS608.pdf",
        "title": "NETGEAR GS605v3/GS608 Data Sheet",
        "version": "Official datasheet D-GS605v3/GS608-2; accessed 2026-10-20",
        "location": "p. 2 - Standards compliance",
    },
    {
        "model": "WAC510", "code": "mesh_support", "kind": "boolean", "value": False,
        "raw": "Instant WiFi Mesh — Wireless backhaul to form Mesh Network: WAC510 — No",
        "url": "https://www.downloads.netgear.com/files/GDC/WAX610/WAX610_WAX610Y_DS.pdf",
        "title": "NETGEAR WAX610/WAX610Y Data Sheet",
        "version": "Latest official product-comparison datasheet; accessed 2026-10-20",
        "location": "p. 6 - Product comparison, Instant WiFi Mesh",
    },
    *[
        {
            "model": model, "code": "pbr_support", "kind": "boolean", "value": True,
            "raw": "Policy-based routing (PBR) is supported and can override destination-based routing using route maps",
            "url": "https://www.downloads.netgear.com/files/GDC/M5300/M5300-M6100-M7100_SWA_EN.pdf",
            "title": "NETGEAR M5300, M6100, and M7100 Software Administration Manual",
            "version": "Official Software Administration Manual, release 11.0; accessed 2026-10-20",
            "location": "Chapter 10 - Policy-Based Routing",
        }
        for model in ("M5300-28G", "M5300-28G-POE+", "M5300-52G", "M5300-52G-POE+")
    ],
    {
        "model": "M4300-24XF", "code": "ip_interface_capacity", "kind": "text",
        "value": "128 routing interfaces (port or VLAN)",
        "raw": "Number of routing interfaces (including port/vlan): 128",
        "url": "https://www.downloads.netgear.com/files/GDC/datasheet/en/M4300-24X-48X.pdf",
        "title": "NETGEAR M4300 Series Data Sheet",
        "version": "Official M4300 series datasheet; accessed 2026-10-20",
        "location": "p. 44 - Layer 3 scaling",
    },
    *[
        {
            "model": model, "code": "ip_interface_capacity", "kind": "text",
            "value": "128 IP routing interfaces (port or VLAN)",
            "raw": "Number of IP routing interfaces (port or VLAN): 128",
            "url": "https://www.downloads.netgear.com/files/GDC/M4500/M4500_CampusIT_Datasheet.pdf",
            "title": "NETGEAR M4500 Campus IT Data Sheet",
            "version": "Official requirements based on software release 7.0 datasheet; accessed 2026-10-20",
            "location": "p. 26 - Performance summary",
        }
        for model in ("M4500-32C", "M4500-48XF8C")
    ],
    *[
        {
            "model": model, "code": "stacking", "kind": "text",
            "value": "Traditional switch stacking not supported; MLAG is supported",
            "raw": "Stacking Features — Max Stacking members: No; MLAG is supported elsewhere in the same official datasheet",
            "url": "https://www.downloads.netgear.com/files/GDC/M4500/M4500_CampusIT_Datasheet.pdf",
            "title": "NETGEAR M4500 Campus IT Data Sheet",
            "version": "Official requirements based on software release 7.0 datasheet; accessed 2026-10-20",
            "location": "p. 29 - Stacking features",
        }
        for model in ("M4500-32C", "M4500-48XF8C")
    ],
]


class Command(BaseCommand):
    help = "Import final manually verified NETGEAR gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        codes = {item["code"] for item in ITEMS}
        definitions = {definition.code: definition for definition in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
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
                        "document_type": SourceDocument.DocumentType.DATASHEET,
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
                "raw_value": item["raw"], "source_url": item["url"][:200],
                "source_note": "Manually verified from the official NETGEAR source.",
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
