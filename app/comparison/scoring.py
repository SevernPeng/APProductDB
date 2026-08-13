import re
from decimal import Decimal

from catalog.models import ProductSpec, SpecDefinition, TemplateField
from catalog.product_types import product_type_code
from catalog.services import template_fields


DEFAULT_PRIORITY_WEIGHTS = {
    TemplateField.Priority.P0: Decimal("3"),
    TemplateField.Priority.P1: Decimal("2"),
    TemplateField.Priority.P2: Decimal("1"),
}


def _published_specs(product):
    cached = getattr(product, "_prefetched_objects_cache", {}).get("specs")
    specs = cached if cached is not None else product.specs.select_related("definition")
    return {
        spec.definition.code: spec
        for spec in specs
        if spec.value_status == ProductSpec.ValueStatus.PUBLISHED
    }


def _normalise_tokens(value):
    return set(re.findall(r"[a-z0-9]+", (value or "").casefold()))


def _field_similarity(left, right, definition):
    if left.value_number is not None and right.value_number is not None:
        left_value = abs(left.value_number)
        right_value = abs(right.value_number)
        largest = max(left_value, right_value)
        return Decimal("1") if largest == 0 else min(left_value, right_value) / largest
    if left.value_boolean is not None and right.value_boolean is not None:
        return Decimal("1") if left.value_boolean == right.value_boolean else Decimal("0")
    if definition.data_type in {SpecDefinition.DataType.TEXT, SpecDefinition.DataType.CHOICE}:
        left_tokens = _normalise_tokens(left.normalized_value or left.value_text)
        right_tokens = _normalise_tokens(right.normalized_value or right.value_text)
        if not left_tokens or not right_tokens:
            return None
        return Decimal(len(left_tokens & right_tokens)) / Decimal(len(left_tokens | right_tokens))
    return None


def calculate_benchmark_index(our_product, competitor_product, manual_score=None):
    """Calculate a 0-100 specification similarity score."""
    if our_product.category_id != competitor_product.category_id:
        return 0
    our_specs = _published_specs(our_product)
    competitor_specs = _published_specs(competitor_product)
    fields = template_fields(our_product.category, product_type_code(our_product))
    earned = Decimal("0")
    possible = Decimal("0")
    for field in fields:
        definition = field.spec_definition
        left = our_specs.get(definition.code)
        right = competitor_specs.get(definition.code)
        if not left or not right:
            continue
        similarity = _field_similarity(left, right, definition)
        if similarity is None:
            continue
        weight = getattr(field, "weight", None) or DEFAULT_PRIORITY_WEIGHTS.get(
            field.priority, Decimal("1")
        )
        possible += weight
        earned += similarity * weight
    if possible == 0:
        return int(manual_score) if manual_score is not None else 0
    return int((earned * Decimal("100") / possible).quantize(Decimal("1")))
