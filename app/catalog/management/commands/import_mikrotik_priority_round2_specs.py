from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


def n(value, raw=None):
    return "number", value, raw or str(value)


def t(value, raw=None):
    return "text", value, raw or str(value)


def b(value=True, raw=None):
    return "boolean", value, raw or ("Yes" if value else "No")


ROUTEROS_MGMT = "RouterOS via WinBox, WebFig, SSH/CLI, API and MikroTik mobile app"
ROUTEROS_FIREWALL = (
    "Stateful firewall and connection tracking; source/destination NAT; filter, mangle and RAW rules; "
    "address lists; Layer 7 matching"
)
ROUTEROS_VPN = "IPsec/IKEv2; WireGuard; OpenVPN; SSTP; L2TP; PPTP; IPIP; EoIP"


PRODUCTS = {
    "ATL 5G R16": {
        "url": "https://mikrotik.com/product/atl_5g_r16",
        "values": {
            "ethernet_interfaces": t("1 x 1GbE RJ45 with 802.3af/at PoE-in"),
            "wan_interfaces": t("5G/LTE cellular modem; 1 x 1GbE RJ45 configurable by RouterOS"),
            "lan_interfaces": t("1 x 1GbE RJ45 configurable by RouterOS"),
            "uplink_interfaces": t("5G/LTE cellular modem; 1 x 1GbE RJ45"),
            "routing_throughput_mbps": n(987.3, "Routing, no rules (fast path), 1518-byte packets: 987.3 Mbps"),
            "controller_management": t(ROUTEROS_MGMT),
            "firewall_features": t(ROUTEROS_FIREWALL),
            "vpn_protocols": t(ROUTEROS_VPN),
            "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
            "sim_interfaces": t("1 x Micro SIM plus built-in eSIM"),
            "cellular_standard": t("5G SA/NSA; LTE Category 20; 3G Release 8"),
            "cellular_downlink_mbps": n(2000, "LTE Category 20: 2.0 Gbps downlink"),
            "operating_temperature_c": t("-40 to 70 °C"),
            "router_wifi_standard": t("No integrated Wi-Fi radio"),
            "router_supported_bands": t("None; 5G/LTE cellular and Ethernet connectivity only"),
        },
    },
    "CCR1009-7G-1C-1S+": {
        "url": "https://mikrotik.com/product/CCR1009-7G-1C-1Splus",
        "values": {
            "ethernet_interfaces": t("7 x 1GbE RJ45; 1 x 1GbE RJ45/SFP combo; 1 x 10GbE SFP+"),
            "wan_interfaces": t("RouterOS-configurable: 7 x 1GbE, 1 x 1GbE RJ45/SFP combo and 1 x 10GbE SFP+"),
            "lan_interfaces": t("RouterOS-configurable: 7 x 1GbE, 1 x 1GbE RJ45/SFP combo and 1 x 10GbE SFP+"),
            "uplink_interfaces": t("1 x 10GbE SFP+; 1 x 1GbE RJ45/SFP combo"),
            "routing_throughput_mbps": n(15791.9, "Routing, no rules (fast path), 1518-byte packets: 15,791.9 Mbps"),
            "vpn_throughput_mbps": n(2693.6, "IPsec, 256 test tunnels, AES-256-CBC + SHA1/SHA256, 1400-byte packets: 2,693.6 Mbps"),
            "controller_management": t(ROUTEROS_MGMT),
            "firewall_features": t(ROUTEROS_FIREWALL),
            "vpn_protocols": t(ROUTEROS_VPN),
            "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
            "usb_interfaces": t("1 x microUSB type AB; USB power reset"),
            "operating_temperature_c": t("-20 to 60 °C"),
        },
    },
    "Chateau LTE6 ax": {
        "url": "https://mikrotik.com/product/chateau_lte6_ax",
        "values": {
            "ethernet_interfaces": t("4 x 1GbE RJ45; 1 x 2.5GbE RJ45"),
            "wan_interfaces": t("LTE Category 6 cellular modem; 4 x 1GbE and 1 x 2.5GbE configurable by RouterOS"),
            "lan_interfaces": t("4 x 1GbE and 1 x 2.5GbE configurable by RouterOS"),
            "uplink_interfaces": t("1 x 2.5GbE RJ45; LTE Category 6 cellular modem"),
            "routing_throughput_mbps": n(2657.8, "Routing, no rules (fast path), 1518-byte packets: 2,657.8 Mbps"),
            "vpn_throughput_mbps": n(878.1, "IPsec, single tunnel, AES-128-CBC + SHA1, 1400-byte packets: 878.1 Mbps"),
            "controller_management": t(ROUTEROS_MGMT + "; TR-069 remote management"),
            "firewall_features": t(ROUTEROS_FIREWALL),
            "vpn_protocols": t(ROUTEROS_VPN),
            "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
            "sim_interfaces": t("1 x Micro SIM"),
            "usb_interfaces": t("1 x USB Type-A; USB power reset"),
            "cellular_standard": t("LTE Category 6; 3G Release 8"),
            "cellular_downlink_mbps": n(300, "LTE Category 6: 300 Mbit/s downlink"),
        },
    },
    "Chateau LTE7 ax": {
        "url": "https://mikrotik.com/product/chateau_lte7_ax",
        "values": {
            "ethernet_interfaces": t("4 x 1GbE RJ45; 1 x 2.5GbE RJ45"),
            "wan_interfaces": t("LTE Category 7 cellular modem; 4 x 1GbE and 1 x 2.5GbE configurable by RouterOS"),
            "lan_interfaces": t("4 x 1GbE and 1 x 2.5GbE configurable by RouterOS"),
            "uplink_interfaces": t("1 x 2.5GbE RJ45; LTE Category 7 cellular modem"),
            "routing_throughput_mbps": n(2657.8, "Routing, no rules (fast path), 1518-byte packets: 2,657.8 Mbps"),
            "vpn_throughput_mbps": n(878.1, "IPsec, single tunnel, AES-128-CBC + SHA1, 1400-byte packets: 878.1 Mbps"),
            "controller_management": t(ROUTEROS_MGMT + "; TR-069 remote management"),
            "firewall_features": t(ROUTEROS_FIREWALL),
            "vpn_protocols": t(ROUTEROS_VPN),
            "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
            "sim_interfaces": t("1 x Micro SIM"),
            "usb_interfaces": t("1 x USB Type-A; USB power reset"),
            "cellular_standard": t("LTE Category 7; 3G Release 8"),
            "cellular_downlink_mbps": n(300, "LTE Category 7: 300 Mbps downlink"),
        },
    },
    "hAP ax S": {
        "url": "https://mikrotik.com/product/hap_ax_s",
        "values": {
            "ethernet_interfaces": t("5 x 1GbE RJ45; 1 x SFP cage with 2.5G support"),
            "wan_interfaces": t("RouterOS-configurable: 5 x 1GbE RJ45 and 1 x SFP cage with 2.5G support"),
            "lan_interfaces": t("RouterOS-configurable: 5 x 1GbE RJ45 and 1 x SFP cage with 2.5G support"),
            "uplink_interfaces": t("1 x SFP cage with 2.5G support"),
            "routing_throughput_mbps": n(3646.6, "Routing, no rules (fast path), 1518-byte packets: 3,646.6 Mbps"),
            "vpn_throughput_mbps": n(351.7, "IPsec, single tunnel, AES-128-CBC + SHA1, 1400-byte packets: 351.7 Mbps"),
            "controller_management": t(ROUTEROS_MGMT),
            "firewall_features": t(ROUTEROS_FIREWALL),
            "vpn_protocols": t(ROUTEROS_VPN),
            "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
            "usb_interfaces": t("1 x USB Type-A; USB power reset"),
        },
    },
    "hEX": {
        "url": "https://mikrotik.com/product/RB750Gr3",
        "values": {},
    },
    "hEX RB750Gr3": {
        "url": "https://mikrotik.com/product/RB750Gr3",
        "values": {},
    },
    "hEX S": {
        "url": "https://mikrotik.com/product/hex_s",
        "values": {},
    },
    "hEX S RB760iGS": {
        "url": "https://mikrotik.com/product/hex_s",
        "values": {},
    },
    "hEX lite": {
        "url": "https://mikrotik.com/product/RB750r2",
        "values": {
            "ethernet_interfaces": t("5 x 10/100 Ethernet RJ45"),
            "wan_interfaces": t("RouterOS-configurable: 5 x 10/100 Ethernet RJ45"),
            "lan_interfaces": t("RouterOS-configurable: 5 x 10/100 Ethernet RJ45"),
            "uplink_interfaces": t("RouterOS-configurable: any of 5 x 10/100 Ethernet RJ45"),
            "routing_throughput_mbps": n(493.0, "Routing, no rules (fast path), 1518-byte packets: 493.0 Mbps"),
            "controller_management": t(ROUTEROS_MGMT),
            "firewall_features": t(ROUTEROS_FIREWALL),
            "vpn_protocols": t(ROUTEROS_VPN),
            "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
            "operating_temperature_c": t("-40 to 70 °C"),
            "usb_interfaces": t("No USB interface"),
        },
    },
    "wAP ax LTE7 kit": {
        "url": "https://mikrotik.com/product/wap_ax_lte7",
        "values": {
            "ethernet_interfaces": t("2 x 1GbE RJ45; one port supports 802.3af/at PoE-in"),
            "wan_interfaces": t("LTE Category 7 cellular modem; 2 x 1GbE RJ45 configurable by RouterOS"),
            "lan_interfaces": t("2 x 1GbE RJ45 configurable by RouterOS"),
            "routing_throughput_mbps": n(1927.3, "Routing, no rules (fast path), 1518-byte packets: 1,927.3 Mbps"),
            "controller_management": t(ROUTEROS_MGMT + "; CAPsMAN centralized Wi-Fi management"),
            "firewall_features": t(ROUTEROS_FIREWALL),
            "vpn_protocols": t(ROUTEROS_VPN),
            "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
            "sim_interfaces": t("1 x Micro SIM"),
            "cellular_standard": t("LTE Category 7; 3G Release 8"),
            "cellular_downlink_mbps": n(300, "LTE Category 7: 300 Mbps downlink"),
        },
    },
}


