from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "SWA": {
        "url": "https://www.downloads.netgear.com/files/GDC/M4200/M4200-M4300_SWA_EN.pdf",
        "title": "NETGEAR M4200 and M4300 Software Administration Manual, software version 12.0.2",
        "version": "Official software administration manual, version 12.0.2; accessed 2026-10-21",
    },
    "WEB": {
        "url": "https://www.downloads.netgear.com/files/GDC/M4200/M4200-M4300_UM_EN.pdf",
        "title": "NETGEAR M4200 and M4300 Web Management User Manual, software version 12.0.2",
        "version": "Official web management user manual, version 12.0.2; accessed 2026-10-21",
    },
    "CLI": {
        "url": "https://www.downloads.netgear.com/files/GDC/M4200/M4200-M4300_CLI_EN.pdf",
        "title": "NETGEAR M4200 and M4300 CLI Command Reference Manual, software version 12.0.0",
        "version": "Official CLI command reference, version 12.0.0; accessed 2026-10-21",
    },
}


ITEMS = [
    {
        "code": "pbr_support", "kind": "boolean", "value": True, "source": "SWA",
        "raw": "Policy-based routing (PBR) enables administrators to define forwarding behavior based on packet contents; route maps can be applied to inbound traffic on routing interfaces.",
        "location": "Chapter 8 — PBR, Policy-Based Routing Concepts and configuration",
    },
    {
        "code": "ospf_support", "kind": "boolean", "value": True, "source": "WEB",
        "raw": "Routing > OSPF > Advanced provides OSPF configuration, interface configuration, areas, neighbors, and graceful restart controls.",
        "location": "OSPF and OSPFv3 chapters — OSPF configuration",
    },
    {
        "code": "vrrp_support", "kind": "boolean", "value": True, "source": "CLI",
        "raw": "The routing command reference includes Virtual Router Redundancy Protocol commands for the M4200 and M4300 software platform.",
        "location": "Routing Commands — Virtual Router Redundancy Protocol Commands",
    },
    {
        "code": "multicast_routing", "kind": "boolean", "value": True, "source": "CLI",
        "raw": "The multicast command reference includes DVMRP, PIM, IGMP Proxy, IPv6 multicast forwarding, IPv6 PIM, and MLD commands.",
        "location": "Multicast Commands — DVMRP, PIM, IGMP and IPv6 multicast sections",
    },
    {
        "code": "stacking", "kind": "text", "value": "Not supported; stacking commands are supported on M4300 series switches only", "source": "CLI",
        "raw": "Note: Stacking commands are supported on the M4300 series switches only.",
        "location": "Chapter 4 — Stacking Commands, applicability note",
    },
]


class Command(BaseCommand):
    help = "Import manually verified NETGEAR M4200 advanced routing and stacking specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        product = Product.objects.filter(brand=brand, model="M4200-10MG-PoE+", is_published=True).first()
        if not product:
            raise CommandError("Missing NETGEAR product: M4200-10MG-PoE+")
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
                        "brand": brand, "product": product,
                        "document_type": SourceDocument.DocumentType.SUPPORT,
                        "title": src["title"], "region": "Global", "published_date": None,
                        "accessed_date": accessed, "active": True,
                    },
                )
            definition = definitions[item["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
            ))
            if item["kind"] == "boolean":
                old_value = existing.value_boolean if had else None
                new_value = bool(item["value"])
            elif item["kind"] == "number":
                old_value = existing.value_number if had else None
                new_value = Decimal(str(item["value"]))
            else:
                old_value = existing.value_text if had else None
                new_value = str(item["value"])
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "", "value_number": None, "value_boolean": None,
                "normalized_value": str(item["value"]), "unit": definition.unit,
                "raw_value": item["raw"], "source_url": src["url"][:200],
                "source_note": "Manually verified from an official NETGEAR M4200/M4300 software manual; model-specific exclusions were honored.",
                "verified_date": accessed,
            }
            if item["kind"] == "boolean":
                defaults["value_boolean"] = new_value
            elif item["kind"] == "number":
                defaults["value_number"] = new_value
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
