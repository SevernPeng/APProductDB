from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Brand, Product, ProductSpec, SourceDocument, SpecDefinition, SpecEvidence


SOURCES = {
    "UCG-Max": "https://techspecs.ui.com/unifi/cloud-gateways/ucg-max",
    "UCG-Ultra": "https://techspecs.ui.com/unifi/cloud-gateways/ucg-ultra?s=us",
    "UDR": "https://techspecs.ui.com/unifi/cloud-gateways/udr",
    "UMR-Industial": "https://techspecs.ui.com/unifi/integrations/umr-industrial-us?s=in",
    "UXG-Enterprise": "https://techspecs.ui.com/unifi/accessories/uxg-enterprise",
    "UXG-Fiber": "https://techspecs.ui.com/unifi/cloud-gateways/uxg-fiber",
    "UXG-Lite": "https://techspecs.ui.com/unifi/advanced-hosting/uxg-lite?s=eu",
    "UXG-Max": "https://techspecs.ui.com/unifi/cloud-gateways/uxg-max",
    "UXG-Pro": "https://techspecs.ui.com/unifi/cloud-gateways/uxg-pro",
}

ITEMS = []


def add(models, code, kind, value, raw, location):
    for model in models:
        ITEMS.append({
            "model": model,
            "code": code,
            "kind": kind,
            "value": value,
            "raw": raw,
            "location": location,
        })


FULL_GATEWAYS = (
    "UCG-Max", "UCG-Ultra", "UDR", "UXG-Enterprise", "UXG-Fiber",
    "UXG-Lite", "UXG-Max", "UXG-Pro",
)
FIREWALL = (
    "Stateful firewall; application-aware Layer 7 firewall; DPI and traffic identification; "
    "zone-based advanced filtering; content filtering; IDS/IPS; ad blocking"
)
VPN = "Site Magic; IPsec; OpenVPN; WireGuard; L2TP; Teleport"
for model in FULL_GATEWAYS:
    add((model,), "firewall_features", "text", FIREWALL, "Stateful Firewall; Application-Aware Layer 7 Firewall; DPI & Traffic Identification; Zone-Based Firewall Advanced Filtering; Content Filtering; Intrusion Prevention (IPS/IDS); Ad Blocking", "Security")
    add((model,), "sd_wan", "text", "License-free UniFi SD-WAN; Site Magic", "VPN & SD-WAN: License-Free SD-WAN; Site-to-Site VPN: Site Magic", "VPN & SD-WAN")
    add((model,), "vpn_protocols", "text", VPN, "Site-to-Site VPN: Site Magic, IPsec, OpenVPN; VPN server/client: Teleport, WireGuard, OpenVPN, L2TP", "VPN & SD-WAN")

for model in ("UCG-Max", "UCG-Ultra", "UDR"):
    add((model,), "controller_management", "text", "Integrated UniFi Network application; Ethernet/Bluetooth management", "UniFi Application Suite: Network; Management: Ethernet, Bluetooth", "Overview / Hardware — Management")
for model in ("UXG-Enterprise", "UXG-Fiber", "UXG-Lite", "UXG-Max", "UXG-Pro"):
    add((model,), "controller_management", "text", "UniFi Network application", "Application requirements: UniFi Network", "Software — Application Requirements")

for model in ("UCG-Max", "UCG-Ultra", "UXG-Enterprise", "UXG-Fiber", "UXG-Max", "UXG-Pro"):
    add((model,), "wan_load_balancing", "boolean", True, "Networking: Multi-WAN Load Balancing — supported", "Networking — Multi-WAN Load Balancing")


