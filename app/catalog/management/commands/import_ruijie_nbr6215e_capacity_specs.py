from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


PRODUCTS = {
    "RG-NBR6215-E": {
        "url": "https://www-file.ruijie.com.cn/Fu/Article/dc77b9b2-a210-43ff-a63d-df75528923fb/v1/%E9%94%90%E6%8D%B7SMB%20NBR-E%E8%B7%AF%E7%94%B1%E5%99%A8%E7%B3%BB%E5%88%97%E5%AE%9E%E6%96%BD%E4%B8%80%E6%9C%AC%E9%80%9A%EF%BC%88V2.3%EF%BC%89/%E9%94%90%E6%8D%B7SMB%20NBR-E%E8%B7%AF%E7%94%B1%E5%99%A8%E7%B3%BB%E5%88%97%E5%AE%9E%E6%96%BD%E4%B8%80%E6%9C%AC%E9%80%9A%EF%BC%88V2.3%EF%BC%89/2018091820581500003.html",
        "page": "Product parameter tables: recommended capacity and VPN sessions",
        "title": "Ruijie SMB NBR-E router series implementation guide V2.3 - product parameters",
        "values": {
            "concurrent_sessions": n(600000),
            "vpn_tunnels": n(1000, "Maximum without auditing: SSL VPN 1000; IPsec/PPTP/L2TP VPN 1000. With auditing: 500"),
            "vpn_protocols": t("SSL VPN; IPsec VPN; PPTP VPN; L2TP VPN"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import manually verified RG-NBR6215-E capacity and VPN specifications from official Ruijie parameter tables."
    products = PRODUCTS
    document_version = "Official NBR-E implementation guide V2.3 product parameters; accessed 2026-10-19"
    brand_name = "Ruijie"
