from pathlib import Path

from django import forms

from catalog.models import ProductType

from .models import ImportJob


class ProductTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, product_type):
        return f"{product_type.category.name} / {product_type.name}"


class ImportUploadForm(forms.ModelForm):
    product_type = ProductTypeChoiceField(
        label="产品形态",
        queryset=ProductType.objects.none(),
        empty_label="请选择与已下载模板一致的产品形态",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = ImportJob
        fields = ("product_type", "uploaded_file", "mode")
        labels = {"uploaded_file": "填写完成的 Excel 模板", "mode": "导入模式"}
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
            raise forms.ValidationError("只支持 .xlsx 文件。")
        return uploaded_file