# Cloud Gateway Max.
add(("UCG-Max",), "dimensions_mm", "text", "141.8 x 127.6 x 30 mm", "Dimensions: 141.8 x 127.6 x 30 mm", "Overview — Dimensions")
add(("UCG-Max",), "ethernet_interfaces", "text", "5 x 2.5GbE RJ45 (1 default WAN; up to 4 WAN)", "Port layout: five 2.5 GbE RJ45; default WAN: one 2.5 GbE RJ45; max WAN port count: 4", "Overview — Port Layout")
add(("UCG-Max",), "lan_interfaces", "text", "4 x 2.5GbE RJ45 by default; ports are WAN-remappable", "Port layout: five 2.5 GbE RJ45; one default WAN; max WAN port count: 4", "Overview — Port Layout")
add(("UCG-Max",), "wan_interfaces", "text", "1 x 2.5GbE RJ45 default; up to 4 WAN ports", "Default WAN ports: (1) 2.5 GbE RJ45; max WAN port count: 4", "Overview — WAN Ports")
add(("UCG-Max",), "uplink_interfaces", "text", "1 x 2.5GbE RJ45 default WAN; up to 4 WAN ports", "Default WAN ports: (1) 2.5 GbE RJ45; max WAN port count: 4", "Overview — WAN Ports")
add(("UCG-Max",), "usb_interfaces", "text", "USB Type-C power input", "Power method: USB type C (5V DC/5A)", "Hardware — Power Method")
add(("UCG-Max",), "lightning_protection_kv", "text", "ESD/EMP: ±8 kV air, ±4 kV contact", "ESD/EMP protection: Air ±8kV; contact ±4kV", "Hardware — ESD/EMP Protection")
add(("UCG-Max",), "max_power_consumption_w", "number", 16.1, "Max. power consumption: 16.1W", "Hardware — Max. Power Consumption")
add(("UCG-Max",), "operating_temperature_c", "text", "-10 to 40 °C", "Ambient operating temperature: -10 to 40° C", "Hardware — Environment")


# Cloud Gateway Ultra.
add(("UCG-Ultra",), "dimensions_mm", "text", "141.8 x 127.6 x 30 mm", "Dimensions: 141.8 x 127.6 x 30 mm", "Overview — Dimensions")
add(("UCG-Ultra",), "ethernet_interfaces", "text", "4 x 1GbE RJ45; 1 x 2.5GbE RJ45", "Port layout: four 1 GbE RJ45; one 2.5 GbE RJ45", "Overview — Port Layout")
add(("UCG-Ultra",), "lan_interfaces", "text", "4 x 1GbE RJ45 by default; ports are WAN-remappable", "Port layout: four 1 GbE RJ45 plus one 2.5 GbE RJ45; max WAN port count: 4", "Overview — Port Layout")
add(("UCG-Ultra",), "wan_interfaces", "text", "1 x 2.5GbE RJ45 default; up to 4 WAN ports", "Default WAN ports: (1) 2.5 GbE RJ45; max WAN port count: 4", "Overview — WAN Ports")
add(("UCG-Ultra",), "uplink_interfaces", "text", "1 x 2.5GbE RJ45 default WAN; up to 4 WAN ports", "Default WAN ports: (1) 2.5 GbE RJ45; max WAN port count: 4", "Overview — WAN Ports")
add(("UCG-Ultra",), "usb_interfaces", "text", "USB Type-C power input", "Power method: USB type C (5V DC/3A)", "Hardware — Power Method")
add(("UCG-Ultra",), "max_power_consumption_w", "number", 6.2, "Max. power consumption: 6.2W", "Hardware — Max. Power Consumption")
add(("UCG-Ultra",), "operating_temperature_c", "text", "-10 to 40 °C", "Ambient operating temperature: -10 to 40° C", "Hardware — Environment")


