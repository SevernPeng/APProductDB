from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


PRODUCTS = {
    "RG-NBR6215-E": {
        "url": "https://image.ruijie.com.cn/Upload/Article/dc77b9b2-a210-43ff-a63d-df75528923fb/%E9%94%90%E6%8D%B7SMB%20NBR-E%E8%B7%AF%E7%94%B1%E5%99%A8%E7%B3%BB%E5%88%97%E5%AE%9E%E6%96%BD%E4%B8%80%E6%9C%AC%E9%80%9A%EF%BC%88V2.3%EF%BC%89/%E9%94%90%E6%8D%B7SMB%20NBR-E%E8%B7%AF%E7%94%B1%E5%99%A8%E7%B3%BB%E5%88%97%E5%AE%9E%E6%96%BD%E4%B8%80%E6%9C%AC%E9%80%9A%EF%BC%88V2.3%EF%BC%89/2018091820581500004.html",
        "page": "RG-NBR6215-E hardware specifications",
        "title": "Ruijie SMB NBR-E router series implementation guide V2.3 - RG-NBR6215-E hardware",
        "values": {
            "ethernet_interfaces": t("8 x 10/100/1000BASE-T configurable WAN/LAN ports; 1 x configurable 10G/1G SFP+/SFP port; 1 x configurable 1G SFP port; 1 x management port; 1 x console port"),
            "lan_interfaces": t("6 x Gigabit RJ45 ports default to LAN; five of them are configurable as WAN; SFP+/SFP port defaults to LAN and is configurable as WAN"),
            "wan_interfaces": t("2 x Gigabit RJ45 ports default to WAN, one configurable as LAN; 1 x Gigabit SFP port defaults to WAN and is configurable as LAN"),
            "uplink_interfaces": t("8 x configurable Gigabit RJ45; 1 x configurable 10G/1G SFP+/SFP; 1 x configurable Gigabit SFP"),
            "usb_interfaces": t("2 x USB"),
            "operating_temperature_c": t("0 to 45 °C"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified RG-NBR6215-E hardware specifications from the official Ruijie implementation guide."
    products = PRODUCTS
    document_version = "Official NBR-E implementation guide V2.3; accessed 2026-10-19"
    brand_name = "Ruijie"
