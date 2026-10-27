from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCE_URL = "https://www.downloads.netgear.com/files/GDC/datasheet/en/M4100.pdf"


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def na(raw="Not applicable"):
    return "not_applicable", None, raw


COMMON = {
    "ethernet_interfaces": t("26 x 10/100/1000BASE-T RJ45; 4 x 100/1000BASE-X SFP shared with copper ports"),
    "uplink_interfaces": t("4 x shared 100/1000BASE-X SFP; any port can be used as an uplink"),
    "console_interfaces": t("1 x serial RS-232 DB9 and 1 x Mini-USB console port (selectable)"),
    "switch_usb_interfaces": t("1 x USB storage port for firmware and configuration files"),
    "cpu": t("Broadcom BCM53003, 600 MHz"),
    "dram_memory": t("128 MB RAM"),
    "flash_memory": t("32 MB flash; dual firmware images and dual configuration files"),
    "switching_capacity_gbps": n(52),
    "packet_forwarding_rate_mpps": n(38.69),
    "packet_buffer_mb": n(1.5, "12 Mb shared packet buffer"),
    "jumbo_frame_bytes": n(9216, "Maximum 9K jumbo frame"),
    "mac_address_table": t("16K"),
    "vlan_count": n(1000, "1K concurrent VLANs; VLAN ID range 1-4093"),
    "igmp_group_capacity": t("1K multicast group memberships"),
    "arp_entry_capacity": t("512 ARP/NDP host entries"),
    "ip_interface_capacity": t("64 routing interfaces (port or VLAN)"),
    "routing_entry_capacity": t("64 IPv4 static routes"),
    "lag_group_capacity": t("12 LAGs; up to 8 ports per LAG"),
    "l2_features": t(
        "IEEE 802.1Q; port-, subnet-, MAC- and protocol-based VLANs; QinQ; private VLANs; "
        "LACP; IGMP/MLD snooping and querier; MVR; LLDP/LLDP-MED; sFlow; RSPAN; QoS"
    ),
    "l3_features": t("IPv4 static routing; port-, subnet-, VLAN- and loopback-based routing; ECMP; proxy ARP"),
    "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP with up to 32 instances"),
    "acl_security": t(
        "50 ACLs; up to 509 configurable rules per list and 4K system-wide rules; L2/L3/L4 "
        "IPv4/IPv6 matching; 802.1X; DHCP snooping; IP source guard; port MAC locking"
    ),
    "dhcp_features": t(
        "DHCP client, relay and server; 16 server pools and 1,024 leases; DHCP snooping with "
        "16K bindings and 1,024 static entries; DHCP/BOOTP auto-install"
    ),
    "management_methods": t(
        "Web GUI (HTTP/HTTPS); industry-standard CLI; Telnet/SSH; SNMP; RMON; sFlow; RSPAN; NMS300"
    ),
    "dimensions_mm": t("440 x 257 x 43.2 mm (W x D x H)"),
    "operating_temperature_c": t("0 to 50 °C"),
}


PRODUCTS = {
    "M4100-26G": {
        **COMMON,
        "poe_standard": na("Non-PoE model"),
        "poe_ports": na("Non-PoE model"),
        "poe_budget_w": na("Non-PoE model"),
        "max_poe_per_port_w": na("Non-PoE model"),
        "poe_configuration": na("Non-PoE model"),
        "max_power_consumption_w": n(31.6),
        "power_supply": t("Fixed internal AC power supply; one optional RPS connector"),
    },
    "M4100-26G-PoE": {
        **COMMON,
        "poe_standard": t("IEEE 802.3af PoE"),
        "poe_ports": n(24),
        "poe_budget_w": n(380, "192 W internal PoE budget; up to 380 W with optional EPS"),
        "max_poe_per_port_w": n(15.4),
        "poe_configuration": t("24 x IEEE 802.3af PoE ports; 192 W internal / 380 W with optional EPS"),
        "max_power_consumption_w": n(272.9),
        "power_supply": t("Fixed internal AC power supply; one optional RPS or EPS connector"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR M4100-26G and M4100-26G-PoE specifications."
    document_version = "Official NETGEAR M4100 series datasheet; accessed 2026-10-20"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="NETGEAR").first()
        if not brand:
            raise CommandError("Missing brand: NETGEAR")
        codes = {code for values in PRODUCTS.values() for code in values}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        source, _ = SourceDocument.objects.update_or_create(
            url=SOURCE_URL, document_version=self.document_version,
            defaults={
                "brand": brand, "product": None,
                "document_type": SourceDocument.DocumentType.DATASHEET,
                "title": "NETGEAR ProSAFE Intelligent Edge Managed Switches M4100 Series datasheet",
                "region": "Global", "published_date": None, "accessed_date": accessed, "active": True,
            },
        )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
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
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": SOURCE_URL[:200],
                    "source_note": "Manually verified from the official NETGEAR M4100 series datasheet, pp. 2-5 and 17-33.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "not_applicable":
                    new_value = None
                    defaults["value_status"] = ProductSpec.ValueStatus.NOT_APPLICABLE
                    defaults["normalized_value"] = ""
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had and kind != "not_applicable":
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"pp. 2-5 and 17-33 - {model} specifications - {code}",
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