# Dream Router.
add(("UDR",), "dimensions_mm", "text", "110 x 184.1 mm", "Dimensions: diameter 110 x 184.1 mm", "Overview — Dimensions")
add(("UDR",), "ethernet_interfaces", "text", "5 x 1GbE RJ45 (1 default WAN; 4 LAN, including 2 PoE)", "Port layout: five 1 GbE RJ45, two PoE; default WAN ports: one GbE RJ45", "Overview — Port Layout")
add(("UDR",), "lan_interfaces", "text", "4 x 1GbE RJ45 LAN, including 2 PoE ports", "Port layout: five 1 GbE RJ45, two PoE; one port is the default WAN", "Overview — Port Layout")
add(("UDR",), "wan_interfaces", "text", "1 x 1GbE RJ45", "Default WAN ports: (1) GbE RJ45; max WAN port count: 1", "Overview — WAN Ports")
add(("UDR",), "uplink_interfaces", "text", "1 x 1GbE RJ45 WAN", "Default WAN ports: (1) GbE RJ45", "Overview — WAN Ports")
add(("UDR",), "max_power_consumption_w", "number", 19.37, "Max. power consumption: 19.37W excluding PoE output", "Hardware — Max. Power Consumption")
add(("UDR",), "operating_temperature_c", "text", "-10 to 45 °C", "Ambient operating temperature: -10 to 45° C", "Hardware — Environment")
add(("UDR",), "router_wifi_standard", "text", "Wi-Fi 6 (802.11a/b/g/n/ac/ax)", "WiFi standard: 802.11a/b/g/n/ac/ax (WiFi 6)", "Integrated WiFi")
add(("UDR",), "router_supported_bands", "text", "2.4 GHz / 5 GHz", "Integrated WiFi: 2.4 GHz and 5 GHz", "Integrated WiFi")
add(("UDR",), "router_wireless_rate_mbps", "number", 3000, "Throughput: 5 GHz 2.4 Gbps; 2.4 GHz 600 Mbps", "Integrated WiFi — Throughput")


# Mobile Router Industrial. The database contains a historical spelling error in its model key.
add(("UMR-Industial",), "cellular_standard", "text", "LTE Cat 4", "Networking interface: LTE Cat 4 radio", "Overview — Networking Interface")
add(("UMR-Industial",), "cellular_downlink_mbps", "number", 150, "LTE throughput speed: download 150 Mbps / upload 50 Mbps", "Hardware — LTE Throughput Speed")
add(("UMR-Industial",), "sim_interfaces", "text", "1 x Nano SIM", "SIM: Nano SIM", "Overview — SIM")
add(("UMR-Industial",), "controller_management", "text", "Local management over Ethernet or Wi-Fi", "Management: Ethernet, WiFi", "Hardware — Management")
add(("UMR-Industial",), "dimensions_mm", "text", "114.5 x 93.6 x 32 mm without antennas/cover; 217 x 94 x 32 mm with antennas and outdoor cover", "Dimensions: 114.5 x 93.6 x 32 mm without antennas and outdoor cover; 217 x 94 x 32 mm with antennas and outdoor cover", "Overview — Dimensions")
add(("UMR-Industial",), "ethernet_interfaces", "text", "2 x GbE RJ45; LTE Cat 4 radio; Wi-Fi 4", "Networking interface: (2) GbE RJ45 ports, LTE Cat 4 radio, WiFi 4", "Overview — Networking Interface")
add(("UMR-Industial",), "lan_interfaces", "text", "2 x GbE RJ45; Ethernet bridge mode supported", "Networking interface: (2) GbE RJ45 ports; Ethernet Bridge Mode supported", "Overview / Features")
add(("UMR-Industial",), "wan_interfaces", "text", "LTE Cat 4, Wi-Fi, or Ethernet with priority/fallback", "WAN Priority & Fallback: Cellular, WiFi, Ethernet", "Features — WAN")
add(("UMR-Industial",), "uplink_interfaces", "text", "LTE Cat 4, Wi-Fi, or Ethernet WAN", "WAN Priority & Fallback: Cellular, WiFi, Ethernet", "Features — WAN")
add(("UMR-Industial",), "usb_interfaces", "text", "USB Type-C power input", "Power method: USB Type-C (5V DC)", "Hardware — Power Method")
add(("UMR-Industial",), "firewall_features", "text", "Firewall; port forwarding; static routes; LTE passthrough; Ethernet bridge mode", "Features: Firewall, Port Forwarding, Static Routes, LTE Passthrough mode, Ethernet Bridge Mode", "Features")
add(("UMR-Industial",), "vpn_protocols", "text", "OpenVPN and WireGuard client; IPsec and WireGuard site-to-site VPN", "VPN client: OpenVPN, WireGuard; Site-to-Site VPN: IPsec, WireGuard", "Features — VPN")
add(("UMR-Industial",), "max_power_consumption_w", "number", 12.5, "Max. power consumption: 12.5W", "Hardware — Max. Power Consumption")
add(("UMR-Industial",), "operating_temperature_c", "text", "-40 to 70 °C", "Ambient operating temperature: -40 to 70° C", "Hardware — Environment")
add(("UMR-Industial",), "router_wifi_standard", "text", "Wi-Fi 4 (802.11b/g/n)", "WiFi standard: WiFi 4; supported data rates: 802.11n/g/b", "Features / Networking")
add(("UMR-Industial",), "router_supported_bands", "text", "2.4 GHz", "WiFi 4 supported data rates: 802.11n/g/b", "Networking — Supported Data Rates")
add(("UMR-Industial",), "router_wireless_rate_mbps", "number", 300, "802.11n supported data rates: up to 300 Mbps (MCS0–MCS7, HT20/40)", "Networking — Supported Data Rates")


