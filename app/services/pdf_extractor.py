from typing import Optional
import PyPDF2
import fitz  # PyMuPDF
import io
from fastapi import HTTPException
from app.core.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """Service for extracting text from PDF documents"""
    
    @staticmethod
    def extract_text_pymupdf(pdf_bytes: bytes) -> str:
        """Extract text using PyMuPDF (more accurate for complex layouts)"""
        logger.debug("PDFExtractor: trying PyMuPDF (%d bytes)", len(pdf_bytes))
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n\n"
            doc.close()
            logger.debug("PDFExtractor: PyMuPDF extracted %d pages, %d chars", doc.page_count, len(text))
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text with PyMuPDF: {str(e)}")

    @staticmethod
    def extract_text_pypdf2(pdf_bytes: bytes) -> str:
        """Fallback extraction using PyPDF2"""
        logger.debug("PDFExtractor: trying PyPDF2 (%d bytes)", len(pdf_bytes))
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
            logger.debug("PDFExtractor: PyPDF2 extracted %d pages, %d chars", len(pdf_reader.pages), len(text))
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text with PyPDF2: {str(e)}")

    @classmethod
    def extract_text(cls, pdf_bytes: bytes) -> str:
        """Extract text using the best available method"""
        try:
            text = cls.extract_text_pymupdf(pdf_bytes)
            if text and len(text.strip()) > 50:
                logger.info("PDFExtractor: used PyMuPDF → %d chars", len(text))
                return text
            logger.warning("PDFExtractor: PyMuPDF returned too little text, falling back to PyPDF2")
        except Exception:
            logger.warning("PDFExtractor: PyMuPDF failed, falling back to PyPDF2")

        text = cls.extract_text_pypdf2(pdf_bytes)
        logger.info("PDFExtractor: used PyPDF2 → %d chars", len(text))
        return text
