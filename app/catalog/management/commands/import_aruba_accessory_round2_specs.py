from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as ArubaImportCommand,
    n,
    t,
)


URL_1G_SX = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%201G%20SFP%20LC%20SX%20"
    "500m%20OM2%20MMF%20Transceiver%20data%20sheet-PSN1010420422SEEN.pdf?lc=EN&oid=1010420422"
)
URL_1G_LX = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%201G%20SFP%20LC%20LX%20"
    "10km%20SMF%20Transceiver%20data%20sheet-PSN1010420526FIEN.pdf?lc=EN&oid=1010420526"
)
URL_10G_SR = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%2010G%20SFP%2B%20LC%20SR%20"
    "300m%20OM3%20MMF%20Transceiver%20data%20sheet-PSN1010420410NGEN.pdf?lc=EN&oid=1010420410"
)
URL_10G_LR = (
    "https://www.hpe.com/asia_pac/en/product-catalog/options/pip.specifications."
    "hpe-aruba-networking-10g-sfpplus-lc-lr-10km-smf-transceiver.1011300027.html"
)
URL_25G_SR = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%2025G%20SFP28%20LC%20SR%20"
    "100m%20MMF%20Transceiver%20data%20sheet-PSN1011181846AUEN.pdf?lc=EN&oid=1011181846"
)
URL_25G_LR = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%2025G%20SFP28%20LC%20LR%20"
    "10km%20SMF%20Transceiver%20data%20sheet-PSN1011181847AEEN.pdf?lc=EN&oid=1011181847"
)
URL_100G_SR4 = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%20100G%20QSFP28%20MPO%20SR4%20"
    "100m%2012-fiber%20MPO%20OM3%20MMF%20Transceiver%20data%20sheet-PSN1010137501CAEN.pdf"
    "?lc=EN&oid=1010137501"
)
URL_100G_DAC = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%20100G%20QSFP28%20to%20QSFP28%20"
    "1m%20Direct%20Attach%20Copper%20Cable%20data%20sheet-PSN1011600008NGEN.pdf?lc=EN&oid=1011600008"
)
URL_10G_DAC_1M = (
    "https://www.hpe.com/psnow/generateDDS/HPE%20Aruba%20Networking%2010G%20SFP%2B%20to%20SFP%2B%20"
    "1m%20Direct%20Attach%20Copper%20Cable%20data%20sheet-PSN1010420527HREN.pdf?lc=EN&oid=1010420527"
)
URL_DAC_GUIDE = (
    "https://arubanetworking.hpe.com/techdocs/Switches/xcvrs/xcvr_guide/Content/"
    "GUID-DDC75F60-4DFE-45DA-9C9A-ACBCFF075F88.html"
)


def item(url, title, dimensions):
    return {
        "url": url,
        "page": "Technical specifications - Product dimensions",
        "title": title,
        "values": {"dimensions_mm": t(dimensions)},
    }


PRODUCTS = {
    "J4858D": item(URL_1G_SX, "HPE Aruba Networking J4858D Data Sheet", "15 x 56 x 13 mm"),
    "J4859D": item(URL_1G_LX, "HPE Aruba Networking J4859D Data Sheet", "15 x 56 x 13 mm"),
    "J9150D": item(URL_10G_SR, "HPE Aruba Networking J9150D Data Sheet", "15 x 56 x 13 mm"),
    "J9151E": item(URL_10G_LR, "HPE Aruba Networking J9151E Product Specifications", "15 x 56 x 13 mm"),
    "JL484A": item(URL_25G_SR, "HPE Aruba Networking JL484A Data Sheet", "13 x 15 x 56 mm"),
    "JL486A": item(URL_25G_LR, "HPE Aruba Networking JL486A Data Sheet", "13 x 15 x 56 mm"),
    "JL309A": item(URL_100G_SR4, "HPE Aruba Networking JL309A Data Sheet", "18 x 132 x 8 mm"),
    "R0Z25A": item(URL_100G_DAC, "HPE Aruba Networking R0Z25A Data Sheet", "25 x 300 x 330 mm"),
    "J9281D": {
        "url": URL_10G_DAC_1M,
        "page": "Technical specifications - Product dimensions",
        "title": "HPE Aruba Networking J9281D Data Sheet",
        "values": {
            "dimensions_mm": t("305 x 305 x 13 mm", "Product dimensions: 30.5 x 30.5 x 1.3 cm"),
            "operating_temperature_c": t("0 to 70 °C", "Commercial temperature rating: 0 to 70 °C"),
        },
    },
    "J9283D": {
        "url": URL_DAC_GUIDE,
        "page": "10G SFP+ direct attach copper cable specifications",
        "title": "HPE Aruba Networking AOS-S and AOS-CX Transceiver Guide",
        "values": {
            "operating_temperature_c": t("0 to 70 °C", "Commercial temperature rating: 0 to 70 °C"),
            "max_power_consumption_w": n(0.2, "Required power: 0.1 W per end; 0.2 W total"),
        },
    },
}


class Command(ArubaImportCommand):
    help = "Import official Aruba transceiver/DAC dimensions, temperature and power gaps."
    products = PRODUCTS
    document_version = "Latest official HPE product data sheets and transceiver guide; checked 2026-10-23"
    brand_name = "Aruba"
