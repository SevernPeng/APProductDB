from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


PAGE_URL = (
    "https://www.h3c.com/en/Products_and_Solutions/SMB_Products/Products/"
    "SMB_Cloudnet/Switches/S5120/H3C_S5120V3-LI/"
)
HARDWARE_URL = "https://www.h3c.com/en/D_202306/1867326_294551_0.htm"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or str(value)


PRODUCTS = {
    # The catalog's legacy model string omits the final "I"; H3C's current
    # official page and hardware guide identify the product as ...-LI.
    "S5120V3-28S-HPWR-L": {
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n("95.232"),
        "dimensions_mm": t("440 x 260 x 43.6 mm (W x D x H)"),
        "max_power_consumption_w": n(445, "Maximum AC power including 370 W PoE output: 445 W"),
        "operating_temperature_c": t(
            "-5 to 50 °C normally; -5 to 45 °C with optics under 80 km; "
            "-5 to 40 °C with optics of 80 km or longer"
        ),
        "poe_standard": t("IEEE 802.3af/802.3at (PoE+)"),
        "poe_ports": n(24, "24 ports at 15.4 W, or 12 ports at 30 W, within the total budget"),
        "poe_budget_w": n(370),
        "max_poe_per_port_w": n(30),
        "jumbo_frame_bytes": n(10000),
        "vlan_count": n(4094),
        "ip_interface_capacity": t("32 VLAN interfaces"),
        "routing_entry_capacity": t("1,024 IPv4 routes; 240 IPv6 unicast routes"),
        "l2_features": t(
            "Static/dynamic/cross-device link aggregation; LACP; port/MAC/protocol-based VLAN; "
            "QinQ/selective QinQ; VLAN mapping; Voice VLAN; MVRP; Smart Link; RRPP; ERPS"
        ),
        "stp_features": t("STP; RSTP; MSTP; PVST/PVST+; STP root protection"),
        "acl_security": t(
            "Layer 2-4, time-range, VLAN and bidirectional ACLs; AAA/RADIUS/HWTACACS; "
            "802.1X and MAC authentication; port security/isolation; IP Source Guard; SSH 2.0; HTTPS"
        ),
        "l3_features": t("IPv4/IPv6 static routing; RIPv1/v2 and RIPng; OSPFv1/v2/v3"),
        "ospf_support": b(True, "OSPFv1/v2/v3 supported"),
        "rip_support": b(True, "RIPv1/v2 and RIPng supported"),
        "multicast_routing": b(
            False,
            "Official capability table lists IGMP/PIM/MLD snooping and multicast VLAN, not multicast routing",
        ),
        "management_methods": t(
            "CLI; console; Telnet; SSH 2.0; SNMP v1/v2c/v3; web NMS; H3C IMC; "
            "RESTful; RMON; FTP/TFTP; zero-touch provisioning"
        ),
        "stacking": t("H3C IRF2 over standard Ethernet interfaces; local or remote stacking"),
        "stacking_units": n(9),
        "stacking_bandwidth_gbps": n(80),
    },
    "S5120V3-28F-LI": {
        "multicast_routing": b(False, "Official capability table lists snooping only, not multicast routing"),
    },
    "S5120V3-28S-LI": {
        "multicast_routing": b(False, "Official capability table lists snooping only, not multicast routing"),
    },
    "S5120V3-52S-LI": {
        "multicast_routing": b(False, "Official capability table lists snooping only, not multicast routing"),
    },
    "S5120V3-52S-PWR-LI": {
        "multicast_routing": b(False, "Official capability table lists snooping only, not multicast routing"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified H3C S5120V3-LI specifications."
    document_version = "Current official product page and hardware specification 6W101; accessed 2026-10-20"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="H3C").first()
        if not brand:
            raise CommandError("Missing brand: H3C")
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        documents = {}
        for url, dtype, title in (
            (PAGE_URL, SourceDocument.DocumentType.PRODUCT_PAGE, "H3C S5120V3-LI Layer 3 Gigabit Access Switch Series"),
            (HARDWARE_URL, SourceDocument.DocumentType.DATASHEET, "H3C S5120V3-LI Hardware Information and Specifications 6W101"),
        ):
            documents[url], _ = SourceDocument.objects.update_or_create(
                url=url, document_version=self.document_version,
                defaults={
                    "brand": brand, "product": None, "document_type": dtype,
                    "title": title, "region": "Global", "published_date": None,
                    "accessed_date": accessed, "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing H3C product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in values.items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or
                    existing.value_boolean is not None
                ))
                old_status = existing.value_status if existing else None
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else (
                        existing.value_number if existing.value_number is not None else existing.value_boolean
                    )
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit,
                    "raw_value": raw, "source_url": PAGE_URL[:200],
                    "source_note": (
                        "Manually verified from H3C's current S5120V3-LI product page and latest available "
                        "hardware specification. Catalog model S5120V3-28S-HPWR-L maps to the official "
                        "S5120V3-28S-HPWR-LI designation."
                    ),
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=documents[PAGE_URL],
                    source_location=f"Hardware/software/performance specification tables - {model} - {code}",
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
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
