from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value):
    return "text", value, str(value)


def b(value=True, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


DGS_F1006_URL = "https://www.dlink.com/in/en/-/media/business_products/dgs/dgs-f1006pe/datasheet/dgs-f1006p-e.pdf"
DGS_F1010_URL = "https://www2.dlink.com/in/en/-/media/business_products/dgs/dgs-f1010p-e/datasheet/dgsf1010pe.pdf"
DES_F1026_URL = "https://www.dlink.com.sg/products/des-f1026p-e-250m-24-port-fast-ethernet-poe-switch-with-24-port-poe-250w-with-2-x-gigabit-uplink-ports-with-1-combo-sfp-des-f1026p-e"
DSS_200G_URL = "https://www.dlink.com/uk/en/-/media/business_products/dss/200g/dss_200g_eu_reva1_datasheet_eu_en.pdf"


F_COMMON = {
    "flow_control": t("IEEE 802.3x flow control"),
    "extend_mode": b(True, "DIP-switch Extend mode supported"),
    "poe_auto_recovery": b(True, "Automatic PoE port power detection, power-off, and restart"),
    "port_isolation": b(True, "DIP-switch VLAN mode isolates downlink PoE ports"),
    "qos_support": t("DIP-switch video traffic priority mode"),
    "installation": t("Desktop; mounting kit supported"),
    "operating_temperature_c": t("0 to 40 °C"),
}

DSS_COMMON = {
    "mac_address_table": t("8K entries"),
    "jumbo_frame_bytes": n(10240),
    "power_supply": t("Internal universal 100-240 V AC, 50/60 Hz power supply"),
    "management_methods": t("Web-based GUI for IPv4/IPv6 and SNMP"),
    "poe_standard": t("IEEE 802.3af/at PoE/PoE+"),
    "max_poe_per_port_w": n(30),
    "vlan_count": n(128, "128 static VLAN groups; maximum 4094 VIDs"),
    "l2_features": t(
        "Port-based and IEEE 802.1Q VLAN, Auto Surveillance VLAN, Voice VLAN, flow control, "
        "10,240-byte jumbo frames, IGMP snooping, IEEE 802.3ad link aggregation, ERPS, "
        "loopback detection, LLDP, port mirroring, and cable diagnostics"
    ),
    "stp_features": t("IEEE 802.1D STP and IEEE 802.1w RSTP"),
    "acl_security": t(
        "D-Link Safeguard, traffic segmentation, broadcast/multicast/unknown-unicast storm "
        "control, DoS attack prevention, and SSL"
    ),
    "operating_temperature_c": t("-5 to 50 °C"),
}

PRODUCTS = {
    "DGS-F1006P-E": {
        "url": DGS_F1006_URL,
        "document_type": SourceDocument.DocumentType.DATASHEET,
        "title": "D-Link DGS-F1006P-E Datasheet",
        "location": "Product highlights and specifications, pp. 1-3",
        "values": {
            **F_COMMON,
            "vlan_support": t("DIP-switch port-isolation VLAN for ports 1-4"),
            "max_power_consumption_w": n(60, "Power: 60 W"),
            "dimensions_mm": t("135 x 75 x 27 mm"),
        },
    },
    "DGS-F1010P-E": {
        "url": DGS_F1010_URL,
        "document_type": SourceDocument.DocumentType.DATASHEET,
        "title": "D-Link DGS-F1010P-E Datasheet",
        "location": "Product highlights and specifications, pp. 1-3",
        "values": {
            **F_COMMON,
            "vlan_support": t("DIP-switch port-isolation VLAN for ports 1-8"),
            "max_power_consumption_w": n(120, "Power: 120 W"),
            "dimensions_mm": t("184 x 94 x 27 mm"),
        },
    },
    "DES-F1026P-E": {
        "url": DES_F1026_URL,
        "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
        "title": "D-Link DES-F1026P-E Product Page",
        "location": "Features and technical specifications",
        "values": {
            "flow_control": t("IEEE 802.3x flow control"),
            "extend_mode": b(True, "Extend mode supports up to 250 m on ports 1-8"),
            "port_isolation": b(True, "VLAN mode isolates downlink ports"),
            "qos_support": t("Video QoS priority mode"),
            "vlan_support": t("DIP-switch port-isolation VLAN"),
            "installation": t("Desktop; mounting kit supported"),
            "max_power_consumption_w": n(250, "External power adapter: 250 W"),
            "dimensions_mm": t("440 x 180 x 44 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DSS-200G-10MP": {
        "url": DSS_200G_URL,
        "document_type": SourceDocument.DocumentType.DATASHEET,
        "title": "D-Link DSS-200G Series Datasheet",
        "location": "Technical specifications, DSS-200G-10MP column, pp. 4-6",
        "values": {
            **DSS_COMMON,
            "fan_design": t("Fanless"),
            "poe_ports": n(8),
            "poe_budget_w": n(130),
            "max_power_consumption_w": n(160.2, "160.2 W with PoE on"),
            "dimensions_mm": t("280 x 180 x 44 mm"),
        },
    },
    "DSS-200G-28MP": {
        "url": DSS_200G_URL,
        "document_type": SourceDocument.DocumentType.DATASHEET,
        "title": "D-Link DSS-200G Series Datasheet",
        "location": "Technical specifications, DSS-200G-28MP column, pp. 4-6",
        "values": {
            **DSS_COMMON,
            "fan_design": t("2 fans"),
            "poe_ports": n(24),
            "poe_budget_w": n(370),
            "max_power_consumption_w": n(425.9, "425.9 W with PoE on"),
            "dimensions_mm": t("440 x 208 x 44 mm"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link F-series and DSS-200G specifications (round 1)."

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
                document_version="Current official document accessed 2026-10-14",
                defaults={
                    "brand": brand,
                    "product": product if model.startswith(("DGS-F", "DES-F")) else None,
                    "document_type": row["document_type"],
                    "title": row["title"],
                    "region": "Global/official regional site",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in row["values"].items():
                definition = definitions[code]
                old = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(
                    old
                    and old.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((old.value_text or "").strip())
                        or old.value_number is not None
                        or old.value_boolean is not None
                    )
                )
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
                        "Manually verified from the official exact-model page or datasheet; "
                        "model columns and continuation tables were visually checked."
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
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
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
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
                f"unchanged={unchanged} models={len(PRODUCTS)}"
            )
        )
        self.stdout.write("; ".join(details))
