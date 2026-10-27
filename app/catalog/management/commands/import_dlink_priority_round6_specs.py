from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def t(value):
    return "text", value, str(value)


def n(value, raw=None):
    return "number", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Supported" if value else "Not supported")


DES_1024D = "https://www.dlink.com/en/products/des-1024d-24-port-10-100mbps-desktop-switch"
DES_F1006P = "https://www2.dlink.com/in/en/-/media/business_products/des/des-f1006p-e/datasheet/desf1006pe.pdf"
DSS_100E_18P = "https://www.dlink.com/en/products/dss-100e-18p-18-port-10-100base-tx-poe-unmanaged-surveillance-switch"


NO_MANAGEMENT = {
    "igmp_snooping": t("Not supported"),
    "link_aggregation": t("Not supported"),
    "port_mirroring": t("Not supported"),
    "cable_test": t("Not supported"),
}


PRODUCTS = {
    "DES-1024D": {
        "url": DES_1024D,
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "D-Link DES-1024D current official product page",
        "location": "Current live-product specification and feature sections",
        "values": {
            **NO_MANAGEMENT,
            "port_isolation": b(False, "No isolation mode listed for current unmanaged model"),
            "loop_prevention": b(False, "No loop prevention function listed"),
            "qos_support": t("IEEE 802.1p QoS with 4 queues per port"),
            "vlan_support": t("Not supported (unmanaged model; no VLAN functions listed)"),
        },
    },
    "DES-F1006P-E": {
        "url": DES_F1006P,
        "type": SourceDocument.DocumentType.DATASHEET,
        "title": "D-Link DES-F1006P-E official datasheet",
        "location": "Working modes and technical specifications, pp. 1-2",
        "values": {
            **NO_MANAGEMENT,
            "installation": t("Desktop; plug-and-play"),
            "port_isolation": b(True, "VLAN mode isolates PoE ports 1-4 from each other"),
            "qos_support": t("QoS mode with customizable application priority"),
            "vlan_support": t("VLAN mode: ports 1-4 isolated from each other"),
        },
    },
    "DSS-100E-18P": {
        "url": DSS_100E_18P,
        "type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "D-Link DSS-100E-18P current official product page",
        "location": "Current live-product feature, mode, and specification sections",
        "values": {
            "igmp_snooping": t("Not supported"),
            "loop_prevention": b(False, "No loop prevention function listed"),
            "poe_auto_recovery": b(False, "No PoE auto-recovery function listed"),
            "poe_ports": n(16, "16 x 10/100BASE-T PoE ports"),
            "port_isolation": b(True, "Isolation mode separates ports 1-16; uplink only to ports 17-18"),
            "qos_support": t("Port priority on ports 1-8 in standard mode"),
            "installation": t("Desktop or rackmount; plug-and-play"),
            "dimensions_mm": t("440 x 178 x 44 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link unmanaged surveillance-switch specifications (round 6)."

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
                document_version="Current exact-model source accessed 2026-10-14",
                defaults={
                    "brand": brand,
                    "product": product,
                    "document_type": row["type"],
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
                        "Manually verified from the exact model official source. Unsupported unmanaged functions "
                        "were recorded only after checking the complete published feature list."
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
