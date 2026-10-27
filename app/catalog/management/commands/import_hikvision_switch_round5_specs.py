from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


PRODUCTS = {
    "DS-3E1505P-EI": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000085149/DS-3E1505P-EI_Datasheet_20231023.pdf",
        "version": "2023-10-23",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1506P-EI": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000112292/DS-3E1506P-EI_Datasheet_20231023.pdf",
        "version": "2023-10-23",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1508-EI": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000034945/DS-3E1508-EI_Datasheet_20240425.pdf",
        "version": "2024-04-25",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1510P-EI": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000068/S000005201/OFR011812/M000034948/Data_Sheet/DS-3E1510P-EI-V2_Datasheet_20231023.pdf",
        "version": "V2 2023-10-23",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1518P-EI/M": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000068/S000005201/OFR013776/M000081862/Data_Sheet/DS-3E1518P-EI_M_Datasheet_20240428.pdf",
        "version": "2024-04-28",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1518P-SI": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000043338/DS-3E1518P-SI_Datasheet_20240425.pdf",
        "version": "2024-04-25",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1524-EI": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000034943/DS-3E1524-EI_Datasheet_20240425.pdf",
        "version": "2024-04-25",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1526P-EI/M": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000081863/DS-3E1526P-EI_M_Datasheet_20240428.pdf",
        "version": "2024-04-28",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3E1526P-SI": {
        "url": "https://www.hikvision.com/content/dam/hikvision/usa/data-sheet/manually-upload/switch/DS-3E1526P-SI_Datasheet_20240514_Updated.pdf",
        "version": "2024-05-14 updated",
        "values": {"acl_security": t("Port isolation")},
    },
    "DS-3T1506HP-SI-4P2F": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000163902/DS-3T1506HP-SI-4P2F_Datasheet_20260518.pdf",
        "version": "2026-05-18",
        "values": {
            "management_methods": t("Web; Hik-Central Pro; Hik-Partner Pro; SNMP v1/v2c; DHCP client; Super IP"),
            "vlan_count": n(4094, "Supports a maximum of 4094 VLANs"),
            "acl_security": t("Port security; up to 64 ACL entries and 128 total ACL rules; DHCP snooping; IPSG binding"),
        },
    },
    "DS-3E0505P-E/M": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000007570/DS-3E0505P-E_M_Datasheet_20240307.pdf",
        "version": "2024-03-07",
        "values": {
            "flow_control": t("IEEE 802.3x flow control", "IEEE 802.3x"),
            "fanless": b(True, "Reliable fan-free design"),
        },
    },
    "DS-3E0505P-E/M(B)": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000159393/DS-3E0505P-E_MB_Datasheet_20241101.pdf",
        "version": "2024-11-01",
        "values": {"fanless": b(True, "Silent running with fanless design")},
    },
    "DS-3E0510P-E": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000008119/DS-3E0510P-E_Datasheet_20240308.pdf",
        "version": "2024-03-08",
        "values": {"fanless": b(True, "Metal material, fan-free design")},
    },
    "DS-3E0526P-E/M": {
        "url": "https://www.hikvision.com/content/dam/hikvision/pt-br/data-sheets/DS-3E0526P-EM-24-Port-Gigabit-Unmanaged-PoE-Switch.pdf",
        "version": "Official exact-model datasheet",
        "values": {"fanless": b(False, "Metal material with a fan equipped")},
    },
    "DS-3E0520HP-E": {
        "url": "https://www.hikvision.com/content/dam/hikvision/usa/data-sheet/manually-upload/switch/DS-3E0520HP-E_Datasheet_20240308_Updated.pdf",
        "version": "2024-03-08 updated",
        "values": {"installation": t("Rack, mounting ears included")},
    },
    "DS-3E0106P-E/M": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000068/S000000069/OFR000087/M000019321/Data_Sheet/DS-3E0106P-E_M_Datasheet_20240307.pdf",
        "version": "2024-03-07",
        "values": {
            "flow_control": t("IEEE 802.3x flow control", "IEEE 802.3x"),
            "fanless": b(True, "Reliable fan-free design"),
        },
    },
    "DS-3WF02C-5N/O": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000061/S000000056/OFR000075/M000011104/Data_Sheet/Datasheet-of-DS-3WF02C-5NO-Outdoor-Wireless-Bridge-Datasheet.pdf",
        "version": "Official exact-model datasheet",
        "values": {
            "wireless_range": t("Up to 5 km"),
            "bridge_modes": t("Point-to-point; point-to-multipoint"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Hikvision switch specifications (round 5)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Hikvision").first()
        if not brand:
            raise CommandError("Missing brand: Hikvision")

        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Hikvision product: {model}")

            document, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version=item["version"],
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"Hikvision {model} official datasheet",
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

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
                    old_value = (
                        existing.value_text
                        if existing.value_text
                        else existing.value_number
                        if existing.value_number is not None
                        else existing.value_boolean
                    )

                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from Hikvision's official exact-model datasheet; newer version preferred where available.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value)
                    new_value = bool(value)
                else:
                    defaults["value_text"] = str(value)
                    new_value = str(value)

                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
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
                    source_document=document,
                    source_location=f"Official datasheet specification table - {model} - {code}",
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
                f"corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(per_model))
