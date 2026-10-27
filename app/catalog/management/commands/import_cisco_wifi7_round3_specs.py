from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
)


URL_9172 = (
    "https://www.cisco.com/c/en/us/td/docs/wireless/access_point/"
    "technical-reference/cw9172-dg.html"
)
URL_9174 = (
    "https://www.cisco.com/c/en/us/td/docs/wireless/access_point/"
    "technical-reference/cw9174-deployment-guide.html"
)
URL_9176 = (
    "https://www.cisco.com/c/en/us/td/docs/wireless/access_point/"
    "technical-reference/cw9176-dg.html"
)
URL_9178 = (
    "https://www.cisco.com/c/en/us/td/docs/wireless/access_point/"
    "technical-reference/cw9178i-dg.html"
)


PRODUCTS = {
    "CW9172I": {
        "url": URL_9172,
        "page": "Technical specifications, Table 2: CW9172I At a Glance",
        "title": "Cisco Wireless CW9172 and CW9171 Access Point Deployment Guide",
        "values": {
            "max_clients": n(768, "Scale: 256 clients per radio; three client-serving radios in tri-radio mode (768 total)"),
        },
    },
    "CW9172H": {
        "url": URL_9172,
        "page": "Technical specifications, Table 2: CW9172I At a Glance",
        "title": "Cisco Wireless CW9172 and CW9171 Access Point Deployment Guide",
        "values": {
            "max_clients": n(768, "Scale: 256 clients per radio; three client-serving radios (768 total)"),
            "max_ssids": n(16, "SSIDs: 16 on each of 2.4 GHz, 5 GHz, and 6 GHz"),
        },
    },
    "CW9171I": {
        "url": URL_9172,
        "page": "Technical specifications, Table 2: CW9172I At a Glance",
        "title": "Cisco Wireless CW9172 and CW9171 Access Point Deployment Guide",
        "values": {
            "max_clients": n(512, "Scale: 256 clients per radio; two client-serving radios (512 total)"),
        },
    },
    "CW9174I": {
        "url": URL_9174,
        "page": "Technical Specifications, Table 2: CW9174x At a Glance",
        "title": "Cisco Wireless CW9174 Series Access Point Deployment Guide",
        "values": {
            "max_clients": n(768, "Scale: 768 clients (256 clients per radio)"),
        },
    },
    "CW9176I": {
        "url": URL_9176,
        "page": "Technical Specifications, Table 2: CW9176x At a Glance",
        "title": "Cisco Wireless CW9176 Access Point Deployment Guide",
        "values": {
            "max_clients": n(1200, "Scale: 1200 clients (400 clients per radio)"),
        },
    },
    "CW9178I": {
        "url": URL_9178,
        "page": "Technical Specifications, Table 2: CW9178I At a Glance",
        "title": "Cisco Wireless CW9178I Access Point Deployment Guide",
        "values": {
            "max_clients": n(1200, "Scale: 1200 clients (400 clients per radio)"),
        },
    },
}


class Command(VerifiedImportCommand):
    help = "Import exact Cisco Wi-Fi 7 AP client-scale and SSID specifications."
    products = PRODUCTS
    document_version = "Latest official Cisco deployment guides checked 2026-10-23"
    brand_name = "Cisco"
