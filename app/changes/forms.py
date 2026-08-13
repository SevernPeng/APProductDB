from django import forms
from django.core.exceptions import ValidationError

from catalog.models import Product
from catalog.product_types import product_type_code
from catalog.services import template_fields
from comparison.models import ProductMatch

from .services import (
    MATCH_DELETE_FIELD,
    build_target_options,
    display_snapshot,
    parse_proposed_value,
    resolve_target,
    snapshot_for_selection,
)
from .validators import validate_change_attachment


class ProductPageEditForm(forms.Form):
    """One-page editor for the content displayed on a product detail page."""

    PRODUCT_FIELD_NAMES = (
        "region",
        "hardware_version",
        "sku",
        "lifecycle_status",
        "official_url",
        "datasheet_url",
        "launch_date",
        "notes",
        "ap_type",
        "wifi_standard",
    )

    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.edit_items = []

        product_options = {
            option["key"]: option for option in build_target_options(product)
            if option["key"].startswith("product:")
        }
        for field_name in self.PRODUCT_FIELD_NAMES:
            key = f"product:{field_name}"
            option = product_options.get(key)
            if not option:
                continue
            selection = resolve_target(product, key)
            form_name = f"product_{field_name}"
            field = forms.CharField(label=option["label"], required=False)
            if field_name == "lifecycle_status":
                field = forms.ChoiceField(
                    label=option["label"],
                    choices=Product.LifecycleStatus.choices,
                )
            elif field_name == "ap_type":
                field = forms.ChoiceField(
                    label=option["label"],
                    choices=Product.APType.choices,
                )
            elif field_name in {"official_url", "datasheet_url"}:
                field = forms.URLField(label=option["label"], required=False)
            elif field_name == "launch_date":
                field = forms.DateField(
                    label=option["label"],
                    required=False,
                    widget=forms.DateInput(attrs={"type": "date"}),
                )
            elif field_name == "notes":
                field.widget = forms.Textarea(attrs={"rows": 2})
            self.fields[form_name] = field
            self.initial[form_name] = self._raw_initial(selection)
            self.edit_items.append(
                {"name": form_name, "group": "Product Information", "selection": selection}
            )

        displayed_definitions = [
            item.spec_definition
            for item in template_fields(product.category, product_type_code(product))
        ]
        specs = {
            spec.definition_id: spec
            for spec in product.specs.filter(
                definition__in=displayed_definitions,
                definition__active=True,
            ).select_related("definition")
        }
        for definition in displayed_definitions:
            spec = specs.get(definition.pk)
            if not spec:
                continue
            selection = resolve_target(product, f"spec:{spec.pk}")
            form_name = f"spec_{spec.pk}"
            if definition.data_type == "boolean":
                field = forms.ChoiceField(
                    label=definition.display_name,
                    required=False,
                    choices=(("", "Unknown"), ("Yes", "Yes"), ("No", "No")),
                )
            elif definition.data_type == "integer":
                field = forms.IntegerField(
                    label=definition.display_name,
                    required=False,
                    widget=forms.NumberInput(attrs={"step": "1"}),
                )
            elif definition.data_type == "decimal":
                field = forms.DecimalField(
                    label=definition.display_name,
                    required=False,
                    decimal_places=3,
                    widget=forms.NumberInput(attrs={"step": "any"}),
                )
            else:
                field = forms.CharField(label=definition.display_name, required=False)
            self.fields[form_name] = field
            self.initial[form_name] = self._raw_initial(selection)
            self.edit_items.append(
                {
                    "name": form_name,
                    "group": definition.group or "Specifications",
                    "unit": definition.unit,
                    "selection": selection,
                }
            )

        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "form-select" if isinstance(field.widget, forms.Select) else "form-control",
            )

    @staticmethod
    def _raw_initial(selection):
        target = selection["target"]
        if selection["request_type"] == "spec":
            if target.value_status != target.ValueStatus.PUBLISHED:
                return ""
            if target.value_boolean is not None:
                return "Yes" if target.value_boolean else "No"
            if target.value_number is not None:
                if target.definition.data_type == "integer":
                    return int(target.value_number)
                return target.value_number
            return target.value_text
        value = getattr(target, selection["field_name"])
        return value.isoformat() if hasattr(value, "isoformat") else value

    def changed_values(self):
        changes = []
        for item in self.edit_items:
            name = item["name"]
            selection = item["selection"]
            value = self.cleaned_data[name]
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            raw_value = "" if value is None else str(value)
            initial_value = self.initial.get(name)
            if hasattr(initial_value, "isoformat"):
                initial_value = initial_value.isoformat()
            initial_raw = "" if initial_value is None else str(initial_value)
            if raw_value == initial_raw:
                continue
            old_value = snapshot_for_selection(selection)
            if selection["request_type"] == "spec" and not raw_value.strip():
                proposed = {"value_status": "unknown"}
            else:
                proposed = parse_proposed_value(selection, raw_value)
            if old_value != proposed:
                changes.append((selection, old_value, proposed))
        return changes


