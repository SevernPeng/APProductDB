from pathlib import Path

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError


class DatasheetUploadForm(forms.Form):
    datasheet = forms.FileField(
        label="Datasheet PDF",
        help_text="Text-based PDF up to 25 MB.",
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": "application/pdf,.pdf"}
        ),
    )

    def clean_datasheet(self):
        uploaded = self.cleaned_data["datasheet"]
        if uploaded.size > settings.DATASHEET_MAX_BYTES:
            raise ValidationError("The file exceeds the maximum allowed size.")
        if Path(uploaded.name).suffix.casefold() != ".pdf":
            raise ValidationError("Only PDF Datasheets can be uploaded.")
        signature = uploaded.read(5)
        uploaded.seek(0)
        if signature != b"%PDF-":
            raise ValidationError("The file content is not a valid PDF.")
        return uploaded


class DatasheetURLForm(forms.Form):
    datasheet_url = forms.URLField(
        label="Datasheet URL",
        max_length=500,
        help_text="Official manufacturer product page or PDF URL.",
        widget=forms.URLInput(
            attrs={
                "class": "form-control",
                "placeholder": "https://vendor.example/product/datasheet.pdf",
                "autocomplete": "url",
            }
        ),
    )