# Gateway Enterprise.
add(("UXG-Enterprise",), "concurrent_sessions", "number", 10000000, "Concurrent sessions: 10 Million", "Overview — Capacity")
add(("UXG-Enterprise",), "dimensions_mm", "text", "442.4 x 43.7 x 325 mm", "Dimensions: 442.4 x 43.7 x 325 mm", "Overview — Dimensions")
add(("UXG-Enterprise",), "ethernet_interfaces", "text", "2 x 2.5GbE RJ45; 2 x 10G SFP+; 2 x 25G SFP28", "Port layout: two 2.5 GbE RJ45, two 10G SFP+, two 25G SFP28", "Overview — Port Layout")
add(("UXG-Enterprise",), "wan_interfaces", "text", "1 x 25G SFP28 and 1 x 2.5GbE RJ45 default; up to 5 WAN ports", "Default WAN ports: (1) 25G SFP28 and (1) 2.5 GbE RJ45; max WAN port count: 5", "Overview — WAN Ports")
add(("UXG-Enterprise",), "lan_interfaces", "text", "Remaining 2.5GbE RJ45, 10G SFP+ and 25G SFP28 ports are LAN/WAN-remappable", "Port layout: two 2.5 GbE RJ45, two 10G SFP+, two 25G SFP28; max WAN port count: 5", "Overview — Port Layout")
add(("UXG-Enterprise",), "vpn_throughput_mbps", "number", 1200, "VPN server single-user throughput: Identity Endpoint 1.2 Gbps, Teleport 1.2 Gbps, WireGuard 1.2 Gbps; other protocols lower", "VPN & SD-WAN — VPN Throughput")
add(("UXG-Enterprise",), "max_power_consumption_w", "number", 82, "Max. power consumption: 82W", "Hardware — Max. Power Consumption")
add(("UXG-Enterprise",), "operating_temperature_c", "text", "0 to 40 °C", "Ambient operating temperature: 0 to 40° C", "Hardware — Environment")


# Gateway Fiber.
add(("UXG-Fiber",), "dimensions_mm", "text", "212.8 x 127.6 x 30 mm", "Dimensions: 212.8 x 127.6 x 30 mm", "Overview — Dimensions")
add(("UXG-Fiber",), "ethernet_interfaces", "text", "4 x 2.5GbE RJ45; 1 x 10GbE RJ45; 2 x 10G SFP+", "Port layout: four 2.5 GbE RJ45, one 10 GbE RJ45, two 10G SFP+", "Overview — Port Layout")
add(("UXG-Fiber",), "wan_interfaces", "text", "1 x 10G SFP+ and 1 x 10GbE RJ45 default; up to 6 WAN ports", "Default WAN ports: (1) 10G SFP+ and (1) 10 GbE RJ45; max WAN port count: 6", "Overview — WAN Ports")
add(("UXG-Fiber",), "lan_interfaces", "text", "4 x 2.5GbE RJ45 plus 1 x 10G SFP+ by default; ports are WAN-remappable", "Port layout: four 2.5 GbE RJ45, one 10 GbE RJ45, two 10G SFP+; two default WAN ports", "Overview — Port Layout")
add(("UXG-Fiber",), "max_power_consumption_w", "number", 25, "Max. power consumption: 25W excluding PoE output", "Hardware — Max. Power Consumption")
add(("UXG-Fiber",), "operating_temperature_c", "text", "0 to 40 °C", "Ambient operating temperature: 0 to 40° C", "Hardware — Environment")


