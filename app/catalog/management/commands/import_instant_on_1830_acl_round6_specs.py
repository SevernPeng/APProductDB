from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    t,
)


URL = (
    "https://community.instant-on.hpe.com/blogs/so93/2026/08/03/"
    "instant-on-1840-1940-annoucement"
)


PRODUCTS = {
    model: {
        "url": URL,
        "page": "Additional security for the Instant On 1840",
        "title": "HPE Networking Instant On 1840 and 1940 announcement",
        "values": {
            "acl_security": t(
                "Not supported",
                "ACLs are supported on the 1840 switches and were previously unavailable on Switch Series 1830",
            ),
        },
    }
    for model in ("JL810A", "JL811A", "JL812A", "JL813A", "JL814A", "JL815A")
}


class Command(VerifiedImportCommand):
    help = "Record the official lack of ACL support on Instant On 1830 switches."
    products = PRODUCTS
    document_version = "Official HPE Instant On announcement, 2026-08-03; accessed 2026-10-27"
    brand_name = "Instant On"
