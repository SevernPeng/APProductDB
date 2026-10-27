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


URL = "https://vipplus.dlink.com/en/-/media/business_products/dgs/dgs-3000/datasheet/dgs3000seriesdatasheetv400ww.pdf"

COMMON = {
    "power_supply": t("100 to 240 V AC, 50/60 Hz; redundant power supply supported"),
    "management_methods": t("Web GUI, CLI, Telnet, SNMP v1/v2c/v3, RMON, SSL, SSH, console, TFTP and FTP"),
    "poe_standard": t("Not supported (non-PoE model)"),
    "jumbo_frame_bytes": n(9216),
    "vlan_count": n(4094),
    "l2_features": t("802.3x flow control, HOL blocking prevention, 802.1AX/802.3ad link aggregation, port mirroring, ERPS, L2PT, Flex Link, IGMP/MLD snooping, Q-in-Q, GVRP, Voice VLAN and Private VLAN"),
    "stp_features": t("IEEE 802.1D STP, IEEE 802.1w RSTP and IEEE 802.1s MSTP; BPDU filtering and root restriction"),
    "acl_security": t("Up to 1,024 ingress ACL rules, 802.1X, MAC/Web access control, RADIUS/TACACS+, IP-MAC-Port binding, DHCP snooping, ARP inspection, storm control and DoS prevention"),
    "l3_features": t("Static IPv4/IPv6 routing, default route, ARP and IPv6 Neighbor Discovery"),
    "routing_entry_capacity": t("16 IPv4 static routes and 16 IPv6 static routes"),
    "ospf_support": b(False, "No OSPF support listed; Layer-2 model with static routing only"),
    "rip_support": b(False, "No RIP support listed; Layer-2 model with static routing only"),
    "pbr_support": b(False, "No policy-based routing support listed; Layer-2 model with static routing only"),
    "vrrp_support": b(False, "No VRRP support listed; Layer-2 model with static routing only"),
    "multicast_routing": b(False, "IGMP/MLD snooping supported; no multicast routing listed"),
    "stacking": t("D-Link Single IP Management (SIM) virtual stacking"),
    "stacking_units": n(32),
    "operating_temperature_c": t("-5 to 50 °C"),
}

PRODUCTS = {
    "DGS-3000-28X": {
        **COMMON,
        "ethernet_interfaces": t("24 x 10/100/1000 Mbps RJ45; 4 x 10G SFP+"),
        "switching_capacity_gbps": n(128),
        "packet_forwarding_rate_mpps": n(95.24),
        "mac_address_table": t("16K entries"),
        "packet_buffer_mb": n(1.5),
        "fan_design": t("1 x Smart Fan"),
        "fanless": b(False, "1 x Smart Fan"),
        "max_power_consumption_w": n(22.1),
        "dimensions_mm": t("440 x 210 x 44 mm"),
    },
    "DGS-3000-52X": {
        **COMMON,
        "ethernet_interfaces": t("48 x 10/100/1000 Mbps RJ45; 4 x 10G SFP+"),
        "switching_capacity_gbps": n(176),
        "packet_forwarding_rate_mpps": n(130.95),
        "mac_address_table": t("16K entries"),
        "packet_buffer_mb": n(3),
        "fan_design": t("2 x Smart Fan"),
        "fanless": b(False, "2 x Smart Fan"),
        "max_power_consumption_w": n(40.7),
        "dimensions_mm": t("440 x 210 x 44 mm"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified D-Link DGS-3000-28X/52X specifications (round 3)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="D-Link").first()
        if not brand:
            raise CommandError("Missing brand: D-Link")
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=URL,
            document_version="DGS-3000 Series Datasheet v4.00 WW, accessed 2026-10-14",
            defaults={
                "brand": brand,
                "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "D-Link DGS-3000 Series Datasheet v4.00 WW",
                "region": "Worldwide",
                "published_date": None,
                "accessed_date": accessed,
                "active": True,
            },
        )
        written = new = corrected = unchanged = 0
        details = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing published D-Link product: {model}")
            model_new = model_corrected = 0
            for code, (kind, value, raw) in values.items():
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
                    "source_url": URL[:200],
                    "source_note": "Manually verified against the exact model column and all-model software tables in the official v4.00 datasheet.",
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
                    source_location=f"Hardware tables pp. 5-6 and software tables pp. 7-9 - {model}",
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
            f"{mode}: spec_values={written} newly_filled={new} corrected={corrected} "
            f"unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(details))
