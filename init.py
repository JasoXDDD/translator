"""translator package init"""
from .keywords_extractor import (
    read_text_file,
    build_prompt,
    extract_keywords_from_text,
    extract_keywords_from_file,
)

__all__ = [
    "read_text_file",
    "build_prompt",
    "extract_keywords_from_text",
    "extract_keywords_from_file",
]
