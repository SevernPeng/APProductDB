"""Catalog navigation from Omada's worldwide English switch listing (2026-09-14).

Source: https://www.omadanetworks.com/en/business-networking/all-omada-switch/
Marketing families intentionally remain separate from technical product types.
The current listing takes precedence over older product URL categories.
"""

from django.db.models import Q

from catalog.models import normalize_model_key


OFFICIAL_MODELS = {
    "aggregation": (
        "SX6632YF", "SX3032F", "SX3016F", "SX3008F", "SG5428XF", "SG3428XF",
    ),
    "access-max": ("SX3832MPP", "SX3832", "SX3206HPP"),
    "access-pro": (
        "SG3428XPP-M2", "SG3428X-M2", "SG3218XP-M2", "SG3210XHP-M2",
        "SG3210X-M2", "SG2210XMP-M2",
    ),
    "access-plus": (
        "SG6654XHP", "SG6654X", "SG6428XHP", "SG6428X", "SG5452XMPP",
        "SG5452X", "SG5428XMPP", "SG5428X", "SG3452XMPP", "SG3452XP",
        "SG3452X", "SG3428XMPP", "SG3428XMP", "SG3428X",
    ),
    "access": (
        "SG3452P", "SG3452", "SG3428MP", "SG3428", "SG3210", "TL-SG3210",
        "SG2452LP", "SG2428P", "SG2428LP", "SG2218P", "SG2218", "SG2016P",
        "SG2210MP", "SG2210P", "SG2206MP", "SG2008P", "SG2008", "SG2005P-PD",
    ),
}


def official_query(key):
    return Q(brand__name__iexact="TP-Link", model_key__in=[
        normalize_model_key(model) for model in OFFICIAL_MODELS[key]
    ])


def switch_subcategories():
    return (
        {"key": "campus", "title": "Campus", "query": Q(product_type__code__startswith="campus_")},
        *({"key": key, "title": title, "query": official_query(key)} for key, title in (
            ("aggregation", "Aggregation"), ("access-max", "Access Max"),
            ("access-pro", "Access Pro"), ("access-plus", "Access Plus"), ("access", "Access"),
        )),
        {"key": "agile", "title": "Agile", "query": Q(product_type__code__startswith="agile_")},
        {"key": "unmanaged", "title": "Unmanaged", "query": Q(product_type__code__in=("unmanaged", "unmanaged_poe", "unmanaged_non_poe"))},
        {"key": "industrial", "title": "Industrial", "query": Q(product_type__code__startswith="industrial_")},
        # Existing TP-Link Easy Smart products are not part of the current Omada
        # menu; keep them reachable without mislabeling them as cloud-managed Agile.
        {"key": "easy-smart", "title": "Easy Smart", "query": Q(product_type__code__in=("easy_smart", "easy_smart_poe", "easy_smart_non_poe"))},
        # Preserve bookmarked technical filters without showing them in the menu.
        {"key": "layer-3", "title": "Layer 3", "hidden": True, "query": Q(product_type__code__in=("l3", "l3_poe", "l3_non_poe"))},
        {"key": "layer-2", "title": "Layer 2", "hidden": True, "query": Q(product_type__code__in=("l2", "l2_plus", "l2_poe", "l2_non_poe"))},
    )