HEX_VALUES = {
    "ethernet_interfaces": t("5 x 1GbE RJ45"),
    "wan_interfaces": t("RouterOS-configurable: 5 x 1GbE RJ45"),
    "lan_interfaces": t("RouterOS-configurable: 5 x 1GbE RJ45"),
    "uplink_interfaces": t("RouterOS-configurable: any of 5 x 1GbE RJ45"),
    "routing_throughput_mbps": n(1802.2, "Routing, no rules (fast path), 1518-byte packets: 1,802.2 Mbps"),
    "vpn_throughput_mbps": n(231.8, "IPsec, single tunnel, AES-128-CBC + SHA1, 1400-byte packets: 231.8 Mbps"),
    "controller_management": t(ROUTEROS_MGMT),
    "firewall_features": t(ROUTEROS_FIREWALL),
    "vpn_protocols": t(ROUTEROS_VPN),
    "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
    "usb_interfaces": t("1 x USB Type-A; USB power reset"),
    "operating_temperature_c": t("-40 to 60 °C"),
}


HEX_S_VALUES = {
    "ethernet_interfaces": t("5 x 1GbE RJ45; 1 x 1.25Gbps SFP"),
    "wan_interfaces": t("RouterOS-configurable: 5 x 1GbE RJ45 and 1 x 1.25Gbps SFP"),
    "lan_interfaces": t("RouterOS-configurable: 5 x 1GbE RJ45 and 1 x 1.25Gbps SFP"),
    "uplink_interfaces": t("1 x 1.25Gbps SFP"),
    "routing_throughput_mbps": n(1802.2, "Routing, no rules (fast path), 1518-byte packets: 1,802.2 Mbps"),
    "vpn_throughput_mbps": n(231.8, "IPsec, single tunnel, AES-128-CBC + SHA1, 1400-byte packets: 231.8 Mbps"),
    "controller_management": t(ROUTEROS_MGMT),
    "firewall_features": t(ROUTEROS_FIREWALL),
    "vpn_protocols": t(ROUTEROS_VPN),
    "wan_load_balancing": b(True, "RouterOS PCC supports multi-WAN load-balancing configurations"),
    "usb_interfaces": t("1 x USB Type-A; USB power reset"),
    "operating_temperature_c": t("-40 to 70 °C"),
}

