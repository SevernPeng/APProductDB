from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    b,
    t,
)


URL = (
    "https://www.hpe.com/psnow/downloadDoc/Aruba%202540%20Switch%20Series-c05278966.pdf?"
    "form=false&hf=slim&id=c05278966.pdf&isFutureVersion=true&preview=false&servePdfFile=true&ver=14"
)
TITLE = "Aruba 2540 Switch Series QuickSpecs, version 14"


def shared_values():
    return {
        "cpu": t("Dual-core ARM Cortex-A9 at 1016 MHz"),
        "dram_memory": t("1 GB DDR3 SDRAM"),
        "flash_memory": t("4 GB eMMC; dual flash images supported"),
        "console_interfaces": t("1 dual-personality RJ45 or USB micro-B serial console port"),
        "mld_snooping": b(True, "RFC 2710 MLDv1, RFC 3810 MLDv2 and IGMP/MLD snooping supported"),
        "fanless": b(False, "Technical table specifies acoustic output and side-to-side airflow"),
        "fan_design": t("Side-to-side airflow"),
        "operating_temperature_c": t("0 to 45 °C up to 5,000 ft; 0 to 40 °C up to 10,000 ft"),
    }


def values(**specific):
    result = shared_values()
    result.update(specific)
    return result


PRODUCTS = {
    "2540 24G 4SFP+ Switch": {
        "url": URL,
        "page": "pp. 13-14, JL354A technical specifications; pp. 2-4 standard features",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("24 x 10/100/1000BASE-T RJ45 and 4 x 1/10GbE SFP+"),
            uplink_interfaces=t("4 x 1/10GbE SFP+"),
        ),
    },
    "2540 48G 4SFP+ Switch": {
        "url": URL,
        "page": "pp. 14-15, JL355A technical specifications; pp. 2-4 standard features",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("48 x 10/100/1000BASE-T RJ45 and 4 x 1/10GbE SFP+"),
            uplink_interfaces=t("4 x 1/10GbE SFP+"),
        ),
    },
    "2540 24G PoE+ 4SFP+ Switch": {
        "url": URL,
        "page": "pp. 15-16, JL356A technical specifications; pp. 2-4 standard features",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("24 x 10/100/1000BASE-T PoE+ RJ45 and 4 x 1/10GbE SFP+"),
            uplink_interfaces=t("4 x 1/10GbE SFP+"),
        ),
    },
    "2540 48G PoE+ 4SFP+ Switch": {
        "url": URL,
        "page": "pp. 16-17, JL357A technical specifications; pp. 2-4 standard features",
        "title": TITLE,
        "values": values(
            ethernet_interfaces=t("48 x 10/100/1000BASE-T PoE+ RJ45 and 4 x 1/10GbE SFP+"),
            uplink_interfaces=t("4 x 1/10GbE SFP+"),
        ),
    },
}


class Command(ArubaImportCommand):
    help = "Import manually verified Aruba 2540 switch specifications."
    products = PRODUCTS
    document_version = "Official retired Aruba QuickSpecs version 14; accessed 2026-10-16"
