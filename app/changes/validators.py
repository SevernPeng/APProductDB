from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".xlsx"}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
FILE_SIGNATURES = {
    ".pdf": (b"%PDF",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".xlsx": (b"PK\x03\x04",),
}


def change_attachment_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"change-evidence/{uuid4().hex}{suffix}"


def validate_change_attachment(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValidationError("附件仅支持 PDF、PNG、JPG、JPEG 或 XLSX。")
    if uploaded_file.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError("附件大小不能超过 10 MB。")
    close_after_validation = isinstance(uploaded_file, FieldFile) and uploaded_file.closed
    if close_after_validation:
        uploaded_file.open("rb")
    try:
        position = uploaded_file.tell()
        uploaded_file.seek(0)
        header = uploaded_file.read(8)
        uploaded_file.seek(position)
    finally:
        if close_after_validation:
            uploaded_file.close()
    if not any(header.startswith(signature) for signature in FILE_SIGNATURES[suffix]):
        raise ValidationError("附件内容与文件扩展名不匹配。")
