"""Apply the saved Global catalog order without fetching websites during requests."""

import json
import re
from functools import lru_cache
from pathlib import Path

from django.db.models import Case, IntegerField, Q, Value, When

from .models import normalize_model_key


@lru_cache(maxsize=1)
def load_order():
    return json.loads(Path(__file__).with_name("official_product_order.json").read_text(encoding="utf-8"))["pages"]


def model_aliases(label):
    # Only split aliases explicitly printed by the manufacturer, not packaging
    # names such as '(2-pack)', and never remove meaningful model suffixes.
    aliases = re.fullmatch(r"([^()]+)\((TL-[^()]+)\)", label)
    return [normalize_model_key(v) for v in aliases.groups()] if aliases else [normalize_model_key(label)]


def model_ranks(family="", subcategory=""):
    pages = load_order()
    keys = []
    if family and subcategory:
        keys.append(f"{family}/{subcategory}")
    if family:
        keys.append(family)
        keys.extend(key for key in pages if key.startswith(family + "/"))
    else:
        keys.extend(key for key in pages if "/" not in key)
        keys.extend(key for key in pages if "/" in key)
    ranks = {}
    for key in keys:
        for label in pages.get(key, {}).get("models", []):
            rank = len(ranks)
            for alias in model_aliases(label):
                ranks.setdefault(alias, rank)
    return ranks


def order_products(queryset, family="", subcategory=""):
    ranks = model_ranks(family, subcategory)
    conditions = [When(Q(brand__slug="tp-link", model_key=model), then=Value(rank))
                  for model, rank in ranks.items()]
    return queryset.annotate(
        official_display_order=Case(*conditions, default=Value(len(ranks)), output_field=IntegerField()),
    ).order_by("official_display_order", "brand__name", "model", "region", "hardware_version", "pk")
