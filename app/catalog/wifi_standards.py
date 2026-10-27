"""Wi-Fi generation rules supplied for the Omada benchmark catalog."""
import re

from collections import defaultdict

from catalog.models import Product


def omada_wifi_standard(product):
    if product.category.slug != "access-point" or product.brand.slug != "tp-link":
        return None
    if "bridge" in product.model.casefold():
        return None
    match = re.match(r"^EAP([7621])\d", product.model, re.I)
    return {"7": "Wi-Fi 7", "6": "Wi-Fi 6", "2": "Wi-Fi 5", "1": "Wi-Fi 4"}.get(match[1]) if match else None


def standard_assignments():
    from comparison.models import ProductMatch

    own = {p.pk: omada_wifi_standard(p) for p in Product.objects.filter(
        brand__slug="tp-link", category__slug="access-point"
    ).select_related("category", "brand")}
    own = {pk: value for pk, value in own.items() if value}
    candidates = defaultdict(set)
    for anchor, competitor in ProductMatch.objects.filter(
        our_product_id__in=own, competitor_product__category__slug="access-point",
        competitor_product__brand__is_own_brand=False,
    ).exclude(status=ProductMatch.Status.REJECTED).values_list("our_product_id", "competitor_product_id"):
        candidates[competitor].add(own[anchor])
    conflicts = {pk: sorted(values) for pk, values in candidates.items() if len(values) != 1}
    return {**own, **{pk: next(iter(values)) for pk, values in candidates.items() if len(values) == 1}}, conflicts