class ChangeSubmissionForm(forms.Form):
    proposed_value = forms.CharField(
        label="Proposed Value",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    reason = forms.CharField(
        label="Reason",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    source_url = forms.URLField(label="Official Source URL", required=False)
    attachment = forms.FileField(
        label="Evidence Attachment",
        required=False,
        validators=[validate_change_attachment],
        help_text="PDF, PNG, JPG, JPEG, or XLSX; up to 10 MB.",
    )

    def __init__(self, *args, selection, **kwargs):
        super().__init__(*args, **kwargs)
        self.selection = selection
        field_name = selection["field_name"]
        target = selection["target"]
        if field_name == MATCH_DELETE_FIELD:
            self.fields["proposed_value"].widget = forms.HiddenInput()
        elif selection["request_type"] == "spec" and target.definition.data_type == "integer":
            self.fields["proposed_value"].widget = forms.NumberInput(
                attrs={"step": "1"},
            )
        elif selection["request_type"] == "spec" and target.definition.data_type == "boolean":
            self.fields["proposed_value"].widget = forms.Select(
                choices=(("Yes", "Yes"), ("No", "No")),
            )
        elif field_name == "ap_type":
            self.fields["proposed_value"].widget = forms.Select(
                choices=Product.APType.choices,
            )
        elif field_name == "lifecycle_status":
            self.fields["proposed_value"].widget = forms.Select(
                choices=Product.LifecycleStatus.choices,
            )
        elif field_name == "match_type":
            self.fields["proposed_value"].widget = forms.Select(
                choices=ProductMatch.MatchType.choices,
            )
        elif field_name == "match_level":
            self.fields["proposed_value"].widget = forms.Select(
                choices=ProductMatch.MatchLevel.choices,
            )
        elif field_name == "status":
            self.fields["proposed_value"].widget = forms.Select(
                choices=ProductMatch.Status.choices,
            )
        elif field_name in {"launch_date", "valid_from", "valid_to"}:
            self.fields["proposed_value"].widget = forms.DateInput(
                attrs={"type": "date"},
            )
        elif field_name in {"match_score", "confidence"}:
            self.fields["proposed_value"].widget = forms.NumberInput(
                attrs={"min": 0, "max": 100},
            )
        elif field_name == "rank":
            self.fields["proposed_value"].widget = forms.NumberInput(
                attrs={"min": 0},
            )
        if field_name != MATCH_DELETE_FIELD and not self.is_bound:
            current_value = display_snapshot(snapshot_for_selection(selection))
            if current_value != "Unknown":
                self.fields["proposed_value"].initial = current_value
        for field in self.fields.values():
            css_class = "form-select" if isinstance(
                field.widget,
                forms.Select,
            ) else "form-control"
            field.widget.attrs.setdefault("class", css_class)

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        try:
            proposed = parse_proposed_value(
                self.selection, cleaned.get("proposed_value", "")
            )
        except ValidationError as exc:
            self.add_error("proposed_value", exc)
            return cleaned
        old_value = snapshot_for_selection(self.selection)
        if old_value == proposed:
            self.add_error("proposed_value", "The proposed value must differ from the current value.")
        if (
            self.selection["request_type"] == "spec"
            and not cleaned.get("source_url")
            and not cleaned.get("attachment")
        ):
            raise ValidationError("Provide an official source URL or evidence attachment.")
        cleaned["old_value"] = old_value
        cleaned["parsed_proposed_value"] = proposed
        return cleaned


class MatchAddForm(forms.Form):
    competitor_product = forms.ModelChoiceField(
        label="Competitor",
        queryset=Product.objects.none(),
        empty_label="Select a competitor model",
    )
    match_type = forms.ChoiceField(
        label="Match Type",
        choices=ProductMatch.MatchType.choices,
        initial=ProductMatch.MatchType.DIRECT,
    )
    match_level = forms.ChoiceField(
        label="Match Level",
        choices=ProductMatch.MatchLevel.choices,
        initial=ProductMatch.MatchLevel.CORE,
    )
    rank = forms.IntegerField(label="Rank", min_value=0, required=False)
    match_score = forms.IntegerField(
        label="Match Score",
        min_value=0,
        max_value=100,
        required=False,
    )
    confidence = forms.IntegerField(
        label="Confidence",
        min_value=0,
        max_value=100,
        required=False,
    )
    relation_reason = forms.CharField(
        label="Rationale",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    source_url = forms.URLField(label="Official Source URL", required=False)
    request_reason = forms.CharField(
        label="Reason",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    attachment = forms.FileField(
        label="Evidence Attachment",
        required=False,
        validators=[validate_change_attachment],
        help_text="PDF, PNG, JPG, JPEG, or XLSX; up to 10 MB.",
    )

    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        active_competitor_ids = product.competitor_matches.exclude(
            status=ProductMatch.Status.REJECTED
        ).values_list("competitor_product_id", flat=True)
        self.fields["competitor_product"].queryset = (
            Product.objects.filter(
                is_published=True,
                category=product.category,
                brand__is_own_brand=False,
            )
            .exclude(pk=product.pk)
            .exclude(pk__in=active_competitor_ids)
            .select_related("brand")
            .order_by("brand__name", "model", "region", "hardware_version")
        )
        for _name, field in self.fields.items():
            css_class = "form-select" if isinstance(
                field.widget,
                forms.Select,
            ) else "form-control"
            field.widget.attrs.setdefault("class", css_class)

    def clean(self):
        cleaned = super().clean()
        competitor = cleaned.get("competitor_product")
        if competitor and self.product.competitor_matches.exclude(
            status=ProductMatch.Status.REJECTED
        ).filter(competitor_product=competitor).exists():
            self.add_error("competitor_product", "This competitor is already in the current benchmarks.")
        if not cleaned.get("source_url") and not cleaned.get("attachment"):
            raise ValidationError("Provide an official source URL or evidence attachment.")
        return cleaned