# Gateway Lite.
add(("UXG-Lite",), "dimensions_mm", "text", "98 x 98 x 30 mm", "Dimensions: 98 x 98 x 30 mm", "Overview — Dimensions")
add(("UXG-Lite",), "ethernet_interfaces", "text", "2 x 1GbE RJ45", "Port layout: two 1 GbE RJ45", "Overview — Port Layout")
add(("UXG-Lite",), "wan_interfaces", "text", "1 x 1GbE RJ45", "Default WAN ports: (1) GbE RJ45; max WAN port count: 1", "Overview — WAN Ports")
add(("UXG-Lite",), "lan_interfaces", "text", "1 x 1GbE RJ45", "Port layout: two 1 GbE RJ45; one is the default WAN", "Overview — Port Layout")
add(("UXG-Lite",), "max_power_consumption_w", "number", 3.83, "Max. power consumption: 3.83W", "Hardware — Max. Power Consumption")
add(("UXG-Lite",), "operating_temperature_c", "text", "-10 to 40 °C", "Ambient operating temperature: -10 to 40° C", "Hardware — Environment")


# Gateway Max.
add(("UXG-Max",), "dimensions_mm", "text", "141.8 x 127.6 x 30 mm", "Dimensions: 141.8 x 127.6 x 30 mm", "Overview — Dimensions")
add(("UXG-Max",), "ethernet_interfaces", "text", "5 x 2.5GbE RJ45", "Port layout: five 2.5 GbE RJ45", "Overview — Port Layout")
add(("UXG-Max",), "wan_interfaces", "text", "1 x 2.5GbE RJ45 default; up to 4 WAN ports", "Default WAN ports: (1) 2.5 GbE RJ45; max WAN port count: 4", "Overview — WAN Ports")
add(("UXG-Max",), "lan_interfaces", "text", "4 x 2.5GbE RJ45 by default; ports are WAN-remappable", "Port layout: five 2.5 GbE RJ45; one default WAN; max WAN port count: 4", "Overview — Port Layout")
add(("UXG-Max",), "max_power_consumption_w", "number", 9.6, "Max. power consumption: 9.6W", "Hardware — Max. Power Consumption")
add(("UXG-Max",), "operating_temperature_c", "text", "-10 to 40 °C", "Ambient operating temperature: -10 to 40° C", "Hardware — Environment")


# Gateway Pro.
add(("UXG-Pro",), "dimensions_mm", "text", "442.4 x 43.7 x 285.6 mm", "Dimensions: 442.4 x 43.7 x 285.6 mm", "Overview — Dimensions")
add(("UXG-Pro",), "ethernet_interfaces", "text", "2 x 1GbE RJ45; 2 x 10G SFP+", "Port layout includes two 10G SFP+; one GbE RJ45 WAN and one GbE RJ45 LAN", "Overview — Port Layout")
add(("UXG-Pro",), "wan_interfaces", "text", "1 x 10G SFP+ and 1 x 1GbE RJ45 default; up to 3 WAN ports", "Default WAN ports: (1) 10G SFP+ and (1) GbE RJ45; max WAN port count: 3", "Overview — WAN Ports")
add(("UXG-Pro",), "lan_interfaces", "text", "1 x 10G SFP+ and 1 x 1GbE RJ45 LAN by default", "Port layout provides matching 10G SFP+ and GbE RJ45 LAN interfaces", "Overview — Port Layout")
add(("UXG-Pro",), "max_power_consumption_w", "number", 30, "Max. power consumption: 30W", "Hardware — Max. Power Consumption")
add(("UXG-Pro",), "operating_temperature_c", "text", "-10 to 40 °C", "Ambient operating temperature: -10 to 40° C", "Hardware — Environment")


# These devices have no integrated cellular modem. Their pages only mention optional external LTE backup.
CLEAR_CELLULAR = ("UCG-Max", "UCG-Ultra", "UDR", "UXG-Enterprise", "UXG-Lite", "UXG-Max")


