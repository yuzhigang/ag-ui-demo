"""Generated page document schema and validation."""

from .schema import VALID_GAPS, VALID_IMPORTANCE, build_page_document_schema
from .validation import PageDocumentValidationError, validate_page_document

__all__ = [
    "PageDocumentValidationError",
    "VALID_GAPS",
    "VALID_IMPORTANCE",
    "build_page_document_schema",
    "validate_page_document",
]
