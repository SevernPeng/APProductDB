from pathlib import Path

from django import forms

from catalog.models import ProductType

from .models import ImportJob


class ProductTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, product_type):
        return f"{product_type.category.name} / {product_type.name}"


class ImportUploadForm(forms.ModelForm):
    product_type = ProductTypeChoiceField(
        label="Product Type",
        queryset=ProductType.objects.none(),
        empty_label="Select the product type matching the template",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = ImportJob
        fields = ("product_type", "uploaded_file", "mode")
        labels = {"uploaded_file": "Completed Excel Template", "mode": "Import Mode"}
        widgets = {
            "uploaded_file": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": ".xlsx"}
            ),
            "mode": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product_type"].queryset = ProductType.objects.filter(
            active=True,
            category__slug__in=(
                "access-point",
                "managed-switches",
                "unmanaged-easy-smart-switches",
                "gateway",
                "accessories",
            ),
        ).select_related("category").order_by(
            "category__name", "display_order", "name"
        )

    def clean_uploaded_file(self):
        uploaded_file = self.cleaned_data["uploaded_file"]
        if Path(uploaded_file.name).suffix.lower() != ".xlsx":
            raise forms.ValidationError("Only .xlsx files are supported.")
        return uploaded_file