class Command(BaseCommand):
    help = "Import manually verified Ubiquiti gateway gap specifications and clear false cellular labels."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Ubiquiti").first()
        if not brand:
            raise CommandError("Missing brand: Ubiquiti")
        codes = {item["code"] for item in ITEMS} | {"cellular_standard"}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")

        accessed = timezone.localdate()
        documents = {}
        newly_filled = corrected = unchanged = cleared = 0

        def document_for(model):
            url = SOURCES[model]
            if url not in documents:
                documents[url], _ = SourceDocument.objects.update_or_create(
                    url=url,
                    document_version="Current official Ubiquiti Tech Specs page; accessed 2026-10-20",
                    defaults={
                        "brand": brand,
                        "product": None,
                        "document_type": SourceDocument.DocumentType.PRODUCT_PAGE,
                        "title": f"Ubiquiti {model} official Tech Specs",
                        "region": "Global",
                        "published_date": None,
                        "accessed_date": accessed,
                        "active": True,
                    },
                )
            return url, documents[url]

        for item in ITEMS:
            product = Product.objects.filter(brand=brand, model=item["model"], is_published=True).first()
            if not product:
                raise CommandError(f"Missing Ubiquiti product: {item['model']}")
            url, document = document_for(item["model"])
            definition = definitions[item["code"]]
            existing = ProductSpec.objects.filter(product=product, definition=definition).first()
            had = bool(existing and existing.value_status == ProductSpec.ValueStatus.PUBLISHED and (
                bool((existing.value_text or "").strip())
                or existing.value_number is not None
                or existing.value_boolean is not None
            ))
            if item["kind"] == "number":
                old_value = existing.value_number if had else None
                new_value = Decimal(str(item["value"]))
            elif item["kind"] == "boolean":
                old_value = existing.value_boolean if had else None
                new_value = bool(item["value"])
            else:
                old_value = existing.value_text if had else None
                new_value = str(item["value"])
            defaults = {
                "value_status": ProductSpec.ValueStatus.PUBLISHED,
                "value_text": "",
                "value_number": None,
                "value_boolean": None,
                "normalized_value": str(item["value"]),
                "unit": definition.unit,
                "raw_value": item["raw"],
                "source_url": url[:200],
                "source_note": "Manually verified from the current official Ubiquiti Tech Specs page.",
                "verified_date": accessed,
            }
            if item["kind"] == "number":
                defaults["value_number"] = new_value
            elif item["kind"] == "boolean":
                defaults["value_boolean"] = new_value
            else:
                defaults["value_text"] = new_value
            spec, _ = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
            if not had:
                newly_filled += 1
            elif old_value != new_value:
                corrected += 1
            else:
                unchanged += 1
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=document,
                source_location=item["location"],
                defaults={
                    "source_excerpt": item["raw"],
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        cellular_definition = definitions["cellular_standard"]
        for model in CLEAR_CELLULAR:
            product = Product.objects.get(brand=brand, model=model, is_published=True)
            url, document = document_for(model)
            spec = ProductSpec.objects.filter(product=product, definition=cellular_definition).first()
            if spec and spec.value_status == ProductSpec.ValueStatus.PUBLISHED and (spec.value_text or "").strip():
                cleared += 1
            spec, _ = ProductSpec.objects.update_or_create(
                product=product,
                definition=cellular_definition,
                defaults={
                    "value_status": ProductSpec.ValueStatus.UNKNOWN,
                    "value_text": "",
                    "value_number": None,
                    "value_boolean": None,
                    "normalized_value": "",
                    "unit": cellular_definition.unit,
                    "raw_value": "No integrated cellular modem is listed; the page only describes optional external UniFi LTE Backup support where applicable.",
                    "source_url": url[:200],
                    "source_note": "Cleared a false legacy cellular label after manual verification of the current official page.",
                    "verified_date": accessed,
                },
            )
            SpecEvidence.objects.update_or_create(
                product_spec=spec,
                source_document=document,
                source_location="Hardware / Networking; no integrated cellular interface listed",
                defaults={
                    "source_excerpt": "No integrated cellular modem is listed on the official hardware page.",
                    "evidence_level": SpecEvidence.EvidenceLevel.A,
                    "verified_at": timezone.now(),
                },
            )

        if options["dry_run"]:
            transaction.set_rollback(True)
        mode = "DRY RUN" if options["dry_run"] else "IMPORTED"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={len(ITEMS)} newly_filled={newly_filled} corrected={corrected} "
            f"unchanged={unchanged} false_cellular_values_cleared={cleared}"
        ))
