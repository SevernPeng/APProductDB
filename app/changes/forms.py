from django import forms
from django.core.exceptions import ValidationError

from catalog.models import Brand, Category, Product, ProductModel, ProductSpec, ProductType, normalize_model_key
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
        "launch_date",
        "notes",
        "ap_type",
        "wifi_standard",
    )

    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        self.edit_items = []
        self.identity_items = []

        identity_fields = {
            "brand": forms.ModelChoiceField(
                label="Brand", queryset=Brand.objects.filter(active=True).order_by("name")
            ),
            "model": forms.CharField(label="Model", max_length=150),
            "product_name": forms.CharField(label="Product Name", required=False, max_length=250),
            "category": forms.ModelChoiceField(
                label="Category", queryset=Category.objects.filter(active=True).order_by("name")
            ),
            "product_type": forms.ModelChoiceField(
                label="Product Type", queryset=ProductType.objects.filter(active=True).order_by("category", "display_order", "name"),
                required=False, empty_label="Use category default",
            ),
            "nom_certified": forms.BooleanField(label="NOM Certified", required=False),
        }
        for name, field in identity_fields.items():
            form_name = f"identity_{name}"
            self.fields[form_name] = field
            if name == "product_name":
                initial = product.product_model.product_name if product.product_model_id else ""
            elif name == "nom_certified":
                initial = product.has_nom
            else:
                initial = getattr(product, name)
            self.initial[form_name] = initial
            self.identity_items.append({"name": form_name, "field_name": name})

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
            elif field_name == "official_url":
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

        layout_initials = {}
        layout_definition_ids = None
        if not product.brand.is_own_brand:
            from core.product_spec_layout import competitor_detail_rows
            layout_definition_ids = set()
            for row in competitor_detail_rows(product, []):
                definition = row.get("definition")
                if definition:
                    layout_definition_ids.add(definition.pk)
                if definition and row["display_value"] not in {"Unknown", "Not Published", "Not Applicable"}:
                    layout_initials[definition.pk] = row["display_value"]

        specs = product.specs.filter(definition__active=True).select_related(
            "definition"
        ).order_by("definition__display_order", "definition__display_name")
        for spec in specs:
            definition = spec.definition
            if layout_definition_ids is not None and definition.pk not in layout_definition_ids:
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
                field = forms.CharField(
                    label=definition.display_name,
                    required=False,
                    widget=(
                        forms.Textarea(attrs={"rows": 3})
                        if "\n" in (spec.value_text or "")
                        else forms.TextInput()
                    ),
                )
            self.fields[form_name] = field
            self.initial[form_name] = self._raw_initial(selection)
            if spec.value_status == ProductSpec.ValueStatus.UNKNOWN and definition.data_type == "text":
                self.initial[form_name] = layout_initials.get(definition.pk, self.initial[form_name])
            self.edit_items.append(
                {
                    "name": form_name,
                    "group": definition.group or "Specifications",
                    "unit": definition.unit,
                    "selection": selection,
                }
            )

        match_options = [
            option for option in build_target_options(product)
            if option["key"].startswith("match:") and not option["key"].endswith(f":{MATCH_DELETE_FIELD}")
        ]
        for option in match_options:
            selection = resolve_target(product, option["key"])
            match = selection["target"]
            field_name = selection["field_name"]
            form_name = f"match_{match.pk}_{field_name}"
            if field_name == "match_type":
                field = forms.ChoiceField(label="Match Type", choices=ProductMatch.MatchType.choices)
            elif field_name == "match_level":
                field = forms.ChoiceField(label="Match Level", choices=ProductMatch.MatchLevel.choices)
            elif field_name == "status":
                field = forms.ChoiceField(label="Status", choices=ProductMatch.Status.choices)
            elif field_name in {"match_score", "confidence"}:
                field = forms.IntegerField(label=option["label"].rsplit(" · ", 1)[-1], required=False, min_value=0, max_value=100)
            elif field_name == "rank":
                field = forms.IntegerField(label="Rank", required=False, min_value=0)
            elif field_name in {"valid_from", "valid_to"}:
                field = forms.DateField(label=option["label"].rsplit(" · ", 1)[-1], required=False, widget=forms.DateInput(attrs={"type": "date"}))
            elif field_name == "source_url":
                field = forms.URLField(label="Source URL", required=False)
            else:
                field = forms.CharField(
                    label=option["label"].rsplit(" · ", 1)[-1], required=False,
                    widget=forms.Textarea(attrs={"rows": 2}) if field_name in {"reason", "advantages", "disadvantages"} else forms.TextInput(),
                )
            self.fields[form_name] = field
            self.initial[form_name] = self._raw_initial(selection)
            self.edit_items.append({
                "name": form_name, "group": option["group"], "selection": selection,
            })

        self.price_snapshot = product.price_snapshots.filter(source__code="syscom").order_by("-created_at", "-pk").first()
        if self.price_snapshot:
            self.fields["price_unit_price"] = forms.DecimalField(
                label="Current Price", max_digits=14, decimal_places=4, min_value=0,
            )
            self.fields["price_currency"] = forms.CharField(label="Currency", max_length=10)
            self.fields["price_product_url"] = forms.URLField(label="SYSCOM Product URL", required=False)
            self.initial.update({
                "price_unit_price": self.price_snapshot.unit_price,
                "price_currency": self.price_snapshot.currency,
                "price_product_url": self.price_snapshot.product_url,
            })

        self.fields["product_image"] = forms.ImageField(
            label="Replace product image",
            required=False,
            widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
        )
        self.fields["remove_image"] = forms.BooleanField(
            label="Remove current image",
            required=False,
        )

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            field.widget.attrs.setdefault("class", css_class)

    def clean(self):
        cleaned = super().clean()
        brand = cleaned.get("identity_brand")
        category = cleaned.get("identity_category")
        product_type = cleaned.get("identity_product_type")
        model = (cleaned.get("identity_model") or "").strip()
        if product_type and category and product_type.category_id != category.pk:
            self.add_error("identity_product_type", "Product type must belong to the selected category.")
        if brand and category and model:
            model_key = normalize_model_key(model)
            canonical = ProductModel.objects.filter(brand=brand, model_key=model_key).first()
            if canonical and canonical.category_id != category.pk:
                self.add_error("identity_model", f"This model already belongs to {canonical.category.name}.")
            region = (cleaned.get("product_region") or "").strip()
            hardware = (cleaned.get("product_hardware_version") or "").strip()
            if Product.objects.exclude(pk=self.product.pk).filter(
                brand=brand, model_key=model_key, region__iexact=region,
                hardware_version__iexact=hardware,
            ).exists():
                self.add_error("identity_model", "This product variant already exists.")
        return cleaned

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

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("product_image") and cleaned.get("remove_image"):
            raise ValidationError("Choose either a replacement image or remove the current image.")
        return cleaned


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
    brand = forms.ModelChoiceField(
        label="Brand",
        queryset=Brand.objects.none(),
        empty_label="Select a competitor brand",
    )
    model = forms.CharField(label="Product Model", max_length=150)
    region = forms.CharField(label="Region", max_length=50)
    hardware_version = forms.CharField(
        label="Hardware Version",
        max_length=100,
        required=False,
    )
    product_type = forms.ModelChoiceField(
        label="Product Type",
        queryset=ProductType.objects.none(),
        required=False,
        empty_label="Use category default",
    )
    official_url = forms.URLField(label="Official Product Page", required=False)
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
        required=False,
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
        self.matched_product = None
        self.fields["brand"].queryset = Brand.objects.filter(
            is_own_brand=False,
            active=True,
        ).order_by("name")
        self.fields["product_type"].queryset = ProductType.objects.filter(
            category=product.category,
            active=True,
        ).order_by("display_order", "name")
        self.fields["region"].initial = product.region
        self.fields["region"].help_text = (
            "Brand, normalized model, region, and hardware version are used to find an existing record."
        )
        for _name, field in self.fields.items():
            css_class = "form-select" if isinstance(
                field.widget,
                forms.Select,
            ) else "form-control"
            field.widget.attrs.setdefault("class", css_class)

    def clean(self):
        cleaned = super().clean()
        brand = cleaned.get("brand")
        model = (cleaned.get("model") or "").strip()
        region = (cleaned.get("region") or "").strip()
        hardware_version = (cleaned.get("hardware_version") or "").strip()
        cleaned.update(
            model=model,
            region=region,
            hardware_version=hardware_version,
        )
        if not brand or not model or not region:
            return cleaned

        model_key = normalize_model_key(model)
        self.matched_product = Product.objects.filter(
            brand=brand,
            model_key=model_key,
            region__iexact=region,
            hardware_version__iexact=hardware_version,
        ).first()
        if self.matched_product:
            if self.matched_product.category_id != self.product.category_id:
                self.add_error(
                    "model",
                    f"This existing product belongs to the {self.matched_product.category.name} category.",
                )
                return cleaned
            if self.product.competitor_matches.exclude(
                status=ProductMatch.Status.REJECTED
            ).filter(competitor_product=self.matched_product).exists():
                self.add_error("model", "This competitor is already in the current benchmarks.")
            return cleaned

        canonical = ProductModel.objects.filter(
            brand=brand,
            model_key=model_key,
        ).first()
        if canonical and canonical.category_id != self.product.category_id:
            self.add_error(
                "model",
                f"This model already belongs to the {canonical.category.name} category.",
            )
        return cleaned

    def save_competitor(self, user):
        """Reuse the matching variant or create a new competitor product."""
        if not self.is_valid():
            raise ValueError("Cannot save an invalid competitor form.")
        if self.matched_product:
            competitor = Product.objects.select_for_update().get(pk=self.matched_product.pk)
            update_fields = []
            if not competitor.is_published:
                competitor.is_published = True
                update_fields.append("is_published")
            if self.cleaned_data.get("official_url") and not competitor.official_url:
                competitor.official_url = self.cleaned_data["official_url"]
                update_fields.append("official_url")
            if self.cleaned_data.get("product_type") and not competitor.product_type_id:
                competitor.product_type = self.cleaned_data["product_type"]
                update_fields.append("product_type")
            if update_fields:
                competitor.updated_by = user
                update_fields.extend(("updated_by", "updated_at"))
                competitor.save(update_fields=update_fields)
            return competitor, False

        competitor = Product.objects.create(
            brand=self.cleaned_data["brand"],
            category=self.product.category,
            product_type=self.cleaned_data.get("product_type"),
            model=self.cleaned_data["model"],
            region=self.cleaned_data["region"],
            hardware_version=self.cleaned_data.get("hardware_version", ""),
            official_url=self.cleaned_data.get("official_url", ""),
            lifecycle_status=Product.LifecycleStatus.ACTIVE,
            is_published=True,
            created_by=user,
            updated_by=user,
        )
        return competitor, True