for model in ("hEX", "hEX RB750Gr3"):
    PRODUCTS[model]["values"] = dict(HEX_VALUES)
for model in ("hEX S", "hEX S RB760iGS"):
    PRODUCTS[model]["values"] = dict(HEX_S_VALUES)


SOFTWARE_CODES = {"controller_management", "firewall_features", "vpn_protocols", "wan_load_balancing"}
NON_CELLULAR_MODELS = {
    "CCR1009-7G-1C-1S+", "hAP ax S", "hEX", "hEX RB750Gr3", "hEX S", "hEX S RB760iGS", "hEX lite"
}


class Command(BaseCommand):
    help = "Import manually verified MikroTik gateway specifications (round 2)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="MikroTik").first()
        if not brand:
            raise CommandError("Missing brand: MikroTik")

        codes = {code for item in PRODUCTS.values() for code in item["values"]} | {"cellular_standard"}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        routeros_doc, _ = SourceDocument.objects.update_or_create(
            url="https://help.mikrotik.com/docs/spaces/ROS/pages/19136707/Software+Specifications",
            document_version="Current RouterOS software specification; accessed 2026-10-15",
            defaults={
                "brand": brand, "product": None,
                "document_type": SourceDocument.DocumentType.SUPPORT,
                "title": "MikroTik RouterOS software specifications",
                "region": "Global", "published_date": None, "accessed_date": accessed, "active": True,
            },
        )

        written = newly_filled = corrected = unchanged = false_values_cleared = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing MikroTik product: {model}")
            product_doc, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Current official product page and performance-test tables; accessed 2026-10-15",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                    "title": f"MikroTik {model} official specifications and test results",
                    "region": "Global", "published_date": None, "accessed_date": accessed, "active": True,
                },
            )
            model_new = model_corrected = 0
            for code, (kind, value, raw) in item["values"].items():
                definition = definitions[code]
                existing = ProductSpec.objects.filter(product=product, definition=definition).first()
                had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                    bool((existing.value_text or "").strip()) or existing.value_number is not None or existing.value_boolean is not None
                ))
                old_value = None
                if had:
                    old_value = existing.value_text if existing.value_text else existing.value_number if existing.value_number is not None else existing.value_boolean
                source = routeros_doc if code in SOFTWARE_CODES else product_doc
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": source.url[:200],
                    "source_note": "Manually verified from the current exact-model MikroTik product page and official RouterOS documentation.",
                    "verified_date": accessed,
                }
                if kind == "number":
                    defaults["value_number"] = Decimal(str(value)); new_value = Decimal(str(value))
                elif kind == "boolean":
                    defaults["value_boolean"] = bool(value); new_value = bool(value)
                else:
                    defaults["value_text"] = str(value); new_value = str(value)
                spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                if not had:
                    newly_filled += 1; model_new += 1
                elif old_value != new_value:
                    corrected += 1; model_corrected += 1
                else:
                    unchanged += 1
                SpecEvidence.objects.update_or_create(
                    product_spec=spec, source_document=source,
                    source_location=f"Official product/performance table or RouterOS feature list - {model} - {code}",
                    defaults={
                        "source_excerpt": f"{definition.display_name}: {raw}",
                        "evidence_level": SpecEvidence.EvidenceLevel.A,
                        "verified_at": timezone.now(),
                    },
                )
                written += 1

            if model in NON_CELLULAR_MODELS:
                cell_def = definitions["cellular_standard"]
                false_spec = ProductSpec.objects.filter(product=product, definition=cell_def).first()
                if false_spec and false_spec.value_status == ProductSpec.ValueStatus.PUBLISHED and (false_spec.value_text or "").strip():
                    false_spec.value_status = ProductSpec.ValueStatus.UNKNOWN
                    false_spec.value_text = ""
                    false_spec.value_number = None
                    false_spec.value_boolean = None
                    false_spec.normalized_value = ""
                    false_spec.raw_value = ""
                    false_spec.source_url = product_doc.url[:200]
                    false_spec.source_note = "Corrected: this exact model has no built-in cellular modem; the prior LTE/5G value was a page-parser artifact."
                    false_spec.verified_date = accessed
                    false_spec.save()
                    false_values_cleared += 1
            per_model.append(f"{model}:+{model_new}/corrected:{model_corrected}")

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} false_values_cleared={false_values_cleared} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
