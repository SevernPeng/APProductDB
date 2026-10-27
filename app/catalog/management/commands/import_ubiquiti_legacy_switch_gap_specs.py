from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


COMMON_L2 = (
    "VLAN; port mirroring; LACP port aggregation; 802.3x flow control; storm control; "
    "port isolation; 802.1X/RADIUS dynamic VLAN"
)
COMMON_STP = "RSTP and Spanning Tree Protocol"
COMMON_ACL = "802.1X (RADIUS) authentication; dynamic VLAN; port isolation"


SOURCES = {
    "switch8": {
        "url": "https://dl.ui.com/datasheets/unifi/UniFi_Switch_8_DS.pdf",
        "version": "Official UniFi Switch 8 datasheet, 2020 edition",
        "title": "Ubiquiti UniFi Switch 8 Datasheet",
    },
    "poe": {
        "url": "https://dl.ui.com/datasheets/unifi/UniFi_PoE_Switch.pdf",
        "version": "Official UniFi PoE Switch datasheet, 2018 edition",
        "title": "Ubiquiti UniFi PoE Switch Datasheet",
    },
    "xg": {
        "url": "https://dl.ui.com/datasheets/unifi/UniFi_Switch_US-16-XG_DS.pdf",
        "version": "Official US-16-XG datasheet, 2020 edition",
        "title": "Ubiquiti UniFi Switch US-16-XG Datasheet",
    },
}


PRODUCTS = {
    "US-8": {
        "source": "switch8",
        "values": {
            "switching_capacity_gbps": n(16),
            "packet_forwarding_rate_mpps": n(11.9),
            "max_power_consumption_w": n(12, "12 W excluding PoE output"),
            "power_supply": t("External AC/DC adapter: 100-240 V AC, 50/60 Hz; 48 V DC, 0.5 A; or 802.3af/at PoE input"),
            "management_methods": t("UniFi Controller; Ethernet in-band management; debug terminal/CLI"),
            "operating_temperature_c": t("-5 to 45 °C"),
            "fan_design": t("Fanless, 0.7 dBr above 27.5 dBA background"),
            "jumbo_frame_bytes": n(9216, "9216-byte jumbo frame support"),
            "l2_features": t(COMMON_L2),
            "stp_features": t(COMMON_STP),
            "acl_security": t(COMMON_ACL),
        },
    },
    "US-8-60W": {
        "source": "switch8",
        "values": {
            "switching_capacity_gbps": n(16),
            "packet_forwarding_rate_mpps": n(11.9),
            "max_power_consumption_w": n(12, "12 W excluding PoE output"),
            "power_supply": t("External AC/DC adapter: 100-240 V AC, 50/60 Hz; 48 V DC, 1.25 A"),
            "management_methods": t("UniFi Controller; Ethernet in-band management; debug terminal/CLI"),
            "operating_temperature_c": t("-5 to 45 °C"),
            "fan_design": t("Fanless, 0.6 dBr above 27.5 dBA background"),
            "poe_ports": n(4),
            "poe_standard": t("IEEE 802.3af"),
            "max_poe_per_port_w": n(15.4),
            "jumbo_frame_bytes": n(9216, "9216-byte jumbo frame support"),
            "l2_features": t(COMMON_L2),
            "stp_features": t(COMMON_STP),
            "acl_security": t(COMMON_ACL),
        },
    },
    "US-8-150W": {
        "source": "poe",
        "values": {
            "poe_ports": n(8),
            "poe_standard": t("IEEE 802.3af/at PoE+; 24 V passive PoE"),
            "max_poe_per_port_w": n(34.2, "Maximum PoE+ wattage per port by PSE: 34.2 W"),
            "power_supply": t("Internal AC/DC, 150 W DC; 100-240 V AC, 50/60 Hz"),
            "vlan_count": n(255),
            "jumbo_frame_bytes": n(9216, "9216-byte jumbo frame support"),
            "l2_features": t(COMMON_L2),
            "stp_features": t(COMMON_STP),
            "acl_security": t(COMMON_ACL),
        },
    },
    "US-24-500W": {
        "source": "poe",
        "values": {
            "poe_ports": n(24),
            "poe_standard": t("IEEE 802.3af/at PoE+; 24 V passive PoE"),
            "max_poe_per_port_w": n(34.2, "Maximum PoE+ wattage per port by PSE: 34.2 W"),
            "power_supply": t("Internal AC/DC, 500 W DC; 100-240 V AC, 50/60 Hz"),
            "vlan_count": n(255),
            "jumbo_frame_bytes": n(9216, "9216-byte jumbo frame support"),
            "l2_features": t(COMMON_L2),
            "stp_features": t(COMMON_STP),
            "acl_security": t(COMMON_ACL),
            "fan_design": t("Variable-speed active cooling; 9.3-21.6 dBr above 27.5 dBA background"),
        },
    },
    "US-48-500W": {
        "source": "poe",
        "values": {
            "switching_capacity_gbps": n(140),
            "packet_forwarding_rate_mpps": n(104.16),
            "mac_address_table": t("16K entries", "16384 MAC addresses"),
            "max_power_consumption_w": n(500, "500 W including PoE output; 64 W excluding PoE output"),
            "poe_ports": n(48),
            "poe_standard": t("IEEE 802.3af/at PoE+; 24 V passive PoE"),
            "max_poe_per_port_w": n(34.2, "Maximum PoE+ wattage per port by PSE: 34.2 W"),
            "power_supply": t("Internal AC/DC, 500 W DC; 100-240 V AC, 50/60 Hz"),
            "vlan_count": n(255),
            "jumbo_frame_bytes": n(9216, "9216-byte jumbo frame support"),
            "l2_features": t(COMMON_L2),
            "stp_features": t(COMMON_STP),
            "acl_security": t(COMMON_ACL),
            "fan_design": t("Variable-speed active cooling; 10.7-23.6 dBr above 27.5 dBA background"),
        },
    },
    "US-16-XG": {
        "source": "xg",
        "values": {
            "switching_capacity_gbps": n(320),
            "packet_forwarding_rate_mpps": n(238.10),
            "max_power_consumption_w": n(36, "36 W excluding SFP/SFP+ modules"),
            "power_supply": t("Internal AC/DC 56 W; 100-240 V AC, or 20-57 V DC terminal input"),
            "management_methods": t("UniFi Controller; RJ45 serial out-of-band; Ethernet in-band; debug terminal/CLI"),
            "operating_temperature_c": t("-5 to 40 °C"),
            "dimensions_mm": t("443 x 221 x 43 mm"),
            "l2_features": t(COMMON_L2),
            "stp_features": t("Spanning Tree configuration"),
            "acl_security": t(COMMON_ACL),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified legacy Ubiquiti UniFi switch gap specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Missing brand: Ubiquiti")

        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        for key, source in SOURCES.items():
            documents[key], _ = SourceDocument.objects.update_or_create(
                url=source["url"],
                document_version=source["version"],
                defaults={
                    "brand": brand,
                    "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": source["title"],
                    "region": "Global",
                    "published_date": None,
                    "accessed_date": accessed,
                    "active": True,
                },
            )

        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Ubiquiti product: {model}")
            source = SOURCES[item["source"]]
            document = documents[item["source"]]
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
                    "source_url": source["url"][:200],
                    "source_note": "Manually verified from Ubiquiti's official exact-model datasheet.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                    new_value = Decimal(str(value))
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
