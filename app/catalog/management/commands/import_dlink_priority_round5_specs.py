from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Supported" if value else "Not supported")


GO_SW = "https://support.dlink.com/resource/products/go-sw-5g/REVD/GO-SW-5G_REVD_DATASHEET_v4.00.pdf"
DES_105 = "https://legacyfiles.us.dlink.com/DES-105/REVC/DES-105_REVC2_DATASHEET_1.00_EN.PDF"
DES_1005P = "https://www.dlink.com/-/media/business_products/des/des-1005p/datasheet/des_1005p_b1_datasheet_en_eu.pdf"
DES_1008PA = "https://www.dlink.com/uk/en/-/media/business_products/des/des-1008pa/datasheet/des_1008pa_c1_datasheet_en.pdf"


UNMANAGED_NO_ADVANCED = {
    "port_isolation": b(False, "No port isolation function listed"),
    "loop_prevention": b(False, "No loop prevention function listed"),
    "vlan_support": t("Not supported (unmanaged model; no VLAN functions listed)"),
    "link_aggregation": t("Not supported"),
    "igmp_snooping": t("Not supported"),
    "port_mirroring": t("Not supported"),
    "cable_test": t("Not supported"),
}


PRODUCTS = {
    "GO-SW-5G": {
        "url": GO_SW,
        "title": "D-Link GO-SW-5G/8G Revision D Datasheet v4.00",
        "location": "Shared product features and technical specifications, pp. 1-2",
        "shared": True,
        "values": {
            **UNMANAGED_NO_ADVANCED,
            "fanless": b(True, "Fanless design"),
            "qos_support": t("Not supported"),
        },
    },
    "GO-SW-8G": {
        "url": GO_SW,
        "title": "D-Link GO-SW-5G/8G Revision D Datasheet v4.00",
        "location": "Shared product features and technical specifications, pp. 1-2",
        "shared": True,
        "values": {
            **UNMANAGED_NO_ADVANCED,
            "fanless": b(True, "Fanless design"),
            "qos_support": t("Not supported"),
        },
    },
    "DES-105": {
        "url": DES_105,
        "title": "D-Link DES-105 Revision C2 Datasheet v1.00",
        "location": "Product features and technical specifications, pp. 1-2",
        "values": {
            **UNMANAGED_NO_ADVANCED,
            "installation": t("Desktop; plug-and-play"),
            "max_power_consumption_w": n(2.17, "2.17 W maximum AC input power"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DES-1005P": {
        "url": DES_1005P,
        "title": "D-Link DES-1005P Revision B1 Datasheet",
        "location": "Product features and technical specifications, pp. 1-2",
        "values": {
            **UNMANAGED_NO_ADVANCED,
            "extend_mode": b(False, "No extend mode listed for revision B1"),
            "poe_auto_recovery": b(False, "No PoE auto-recovery function listed for revision B1"),
            "qos_support": t("IEEE 802.1p QoS with 4 queues"),
        },
    },
    "DES-1008PA": {
        "url": DES_1008PA,
        "title": "D-Link DES-1008PA Revision C1 Datasheet",
        "location": "Product features and technical specifications, pp. 1-2",
        "values": {
            **UNMANAGED_NO_ADVANCED,
            "extend_mode": b(False, "No extend mode listed for revision C1"),
            "poe_auto_recovery": b(False, "No PoE auto-recovery function listed for revision C1"),
            "qos_support": t("Not supported"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link unmanaged and PoE desktop-switch specifications (round 5)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
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
                raise CommandError(f"Missing published D-Link product: {model}")
            source, _ = SourceDocument.objects.update_or_create(
                url=row["url"],
                document_version="Current exact-model document accessed 2026-10-14",
                defaults={
                    "brand": brand,
                    "product": None if row.get("shared") else product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": row["title"],
                    "region": "Global/official regional support",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(old and old.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((old.value_text or "").strip()) or old.value_number is not None or old.value_boolean is not None
                ))
                if not had:
                    old_value = None
                elif old.value_text:
                    old_value = old.value_text
                elif old.value_number is not None:
                    old_value = old.value_number
                else:
                    old_value = old.value_boolean
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": raw,
                    "source_url": row["url"][:200],
                    "source_note": (
                        "Manually verified from the exact model/revision official datasheet. "
                        "Unsupported unmanaged functions were recorded only after checking the exhaustive feature table."
                    ),
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
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
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
                    source_location=f"{row['location']} - {model}",
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
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
