"""Read NOM tracker evidence; never infer certification from a model substring."""

import re
from datetime import date

from django.utils import timezone

from .models import normalize_model_key

CERTIFICATE_COLUMNS = (("NOM-001", 5), ("NOM-208", 9), ("NOM-019", 12),
                       ("NOM-003", 21), ("NOM-030", 24))
REGION_RE = re.compile(r"\((US\d*|EU|UN|UK|AU|CA|MX|ES)\)", re.IGNORECASE)
VERSION_RE = re.compile(r"\bV(\d+(?:\.\d+)*)", re.IGNORECASE)


def version_key(value):
    value = str(value).strip().upper().removeprefix("V")
    return re.sub(r"(?:\.0)+$", "", value)


def parse_identity(label):
    regions = REGION_RE.findall(label)
    versions = VERSION_RE.findall(label)
    boundary = re.search(r"\s*\((?:US\d*|EU|UN|UK|AU|CA|MX|ES)\)|\s+V\d", label, re.I)
    model = label[:boundary.start()] if boundary else label
    return normalize_model_key(model.strip()), [r.upper() for r in regions], versions


def matches_product(record, product):
    return (
        record["model_key"] == product.model_key
        and (not record["regions"] or product.region.upper() in record["regions"])
        and (not product.hardware_version or not record["versions"]
             or version_key(product.hardware_version) in {
                 version_key(v) for v in record["versions"]
             })
    )


def has_current_nom(records, on_date=None):
    today = on_date or timezone.localdate()
    for record in records:
        if not record.get("ready"):
            continue
        for certificate in record.get("certificates", []):
            expiry = certificate.get("expires_on")
            if certificate.get("number") and (
                certificate.get("permanent")
                or (expiry and date.fromisoformat(expiry) >= today)
            ):
                return True
    return False


def read_tracker(path):
    import xlrd

    workbook = xlrd.open_workbook(str(path))
    sheet = workbook.sheet_by_name("NOM_2026")
    if sheet.cell_value(3, 0) != "MODELS" or sheet.cell_value(3, 1) != "READY":
        raise ValueError("Unexpected NOM tracker headers.")
    for standard, column in CERTIFICATE_COLUMNS:
        group_column = 8 if standard == "NOM-208" else column
        if sheet.cell_value(2, group_column) != standard or sheet.cell_value(3, column) != "CERTIFICATE":
            raise ValueError(f"Unexpected {standard} certificate column.")
    records = []
    for index in range(5, sheet.nrows):
        values = sheet.row_values(index)
        label = str(values[0]).strip()
        if not label:
            continue
        model_key, regions, versions = parse_identity(label)
        certificates = []
        for standard, column in CERTIFICATE_COLUMNS:
            number = str(values[column]).strip()
            if not number or number.upper() in {"N/A", "-"}:
                continue
            end = values[column + 2]
            expires_on = None
            if isinstance(end, (float, int)):
                expires_on = xlrd.xldate_as_datetime(end, workbook.datemode).date().isoformat()
            certificates.append({
                "standard": standard, "number": number,
                "expires_on": expires_on,
                "permanent": str(end).strip().casefold() == "definitiva",
            })
        records.append({
            "source": path.name, "sheet": sheet.name, "row": index + 1,
            "label": label, "model_key": model_key, "regions": regions,
            "versions": versions, "ready": str(values[1]).strip().upper() == "YES",
            "certificates": certificates,
        })
    if not records:
        raise ValueError("NOM tracker contains no model records.")
    return records
