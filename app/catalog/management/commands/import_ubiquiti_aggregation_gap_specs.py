from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


L2 = (
    "LACP; IGMP snooping; flow control; port isolation and mirroring; egress rate limiting; "
    "MAC/IP ACLs and isolation; DHCP snooping and guarding; LLDP-MED; voice VLAN; loop protection"
)
L3 = "DHCP server and relay; inter-VLAN routing; static routing"
STP = "STP and RSTP"

MODELS = {
    "ECS-Aggregation": {
        "url": "https://techspecs.ui.com/unifi/switching/ecs-aggregation",
        "values": {
            "switching_capacity_gbps": n(3600, "Switching capacity: 3.6 Tbps"),
            "packet_forwarding_rate_mpps": n(2400, "Forwarding rate: 2.4 Bpps"),
            "vlan_count": n(1000, "Supported VLANs: 1,000"),
            "mac_address_table": t("128000 entries", "MAC address table size: 128,000"),
            "routing_entry_capacity": t("256 IPv4 static routes"),
            "l2_features": t("MC-LAG; " + L2),
            "l3_features": t(L3),
            "stp_features": t(STP),
            "acl_security": t("512 IPv4 ACLs and 512 MAC ACLs; MAC/IP ACLs; device and network isolation; DHCP snooping and guarding"),
        },
    },
    "USW-Aggregation": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-aggregation",
        "values": {
            "vlan_count": n(1000, "Supported VLANs: 1,000"),
            "l2_features": t(L2),
            "stp_features": t(STP),
            "acl_security": t("128 IPv4 ACLs and 128 MAC ACLs; MAC/IP ACLs; device and network isolation; DHCP snooping and guarding"),
        },
    },
    "USW-Pro-Aggregation": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-pro-aggregation",
        "values": {
            "vlan_count": n(1000, "Supported VLANs: 1,000"),
            "routing_entry_capacity": t("256 IPv4 static routes"),
            "l2_features": t(L2),
            "l3_features": t(L3),
            "stp_features": t(STP),
            "acl_security": t("128 IPv4 ACLs and 128 MAC ACLs; MAC/IP ACLs; device and network isolation; DHCP snooping and guarding"),
        },
    },
    "USW-EnterpriseXG-24": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-enterprisexg-24",
        "values": {
            "vlan_count": n(1000, "Supported VLANs: 1,000"),
            "routing_entry_capacity": t("256 IPv4 static routes"),
            "l2_features": t(L2),
            "l3_features": t(L3),
            "stp_features": t(STP),
            "acl_security": t("128 IPv4 ACLs and 128 MAC ACLs; MAC/IP ACLs; device and network isolation; DHCP snooping and guarding"),
        },
    },
    "USW-Pro-XG-24": {
        "url": "https://techspecs.ui.com/unifi/switching/usw-pro-xg-24",
        "values": {
            "mac_address_table": t("32000 entries", "MAC address table size: 32,000"),
            "vlan_count": n(1000, "Supported VLANs: 1,000"),
            "routing_entry_capacity": t("512 IPv4 static routes"),
            "l2_features": t(L2),
            "l3_features": t(L3),
            "stp_features": t(STP),
            "acl_security": t("256 IPv4 ACLs and 256 MAC ACLs; MAC/IP ACLs; device and network isolation; DHCP snooping and guarding"),
        },
    },
}


class Command(BaseCommand):
    help = "Import verified current Ubiquiti aggregation and XG switch gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Missing brand: Ubiquiti")
        codes = {code for item in MODELS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for model, item in MODELS.items():
            documents[model], _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Official current UniFi Tech Specs page, accessed 2026-10-22",
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"Ubiquiti {model} Tech Specs",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Ubiquiti product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
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
                    "source_url": item["url"][:200],
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
                    model_new += 1
                elif old_value != new_value:
                    corrected += 1
                    model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=documents[model],
                    source_location=f"Official Tech Specs table - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={newly_filled} "
                f"corrected={corrected} unchanged={unchanged} models={len(MODELS)}"
            )
        )
        self.stdout.write("; ".join(per_model))
