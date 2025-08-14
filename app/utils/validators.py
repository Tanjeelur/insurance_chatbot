from fastapi import HTTPException
from typing import List

def validate_pdf_file_type(content_type: str, allowed_types: List[str] = ["application/pdf"]) -> None:
    """Validate that uploaded file is a PDF"""
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File must be a PDF")

def validate_question_content(question: str) -> None:
    """Validate that question is not empty"""
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
