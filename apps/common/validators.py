import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_RESUME_EXTENSIONS = [".pdf", ".docx"]
PDF_MAGIC_BYTES = b"%PDF"
DOCX_MAGIC_BYTES = b"PK\x03\x04"


def validate_file_size(value, max_mb=5):
    """Enforces maximum file size limit."""
    filesize = value.size
    limit = max_mb * 1024 * 1024
    if filesize > limit:
        raise ValidationError(
            _(f"The maximum file size allowed is {max_mb} MB. Uploaded file size is {filesize / (1024 * 1024):.2f} MB.")
        )


def validate_resume_file(value):
    """
    Validates resume file extension and header signature / magic bytes.
    Accepts PDF and DOCX only.
    """
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise ValidationError(
            _(f"Unsupported file format '{ext}'. Only PDF (.pdf) and Microsoft Word (.docx) documents are allowed.")
        )

    # Validate file size
    validate_file_size(value, max_mb=5)

    # Validate file contents signature
    initial_pos = value.tell()
    value.seek(0)
    header = value.read(8)
    value.seek(initial_pos)

    if ext == ".pdf" and not header.startswith(PDF_MAGIC_BYTES):
        raise ValidationError(_("The uploaded file does not match a valid PDF file structure."))
    elif ext == ".docx" and not header.startswith(DOCX_MAGIC_BYTES):
        raise ValidationError(_("The uploaded file does not match a valid DOCX file structure."))
