from catalog.management.commands.import_aruba_ap_priority_round3_specs import (
    Command as VerifiedImportCommand,
    n,
    t,
)


URL_1830 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Networking%20Instant%20On%20Switch%20Series%201830%20Data%20Sheet-a00119988enw.pdf?deepLink=&form=false&hf=regular&id=a00119988enw&isFutureVersion=true&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=10"
URL_1930 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Networking%20Instant%20On%20Switch%201930%20QuickSpecs-a50000620enw.pdf?deepLink=&form=false&hf=regular&id=a50000620enw&isFutureVersion=true&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=12"
URL_1960 = "https://www.hpe.com/psnow/downloadDoc/HPE%20Networking%20Instant%20On%20Switch%201960%20QuickSpecs-a50002593enw.pdf?deepLink=&form=false&hf=regular&id=a50002593enw&isFutureVersion=true&originalObjectName=&prelaunchSection=&preview=false&print=&r=&section=&softrollSection=&ver=12"


def product(url, title, page, watts, raw_watts, supply):
    return {
        "url": url,
        "title": title,
        "page": page,
        "values": {
            # The schema stores one scalar maximum.  Where HPE publishes two
            # input-voltage figures, retain the complete statement in raw_value
            # and normalize to the larger of the two ratings.
            "max_power_consumption_w": n(watts, raw_watts),
            "power_supply": t(supply),
        },
    }


TITLE_1830 = "HPE Networking Instant On Switch Series 1830 Data Sheet, version 10"
TITLE_1930 = "HPE Networking Instant On Switch 1930 QuickSpecs, version 12"
TITLE_1960 = "HPE Networking Instant On Switch 1960 QuickSpecs, version 12"


PRODUCTS = {
    "JL810A": product(URL_1830, TITLE_1830, "Technical specifications, electrical characteristics table, page 9", 8.09, "Maximum power rating: 100-127V: 8.09W; 200-220V: 8.05W", "External power adapter (included)"),
    "JL811A": product(URL_1830, TITLE_1830, "Technical specifications, electrical characteristics table, page 9", 86.07, "Maximum power rating: 100-127V: 86.07W; 200-220V: 83.67W", "Internal power supply"),
    "JL812A": product(URL_1830, TITLE_1830, "Technical specifications, electrical characteristics table, page 9", 19.1, "Maximum power rating: 100-127V: 19.1W; 200-220V: 19W", "Internal power supply"),
    "JL813A": product(URL_1830, TITLE_1830, "Technical specifications, electrical characteristics table, page 10", 244.6, "Maximum power rating: 100-127V: 244.6W; 200-220V: 237.2W", "Internal power supply"),
    "JL814A": product(URL_1830, TITLE_1830, "Technical specifications, electrical characteristics table, page 10", 40.2, "Maximum power rating: 100-127V: 40.2W; 200-220V: 40W", "Internal power supply"),
    "JL815A": product(URL_1830, TITLE_1830, "Technical specifications, electrical characteristics table, page 10", 462.5, "Maximum power rating: 100-127V: 462.5W; 200-220V: 452.5W", "Internal power supply"),
    "JL680A": product(URL_1930, TITLE_1930, "Technical Specifications - JL680A", 11.0, "Maximum power rating: 11.0 W", "External power adapter (included)"),
    "JL681A": product(URL_1930, TITLE_1930, "Technical Specifications - JL681A", 150.2, "Maximum power rating: 150.2 W", "Internal power supply"),
    "JL682A": product(URL_1930, TITLE_1930, "Technical Specifications - JL682A", 22.6, "Maximum power rating: 22.6 W", "Internal power supply"),
    "JL684B": product(URL_1930, TITLE_1930, "Technical Specifications - JL684B", 440.4, "Maximum power rating: 440.4 W", "Internal power supply"),
    "JL685A": product(URL_1930, TITLE_1930, "Technical Specifications - JL685A", 36.9, "Maximum power rating: 36.9 W", "Internal power supply"),
    "JL686B": product(URL_1930, TITLE_1930, "Technical Specifications - JL686B", 465.6, "Maximum power rating: 465.6 W", "Internal power supply"),
    "JL806A": product(URL_1960, TITLE_1960, "Technical Specifications - JL806A", 80, "Maximum power rating: 100-127V: 60W; 200-220V: 80W", "Internal power supply"),
    "JL807A": product(URL_1960, TITLE_1960, "Technical Specifications - JL807A", 500, "Maximum power rating: 100-127V: 500W; 200-220V: 480W", "Internal power supply"),
    "JL808A": product(URL_1960, TITLE_1960, "Technical Specifications - JL808A", 120, "Maximum power rating: 100-127V: 110W; 200-220V: 120W", "Internal power supply"),
    "JL809A": product(URL_1960, TITLE_1960, "Technical Specifications - JL809A", 790, "Maximum power rating: 100-127V: 790W; 200-220V: 760W", "Internal power supply"),
}


class Command(VerifiedImportCommand):
    help = "Import current official Instant On 1830, 1930, and 1960 switch power specifications."
    products = PRODUCTS
    document_version = "Current official HPE datasheet/QuickSpecs revisions; accessed 2026-10-21"
    brand_name = "Instant On"
