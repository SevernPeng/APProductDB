from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


PRODUCTS = {
    "eKit AP362E": {
        "url": "https://e.huawei.com/marketingcloud/pep/asset/20000001/Material/e7d4025ee56d492abf593537050ffc4f/M3T1A590N1046402695198597363/%E5%8D%8E%E4%B8%BA%E5%9D%A4%E7%81%B5%20eKitEngine%20AP362E%E6%97%A0%E7%BA%BF%E6%8E%A5%E5%85%A5%E7%82%B9%E5%BD%A9%E9%A1%B5.pdf",
        "page": "产品规格 / 射频参数",
        "title": "华为坤灵 eKitEngine AP362E 无线接入点彩页",
        "values": {
            "max_clients": n(128, "最大接入用户；实际用户数随使用环境变化"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import the manually verified current Huawei eKitEngine AP362E client capacity."
    products = PRODUCTS
    document_version = "Current official Chinese datasheet (published 2025); accessed 2026-10-20"
    brand_name = "Huawei"
