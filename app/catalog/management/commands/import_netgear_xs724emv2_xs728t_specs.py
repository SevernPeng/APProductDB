from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "XS724EM": {
        "url": "https://www.downloads.netgear.com/files/GDC/XS512EMv2/XS512EMv2_XS724EMv2_DS.pdf",
        "title": "NETGEAR XS512EMv2 and XS724EMv2 Plus Switches datasheet",
        "version": "DS-XS512EM/XS724EM-02Apr26; accessed 2026-10-20",
        "location": "XS724EMv2 feature and technical-specification tables",
    },
    "XS728T": {
        "url": "https://www.netgear.com/images/datasheet/switches/SmartSwitches/XS708T_XS712Tv2_XS716T_XS728T_XS748T_DS.pdf",
        "title": "NETGEAR 10-Gigabit Smart Managed Pro Switches datasheet",
        "version": "Official NETGEAR XS708T/XS712Tv2/XS716T/XS728T/XS748T datasheet; accessed 2026-10-20",
        "location": "XS728T hardware, features, performance and physical-specification columns",
    },
}


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


def u(raw):
    return "unknown", None, raw


PRODUCTS = {
    "XS724EM": {
        "ethernet_interfaces": t("24 x 100M/1G/2.5G/5G/10GBASE-T RJ45; 4 x dedicated 1G/10G SFP+"),
        "uplink_interfaces": t("4 x dedicated 1G/10G SFP+; up to 2 copper transceiver modules supported"),
        "switching_capacity_gbps": n(560),
        "packet_forwarding_rate_mpps": n(416.7),
        "packet_buffer_mb": n(8),
        "jumbo_frame_bytes": n(12288, "Up to 12K jumbo frames"),
        "mac_address_table": t("32K"),
        "vlan_count": n(64),
        "igmp_group_capacity": t("256 multicast groups"),
        "lag_group_capacity": t("12 LAGs; up to 8 ports per LAG"),
        "l2_features": t(
            "Port-based and IEEE 802.1Q VLANs; management VLAN; static LAG and LACP; "
            "IGMPv1/v2/v3 snooping and querier; storm control; port mirroring; loop detection; QoS"
        ),
        "acl_security": t(
            "Automatic denial-of-service prevention; broadcast, multicast and unknown-unicast storm control"
        ),
        "dhcp_features": t("DHCP client"),
        "management_methods": t("Web browser-based management GUI"),
        "dimensions_mm": t("440 x 204 x 43 mm (W x D x H)"),
        "power_supply": t("Fixed internal 100-240 V AC, 50/60 Hz, 3 A power supply"),
        "max_power_consumption_w": n(139),
        "fan_design": t("3 fans; 35.3 dBA acoustic noise"),
        "fanless": b(False),
        "operating_temperature_c": t("0 to 50 °C"),
        "ip_interface_capacity": u("Not published for this Layer 2 Plus Switch; prior '×' value removed"),
    },
    "XS728T": {
        "ethernet_interfaces": t("24 x 1G/10GBASE-T RJ45; 4 x dedicated 1G/10G SFP+"),
        "uplink_interfaces": t("4 x dedicated 1G/10G SFP+"),
        "switch_usb_interfaces": t("1 x USB port for firmware and configuration files"),
        "cpu": t("800 MHz dual-core CPU"),
        "dram_memory": t("512 MB RAM"),
        "flash_memory": t("8 MB SPI flash and 256 MB NAND flash"),
        "switching_capacity_gbps": n(560),
        "packet_forwarding_rate_mpps": n(416.6),
        "packet_buffer_mb": n(3),
        "jumbo_frame_bytes": n(10240, "Up to 10K jumbo frames"),
        "mac_address_table": t("16K"),
        "vlan_count": n(512),
        "igmp_group_capacity": t("512 multicast groups"),
        "arp_entry_capacity": t("1K ARP/NDP entries"),
        "ip_interface_capacity": t("32 IP VLAN interfaces"),
        "routing_entry_capacity": t("64 IPv4 and 64 IPv6 static routes"),
        "lag_group_capacity": t("12 LAGs; up to 8 ports per LAG"),
        "l2_features": t(
            "IEEE 802.1Q and private VLANs; LACP; IGMP and MLD snooping; LLDP/LLDP-MED; "
            "port mirroring; storm control; QoS"
        ),
        "l3_features": t("IPv4 and IPv6 static routing and VLAN routing"),
        "stp_features": t("IEEE 802.1D STP; IEEE 802.1w RSTP; IEEE 802.1s MSTP"),
        "acl_security": t(
            "164 shared MAC, IPv4 and IPv6 ACLs with L2/L3/L4 matching; 802.1X; RADIUS; MAC locking"
        ),
        "dhcp_features": t("DHCP client and DHCP snooping with up to 1K bindings"),
        "management_methods": t("Web GUI; Smart Control Center; SNMP/RMON; TFTP/HTTP; syslog"),
        "dimensions_mm": t("440 x 310 x 43 mm (W x D x H)"),
        "power_supply": t("One fixed internal AC power supply"),
        "max_power_consumption_w": n(134.9),
        "fan_design": t("4 fixed fans; 41.6 dBA acoustic noise"),
        "fanless": b(False),
        "operating_temperature_c": t("0 to 50 °C"),
    },
}


class Command(BaseCommand):
    help = "Import manually verified NETGEAR XS724EMv2 and XS728T specifications."

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
        documents = {}
        for model, source_data in SOURCES.items():
            documents[model], _ = SourceDocument.objects.update_or_create(
                url=source_data["url"], document_version=source_data["version"],
                defaults={
                    "brand": brand, "product": None,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": source_data["title"], "region": "Global",
                    "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, values in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing NETGEAR product: {model}")
            source_data = SOURCES[model]
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
                    "normalized_value": "" if value is None else str(value), "unit": definition.unit,
                    "raw_value": raw, "source_url": source_data["url"][:200],
                    "source_note": f"Manually verified from the official NETGEAR datasheet: {source_data['location']}.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    new_value = Decimal(str(value)); defaults["value_number"] = new_value
                elif kind == "boolean":
                    new_value = bool(value); defaults["value_boolean"] = new_value
                elif kind == "unknown":
                    new_value = None; defaults["value_status"] = ProductSpec.ValueStatus.UNKNOWN
                else:
                    new_value = str(value); defaults["value_text"] = new_value
                spec, _ = ProductSpec.objects.update_or_create(
                    product=product, definition=definition, defaults=defaults
                )
                if not had and kind not in {"unknown"}:
                    newly_filled += 1; model_new += 1
                elif old_status != defaults["value_status"] or old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=documents[model],
                    source_location=f"{source_data['location']} - {model} - {code}",
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
