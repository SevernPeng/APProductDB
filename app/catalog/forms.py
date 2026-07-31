from pathlib import Path

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError


class DatasheetUploadForm(forms.Form):
    datasheet = forms.FileField(
        label="Datasheet PDF",
        help_text="仅支持不超过 25 MB、可提取文字的 PDF 文件。",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": "application/pdf,.pdf"}
        ),
    )

    def clean_datasheet(self):
        uploaded = self.cleaned_data["datasheet"]
        if uploaded.size > settings.DATASHEET_MAX_BYTES:
            raise ValidationError("文件超过系统允许的大小。")
        if Path(uploaded.name).suffix.casefold() != ".pdf":
            raise ValidationError("只允许上传 PDF 格式的 Datasheet。")
        signature = uploaded.read(5)
        uploaded.seek(0)
        if signature != b"%PDF-":
            raise ValidationError("文件扩展名为 PDF，但文件内容不是有效 PDF。")
        return uploaded


class DatasheetURLForm(forms.Form):
    datasheet_url = forms.URLField(
        label="Datasheet URL",
        max_length=500,
        help_text="请填写厂商官方产品页或官方 PDF 地址。",
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://vendor.example/product/datasheet.pdf",
                "autocomplete": "url",
            }
        ),
    )
