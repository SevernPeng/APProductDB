from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


URL = "https://techspecs.ui.com/unifi/switching/usw-enterprise-8-poe"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


VALUES = {
    "poe_ports": n(8, "8 PoE+ ports"),
    "poe_standard": t("PoE/PoE+ output", "Max. PoE output: up to PoE+"),
    "poe_budget_w": n(120, "Total PoE availability: 120 W"),
    "max_poe_per_port_w": n(32, "Maximum PoE+ wattage per port by PSE: 32 W"),
    "vlan_count": n(1000, "Supported VLANs: 1,000"),
    "mac_address_table": t("16000 entries", "MAC address table size: 16,000"),
    "routing_entry_capacity": t("256 IPv4 static routes"),
    "l3_features": t("DHCP server; inter-VLAN routing; static routing"),
    "l2_features": t(
        "LACP; advanced IGMP configuration and snooping; 802.1X; flow control; storm control; "
        "multicast and broadcast rate limiting; port isolation and mirroring; LLDP-MED; voice VLAN; loop protection"
    ),
    "stp_features": t("STP and RSTP"),
    "acl_security": t(
        "12 IPv4 ACLs and 10 MAC ACLs; MAC- and IP-based ACLs; network and device isolation; "
        "DHCP snooping and guarding; MAC address blocking; MAC-based port restriction"
    ),
}


class Command(BaseCommand):
    help = "Import manually verified Ubiquiti USW-Enterprise-8-PoE gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Missing brand: Ubiquiti")
        product = Product.objects.filter(brand=brand, model="USW-Enterprise-8-PoE", is_published=True).first()
        if not product:
            raise CommandError("Missing Ubiquiti product: USW-Enterprise-8-PoE")

        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=VALUES)}
        if missing := VALUES.keys() - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        document, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="Official current UniFi Tech Specs page, accessed 2026-10-22",
            defaults={
                "brand": brand,
                "product": product,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "Ubiquiti UniFi Enterprise 8 PoE (Vintage) Tech Specs",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )

        newly_filled = corrected = unchanged = 0
        for code, (kind, value, raw) in VALUES.items():
            definition = definitions[code]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(
                existing
                and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                and (
                    bool((existing.value_text or "").strip())
                    or existing.value_number is not None
                    or existing.value_boolean is not None
                )
            )
            old_value = None
            if had:
                old_value = existing.value_text or existing.value_number

            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(value),
                "unit": definition.unit,
                "raw_value": raw,
                "source_url": URL[:200],
                "source_note": "Manually verified from Ubiquiti's official current exact-model Tech Specs page.",
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
                newly_filled += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1

            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=document,
                source_location=f"Official Tech Specs table - USW-Enterprise-8-PoE - {code}",
                defaults={
                    "source_excerpt": f"{definition.display_name}: {raw}",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={len(VALUES)} newly_filled={newly_filled} "
                f"corrected={corrected} unchanged={unchanged} models=1"
            )
        )
