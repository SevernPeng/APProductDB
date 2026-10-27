from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = (
    "https://www.h3c.com/en/Products_and_Solutions/SMB_Products/Products/SMB_Cloudnet/"
    "Switches/S5120/H3C_S5120V3-LI/"
)


def n(value):
    return "number", value


def t(value):
    return "text", value


COMMON = {
    "jumbo_frame_bytes": n(10000),
    "management_methods": t(
        "CLI; console; Telnet; SSH 2.0; SNMP v1/v2c/v3; web NMS; H3C IMC; "
        "RESTful; RMON; FTP/TFTP/XModem; Zero Touch Provisioning"
    ),
    "vlan_count": n(4094),
    "l2_features": t(
        "Static/dynamic/cross-device link aggregation; port/MAC/protocol-based VLAN; "
        "QinQ/selective QinQ; VLAN mapping; Voice VLAN; MVRP; Smart Link; RRPP; "
        "G.8032 ERPS; IGMP/PIM/MLD snooping; sFlow"
    ),
    "stp_features": t("STP; RSTP; MSTP; PVST/PVST+; STP root protection"),
    "l3_features": t("Static routing; RIPv1/v2; RIPng; OSPFv1/v2/v3"),
    "routing_entry_capacity": t("1024 IPv4 routes; 240 IPv6 unicast routes"),
    "stacking": t(
        "H3C IRF2 through standard Ethernet interfaces; local and remote stacking; up to 9 members"
    ),
}


MODELS = {
    "S5120V3-28S-LI": {
        **COMMON,
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n("95.232"),
        "max_power_consumption_w": n(24),
        "dimensions_mm": t("440 x 160 x 43.6 mm (W x D x H)"),
        "operating_temperature_c": t(
            "-5 to 50 °C normally; -5 to 45 °C with optics under 80 km; "
            "-5 to 40 °C with optics of 80 km or longer"
        ),
    },
    "S5120V3-52S-LI": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n("130.952"),
        "max_power_consumption_w": n(44),
        "dimensions_mm": t("440 x 230 x 43.6 mm (W x D x H)"),
        "operating_temperature_c": t(
            "-5 to 50 °C normally; -5 to 45 °C with optics under 80 km; "
            "-5 to 40 °C with optics of 80 km or longer"
        ),
    },
    "S5120V3-52S-PWR-LI": {
        **COMMON,
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n("130.952"),
        "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
        "poe_ports": n(48),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "max_power_consumption_w": n(467),
        "dimensions_mm": t("440 x 400 x 43.6 mm (W x D x H)"),
        "operating_temperature_c": t(
            "-5 to 50 °C normally; -5 to 45 °C with optics under 80 km; "
            "-5 to 40 °C with optics of 80 km or longer"
        ),
    },
    "S5120V3-28F-LI": COMMON,
}


class Command(BaseCommand):
    help = "Import manually verified H3C S5120V3-LI series specifications."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="H3C").first()
        if not brand:
            raise CommandError("Brand 'H3C' was not found.")
        codes = {code for values in MODELS.values() for code in values}
        definitions = {item.code: item for item in SpecDefinition.objects.filter(code__in=codes)}
        if codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(codes - definitions.keys()))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL,
            document_version="Current official product page accessed 2026-10-12",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                "title": "H3C S5120V3-LI Layer 3 Gigabit Access Switch Series",
                "region": "Global",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        updated = 0
        newly_filled = 0
        missing_models = []
        for model, values in MODELS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                missing_models.append(model)
                continue
            for code, (kind, value) in values.items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had_value = bool(
                    existing
                    and existing.value_status == ProductSpec.ValueStatus.PUBLISHED
                    and (
                        bool((existing.value_text or "").strip())
                        or existing.value_number is not None
                        or existing.value_boolean is not None
                    )
                )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": str(value),
                    "unit": definition.unit,
                    "raw_value": str(value),
                    "source_url": SOURCE_URL,
                    "source_note": (
                        "Manually verified from H3C's current official S5120V3-LI product page. "
                        "Only exact-model table values and explicitly series-wide features are recorded."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value))
                else:
                    defaults["value_text"] = str(value)
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product,
                    definition=definition,
                    defaults=defaults,
                )
                newly_filled += int(not had_value)
                SpecEvidence.objects.update_or_create(
                    product_spec=spec,
                    source_document=source,
                    source_location=f"Hardware, software, and performance specification tables - {model}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {value}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                updated += 1

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: spec_values={updated} newly_filled={newly_filled} "
                f"models={len(MODELS) - len(missing_models)}"
            )
        )
        if missing_models:
            self.stdout.write(f"Missing models: {', '.join(missing_models)}")
