from django import forms
from django.core.exceptions import ValidationError

from catalog.models import Product
from comparison.models import ProductMatch

from .services import (
    MATCH_DELETE_FIELD,
    display_snapshot,
    parse_proposed_value,
    snapshot_for_selection,
)
from .validators import validate_change_attachment


class ChangeSubmissionForm(forms.Form):
    proposed_value = forms.CharField(
        label="建议值",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    reason = forms.CharField(
        label="修改原因",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    source_url = forms.URLField(label="官方来源 URL", required=False)
    attachment = forms.FileField(
        label="证据附件",
        required=False,
        validators=[validate_change_attachment],
        help_text="支持 PDF、PNG、JPG、JPEG、XLSX，最大 10 MB。",
    )

    def __init__(self, *args, selection, **kwargs):
        super().__init__(*args, **kwargs)
        self.selection = selection
        field_name = selection["field_name"]
        target = selection["target"]
        if field_name == MATCH_DELETE_FIELD:
            self.fields["proposed_value"].widget = forms.HiddenInput()
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
            self.add_error("proposed_value", "建议值不能与当前值相同。")
        if (
            self.selection["request_type"] == "spec"
            and not cleaned.get("source_url")
            and not cleaned.get("attachment")
        ):
            raise ValidationError("规格修改必须提供官方来源 URL 或证据附件。")
        cleaned["old_value"] = old_value
        cleaned["parsed_proposed_value"] = proposed
        return cleaned


class MatchAddForm(forms.Form):
    competitor_product = forms.ModelChoiceField(
        label="新增竞品",
        queryset=Product.objects.none(),
        empty_label="请选择竞品型号",
    )
    match_type = forms.ChoiceField(
        label="对标类型",
        choices=ProductMatch.MatchType.choices,
        initial=ProductMatch.MatchType.DIRECT,
    )
    match_level = forms.ChoiceField(
        label="对标级别",
        choices=ProductMatch.MatchLevel.choices,
        initial=ProductMatch.MatchLevel.CORE,
    )
    rank = forms.IntegerField(label="排序", min_value=0, required=False)
    match_score = forms.IntegerField(
        label="匹配分数",
        min_value=0,
        max_value=100,
        required=False,
    )
    confidence = forms.IntegerField(
        label="置信度",
        min_value=0,
        max_value=100,
        required=False,
    )
    relation_reason = forms.CharField(
        label="对标理由",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    source_url = forms.URLField(label="官方来源 URL", required=False)
    request_reason = forms.CharField(
        label="新增原因",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    attachment = forms.FileField(
        label="证据附件",
        required=False,
        validators=[validate_change_attachment],
        help_text="支持 PDF、PNG、JPG、JPEG、XLSX，最大 10 MB。",
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
            self.add_error("competitor_product", "该竞品已在当前对标关系中。")
        if not cleaned.get("source_url") and not cleaned.get("attachment"):
            raise ValidationError("新增对标关系必须提供官方来源 URL 或证据附件。")
        return cleaned


class ReviewDecisionForm(forms.Form):
    review_comment = forms.CharField(
        label="审核意见",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
    )
