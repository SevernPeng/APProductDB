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


PRODUCTS = {
    "DS-3E0106HP-E": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000008116/DS-3E0106HP-E_Datasheet_20240627.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 10/100 PoE RJ45; 2 x 10/100 RJ45"),
            "management_type": t("Unmanaged"),
            "switching_capacity_gbps": n(1.2),
            "packet_forwarding_rate_mpps": n(0.89),
            "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.096, "768 Kbits (0.096 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at/bt"),
            "poe_ports": n(4), "poe_budget_w": n(60),
            "max_poe_per_port_w": n(60, "Port 1: up to 60 W; ports 2-4: up to 30 W"),
            "extend_mode": b(True, "Ports 1-4: up to 300 m long-range PoE transmission"),
            "qos_support": t("VIP priority forwarding on ports 1-2"),
            "fanless": b(True, "Metal enclosure; fan-free design"),
            "installation": t("Desktop or wall mounting"),
            "max_power_consumption_w": n(65),
            "dimensions_mm": t("145 x 25.6 x 68.45 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0510HP-E": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000011311/DS-3E0510HP-E_Datasheet_20240319.pdf",
        "values": {
            "ethernet_interfaces": t("8 x 1GbE PoE RJ45; 1 x 1GbE RJ45; 1 x 1GbE SFP"),
            "management_type": t("Unmanaged"),
            "switching_capacity_gbps": n(20),
            "packet_forwarding_rate_mpps": n(14.88),
            "mac_address_table": t("4K"),
            "packet_buffer_mb": n(0.188, "1.5 Mbits (0.1875 MB decimal; stored to three decimal places)"),
            "flow_control": t("IEEE 802.3x flow control"),
            "poe_standard": t("IEEE 802.3af/at/bt"),
            "poe_ports": n(8), "poe_budget_w": n(110),
            "max_poe_per_port_w": n(90, "Ports 1-2: up to 90 W; ports 3-8: up to 30 W"),
            "extend_mode": b(True, "Ports 7-8: up to 300 m long-range transmission"),
            "port_isolation": b(True, "Port isolation on ports 1-8"),
            "poe_auto_recovery": b(True, "PoE watchdog automatically detects and restarts unresponsive cameras"),
            "fanless": b(True, "Metal enclosure; fan-free design"),
            "installation": t("Desktop mounting"),
            "transmission_method": t("Store-and-forward; wire-speed forwarding"),
            "max_power_consumption_w": n(120),
            "dimensions_mm": t("217.6 x 108.55 x 27.8 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0505HP-E": {
        "url": "https://www.hikvision.com/content/dam/hikvision/products/S000000001/S000000048/S000000068/S000000071/OFR000107/M000011310/Data_Sheet/DS-3E0505HP-E_Datasheet_20240315.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 1GbE PoE RJ45; 1 x 1GbE RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.125, "1 Mbit (0.125 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at/bt"), "poe_ports": n(4),
            "poe_budget_w": n(60), "max_poe_per_port_w": n(60, "Port 1: up to 60 W; ports 2-4: up to 30 W"),
            "extend_mode": b(True, "Ports 3-4: up to 300 m long-range transmission"),
            "port_isolation": b(True, "Port isolation on ports 1-4"),
            "poe_auto_recovery": b(True, "PoE watchdog automatically detects and restarts unresponsive cameras"),
            "fanless": b(True, "Metal enclosure; fan-free design"), "installation": t("Desktop mounting"),
            "max_power_consumption_w": n(65), "dimensions_mm": t("121 x 88.1 x 27.6 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0520HP-E": {
        "url": "https://us-legacy.hikvision.com/sites/default/files/data_sheet/baseline_datasheet_of_ds-3e0520hp-e_20-port_gigabit_unmanaged_hi-poe_switch_20190923.pdf",
        "values": {
            "ethernet_interfaces": t("12 x 1GbE PoE RJ45; 4 x 1GbE Hi-PoE RJ45; 2 x 1GbE RJ45; 2 x 1GbE SFP"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(40),
            "packet_forwarding_rate_mpps": n(29.76), "mac_address_table": t("8K"),
            "packet_buffer_mb": n(0.513, "4.1 Mbits (0.5125 MB decimal; stored to three decimal places)"),
            "flow_control": t("IEEE 802.3x flow control"),
            "poe_standard": t("Ports 1-4: IEEE 802.3af/at/bt; ports 5-16: IEEE 802.3af/at"),
            "poe_ports": n(16), "poe_budget_w": n(225),
            "max_poe_per_port_w": n(90, "Ports 1-4: up to 90 W; ports 5-16: up to 30 W"),
            "extend_mode": b(True, "Ports 13-16: up to 300 m at 10 Mbps"),
            "port_isolation": b(True, "Port isolation on ports 1-16"),
            "poe_auto_recovery": b(True, "PoE watchdog automatically detects and restarts unresponsive cameras"),
            "transmission_method": t("Store-and-forward switching"),
            "max_power_consumption_w": n(250), "dimensions_mm": t("440 x 220.8 x 44 mm"),
            "operating_temperature_c": t("-10 to 55 °C"),
        },
    },
    "DS-3E0310HP-E(C)": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000160946/DS-3E0310HP-EC_Datasheet_20241218.pdf",
        "values": {
            "ethernet_interfaces": t("8 x 10/100 PoE RJ45; 2 x 1GbE RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(5.6),
            "packet_forwarding_rate_mpps": n(4.17), "mac_address_table": t("4K"),
            "packet_buffer_mb": n(0.25, "2 Mbits (0.25 MB decimal)"),
            "poe_standard": t("Ports 1-2: IEEE 802.3af/at/bt; ports 3-8: IEEE 802.3af/at"),
            "poe_ports": n(8), "poe_budget_w": n(110),
            "max_poe_per_port_w": n(90, "Ports 1-2: up to 90 W; ports 3-8: up to 30 W"),
            "extend_mode": b(True, "Ports 1-8: up to 300 m long-range transmission"),
            "port_isolation": b(True, "Port isolation on ports 1-8"),
            "poe_auto_recovery": b(True, "PoE watchdog automatically detects and restarts unresponsive cameras"),
            "fanless": b(True, "Metal enclosure; fan-free design"), "installation": t("Desktop mounting"),
            "max_power_consumption_w": n(120), "dimensions_mm": t("217.6 x 27.6 x 108.5 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0505P-E/M": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000007570/DS-3E0505P-E_M_Datasheet_20240307.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 1GbE PoE RJ45; 1 x 1GbE RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.125, "1 Mbit (0.125 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(4),
            "poe_budget_w": n(35), "max_poe_per_port_w": n(30),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(38),
            "dimensions_mm": t("105 x 27.6 x 83.1 mm"), "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0505P-E": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000008118/DS-3E0505P-E_Datasheet_20240308.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 1GbE PoE RJ45; 1 x 1GbE RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.125, "1 Mbit (0.125 MB decimal)"),
            "flow_control": t("IEEE 802.3x flow control"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(4),
            "poe_budget_w": n(60), "max_poe_per_port_w": n(30),
            "fanless": b(True, "Metal enclosure; fan-free design"),
            "installation": t("Desktop or wall mounting"),
            "transmission_method": t("Store-and-forward switching"),
            "max_power_consumption_w": n(65), "dimensions_mm": t("105 x 27.6 x 83.1 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0510P-E/M": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000007571/DS-3E0510P-E_M_Datasheet_20240307.pdf",
        "values": {
            "ethernet_interfaces": t("8 x 1GbE PoE RJ45; 1 x 1GbE RJ45; 1 x 1GbE SFP"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(20),
            "packet_forwarding_rate_mpps": n(14.88), "mac_address_table": t("4K"),
            "packet_buffer_mb": n(0.188, "1.5 Mbits (0.1875 MB decimal; stored to three decimal places)"),
            "flow_control": t("IEEE 802.3x flow control"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(8),
            "poe_budget_w": n(58), "max_poe_per_port_w": n(30),
            "fanless": b(True, "Reliable fan-free design"),
            "installation": t("Desktop or wall mounting"),
            "transmission_method": t("Store-and-forward; wire-speed non-blocking forwarding"),
            "max_power_consumption_w": n(65), "dimensions_mm": t("217.6 x 27.8 x 108.55 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0526P-E/M": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000007573/DS-3E0526P-E_M_Datasheet_20240308.pdf",
        "values": {
            "ethernet_interfaces": t("24 x 1GbE PoE RJ45; 2 x 1GbE SFP"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(52),
            "packet_forwarding_rate_mpps": n(38.69), "mac_address_table": t("8K"),
            "packet_buffer_mb": n(0.513, "4.1 Mbits (0.5125 MB decimal; stored to three decimal places)"),
            "flow_control": t("IEEE 802.3x flow control"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(24),
            "poe_budget_w": n(225), "max_poe_per_port_w": n(30),
            "installation": t("19-inch rack mounting; mounting ears included"),
            "transmission_method": t("Store-and-forward; wire-speed forwarding"),
            "max_power_consumption_w": n(250), "dimensions_mm": t("440 x 44 x 220.8 mm"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "DS-3E0105P-E/M(C)": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000110625/DS-3E0105P-E_MC_Datasheet_20250110.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 10/100 PoE RJ45; 1 x 10/100 RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(1),
            "packet_forwarding_rate_mpps": n(0.744), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.096, "768 Kbits (0.096 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(4),
            "poe_budget_w": n(45), "max_poe_per_port_w": n(30),
            "extend_mode": b(True, "Ports 1-4: up to 300 m at 10 Mbps"),
            "fanless": b(True, "Metal enclosure; fan-free design"),
            "installation": t("Desktop or wall mounting"),
            "max_power_consumption_w": n(50), "dimensions_mm": t("121.1 x 27.6 x 83.1 mm"),
            "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0105P-E/M(B)": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000008108/DS-3E0105P-E_MB_Datasheet_20240307.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 10/100 PoE RJ45; 1 x 10/100 RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(1),
            "packet_forwarding_rate_mpps": n(0.74), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.096, "768 Kbits (0.096 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(4),
            "poe_budget_w": n(35), "max_poe_per_port_w": n(30),
            "extend_mode": b(True, "Ports 1-4: up to 300 m long-range transmission"),
            "qos_support": t("VIP priority forwarding for video traffic"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(38),
            "dimensions_mm": t("105 x 27.6 x 83.1 mm"), "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0109P-E/M(C)": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000160712/DS-3E0109P-E_MC_Datasheet_20250110.pdf",
        "values": {
            "ethernet_interfaces": t("8 x 10/100 PoE RJ45; 1 x 10/100 RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(1.8),
            "packet_forwarding_rate_mpps": n(1.34), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.125, "1 Mbit (0.125 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(8),
            "poe_budget_w": n(80), "max_poe_per_port_w": n(30),
            "extend_mode": b(True, "Ports 1-8: up to 300 m at 10 Mbps"),
            "qos_support": t("VIP priority forwarding for video traffic"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(86),
            "dimensions_mm": t("170 x 27.6 x 93.1 mm"), "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0318P-E/M(C)": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000065873/DS-3E0318P-E_MC_Datasheet_20240307.pdf",
        "values": {
            "ethernet_interfaces": t("16 x 10/100 PoE RJ45; 1 x 1GbE RJ45; 1 x 1GbE RJ45/SFP combo"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(7.2),
            "packet_forwarding_rate_mpps": n(5.36), "mac_address_table": t("8K"),
            "packet_buffer_mb": n(0.5, "4 Mbits (0.5 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(16),
            "poe_budget_w": n(130), "max_poe_per_port_w": n(30),
            "extend_mode": b(True, "Ports 9-16: up to 300 m long-range transmission"),
            "port_isolation": b(True), "poe_auto_recovery": b(True, "PoE watchdog"),
            "qos_support": t("VIP priority forwarding for video traffic"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(150),
            "dimensions_mm": t("335 x 44.5 x 175.8 mm"), "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "DS-3E0326P-E/M(C)": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000065874/DS-3E0326P-E_MC_Datasheet_20240307.pdf",
        "values": {
            "ethernet_interfaces": t("24 x 10/100 PoE RJ45; 1 x 1GbE RJ45; 1 x 1GbE RJ45/SFP combo"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(8.8),
            "packet_forwarding_rate_mpps": n(6.55), "mac_address_table": t("8K"),
            "packet_buffer_mb": n(0.5, "4 Mbits (0.5 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(24),
            "poe_budget_w": n(230), "max_poe_per_port_w": n(30),
            "extend_mode": b(True, "Ports 17-24: up to 300 m at 10 Mbps"),
            "port_isolation": b(True, "Port isolation on ports 1-24"),
            "poe_auto_recovery": b(True, "PoE watchdog on ports 1-24"),
            "qos_support": t("VIP priority forwarding for video traffic"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(250),
            "dimensions_mm": t("335 x 44.5 x 226 mm"), "operating_temperature_c": t("0 to 45 °C"),
        },
    },
    "DS-3E0505P-E/M(B)": {
        "url": "https://assets.hikvision.com/prd/normal/all/doc/m000159393/DS-3E0505P-E_MB_Datasheet_20241101.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 1GbE PoE RJ45; 1 x 1GbE RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(10),
            "packet_forwarding_rate_mpps": n(7.44), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.125, "1 Mbit (0.125 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(4),
            "poe_budget_w": n(45), "max_poe_per_port_w": n(30),
            "fanless": b(True, "Silent fanless design"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(50),
            "dimensions_mm": t("121.1 x 27.6 x 83.1 mm"), "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0106P-E/M": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000019321/DS-3E0106P-E_M_Datasheet_20240307.pdf",
        "values": {
            "ethernet_interfaces": t("4 x 10/100 PoE RJ45; 2 x 10/100 RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(1.2),
            "packet_forwarding_rate_mpps": n(0.89), "mac_address_table": t("2K"),
            "packet_buffer_mb": n(0.096, "768 Kbits (0.096 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(4),
            "poe_budget_w": n(35), "max_poe_per_port_w": n(30),
            "extend_mode": b(True, "Ports 1-4: up to 300 m long-range transmission"),
            "qos_support": t("VIP priority forwarding on ports 1-2"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(30),
            "dimensions_mm": t("145 x 68.45 x 25.6 mm"), "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0310HP-E": {
        "url": "https://assets.hikvision.com/prd/public/all/doc/m000008117/DS-3E0310HP-E_Datasheet_20240308.pdf",
        "values": {
            "ethernet_interfaces": t("8 x 10/100 PoE RJ45; 2 x 1GbE RJ45"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(5.6),
            "packet_forwarding_rate_mpps": n(4.17), "mac_address_table": t("8K"),
            "packet_buffer_mb": n(0.5, "4 Mbits (0.5 MB decimal)"),
            "poe_standard": t("IEEE 802.3af/at/bt"), "poe_ports": n(8),
            "poe_budget_w": n(110), "max_poe_per_port_w": n(90, "Port 1: up to 90 W; ports 2-8: up to 30 W"),
            "extend_mode": b(True, "Ports 1-8: up to 300 m long-range transmission"),
            "qos_support": t("VIP priority forwarding on ports 1-8"),
            "fanless": b(True, "Metal enclosure; fan-free design"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(120),
            "dimensions_mm": t("217.6 x 27.8 x 103.55 mm"), "operating_temperature_c": t("0 to 40 °C"),
        },
    },
    "DS-3E0510P-E": {
        "url": "https://us-legacy.hikvision.com/sites/default/files/manual/qrg_switch_2022_updated_flyer.pdf",
        "values": {
            "ethernet_interfaces": t("8 x 1GbE PoE RJ45; 1 x 1GbE RJ45; 1 x 1GbE SFP"),
            "management_type": t("Unmanaged"), "switching_capacity_gbps": n(20),
            "packet_forwarding_rate_mpps": n(14.88), "mac_address_table": t("4K"),
            "packet_buffer_mb": n(0.188, "1.5 Mbits (0.1875 MB decimal; stored to three decimal places)"),
            "flow_control": t("IEEE 802.3x flow control"),
            "poe_standard": t("IEEE 802.3af/at"), "poe_ports": n(8),
            "poe_budget_w": n(110), "max_poe_per_port_w": n(30),
            "transmission_method": t("Store-and-forward switching"),
            "installation": t("Desktop or wall mounting"), "max_power_consumption_w": n(120),
            "dimensions_mm": t("217.6 x 27.8 x 108.55 mm"), "operating_temperature_c": t("-10 to 55 °C"),
        },
    },
}


class Command(BaseCommand):
    help = "Import manually verified Hikvision unmanaged-switch specifications (round 2)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        brand = Brand.objects.filter(name="Hikvision").first()
        if not brand:
            raise CommandError("Missing brand: Hikvision")
        codes = {code for item in PRODUCTS.values() for code in item["values"]}
        definitions = {d.code: d for d in SpecDefinition.objects.filter(code__in=codes)}
        if missing := codes - definitions.keys():
            raise CommandError(f"Missing definitions: {', '.join(sorted(missing))}")
        accessed = timezone.localdate()
        written = newly_filled = corrected = unchanged = 0
        per_model = []
        for model, item in PRODUCTS.items():
            product = Product.objects.filter(brand=brand, model=model, is_published=True).first()
            if not product:
                raise CommandError(f"Missing Hikvision product: {model}")
            document, _ = SourceDocument.objects.update_or_create(
                url=item["url"],
                document_version="Current official exact-model datasheet; accessed 2026-10-15",
                defaults={
                    "brand": brand, "product": product,
                    "document_type": SourceDocument.DocumentType.DATASHEET,
                    "title": f"Hikvision {model} official datasheet",
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
                defaults = {
                    "value_status": ProductSpec.ValueStatus.PUBLISHED,
                    "value_text": "", "value_number": None, "value_boolean": None,
                    "normalized_value": str(value), "unit": definition.unit, "raw_value": raw,
                    "source_url": item["url"][:200],
                    "source_note": "Manually verified from Hikvision's official exact-model datasheet.",
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
                    product_spec=spec, source_document=document,
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
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: spec_values={written} newly_filled={newly_filled} corrected={corrected} unchanged={unchanged} models={len(PRODUCTS)}"
        ))
        self.stdout.write("; ".join(per_model))
