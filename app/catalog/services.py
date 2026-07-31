from dataclasses import dataclass

from django.db.models import Q

from catalog.models import (
    ComparisonTemplate,
    Product,
    ProductSpec,
    SpecDefinition,
    TemplateField,
)


@dataclass(frozen=True)
class ResolvedTemplateField:
    spec_definition: SpecDefinition
    priority: str
    required: bool
    display_group: str
    display_order: int
    highlight_relevance: bool


def ensure_product_spec_placeholders(product):
    definitions = SpecDefinition.objects.filter(
        Q(category=product.category) | Q(category__isnull=True),
        active=True,
    ).order_by("display_order", "display_name")
    existing_definition_ids = set(
        product.specs.values_list("definition_id", flat=True)
    )
    missing = [
        ProductSpec(
            product=product,
            definition=definition,
            value_status=ProductSpec.ValueStatus.UNKNOWN,
            unit=definition.unit,
        )
        for definition in definitions
        if definition.pk not in existing_definition_ids
    ]
    if missing:
        ProductSpec.objects.bulk_create(missing, ignore_conflicts=True)
    return len(missing)


def backfill_product_spec_placeholders(queryset=None):
    products = (
        queryset
        if queryset is not None
        else Product.objects.select_related("category").all()
    )
    return sum(ensure_product_spec_placeholders(product) for product in products)


def select_comparison_template(category, form_factor=""):
    templates = ComparisonTemplate.objects.filter(category=category, active=True)
    if form_factor:
        exact = templates.filter(form_factor=form_factor).order_by("-version", "-pk").first()
        if exact:
            return exact
    return templates.filter(form_factor="").order_by("-version", "-pk").first()


def template_fields(category, form_factor=""):
    template = select_comparison_template(category, form_factor)
    if template:
        return list(
            template.fields.select_related("spec_definition")
            .filter(spec_definition__active=True)
            .order_by("display_order", "spec_definition__display_name")
        )
    definitions = list(
        SpecDefinition.objects.filter(
            Q(category=category) | Q(category__isnull=True),
            active=True,
            is_core=True,
        ).order_by("display_order", "display_name")
    )
    return [
        ResolvedTemplateField(
            spec_definition=definition,
            priority=TemplateField.Priority.P0,
            required=True,
            display_group=definition.group,
            display_order=definition.display_order,
            highlight_relevance=True,
        )
        for definition in definitions
    ]


def template_definitions(category, form_factor=""):
    return [
        field.spec_definition
        for field in template_fields(category, form_factor)
    ]
