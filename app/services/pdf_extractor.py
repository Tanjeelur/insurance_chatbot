from typing import Optional
import PyPDF2
import fitz  # PyMuPDF
import io
from fastapi import HTTPException

class PDFExtractor:
    """Service for extracting text from PDF documents"""
    
    @staticmethod
    def extract_text_pymupdf(pdf_bytes: bytes) -> str:
        """Extract text using PyMuPDF (more accurate for complex layouts)"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            
            for page in doc:
                # Extract text with layout preservation
                page_text = page.get_text("text")
                text += page_text + "\n\n"
            
            doc.close()
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text with PyMuPDF: {str(e)}")
    
    @staticmethod
    def extract_text_pypdf2(pdf_bytes: bytes) -> str:
        """Fallback extraction using PyPDF2"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text with PyPDF2: {str(e)}")
    
    @classmethod
    def extract_text(cls, pdf_bytes: bytes) -> str:
        """Extract text using the best available method"""
        try:
            # Try PyMuPDF first (more accurate)
            text = cls.extract_text_pymupdf(pdf_bytes)
            if text and len(text.strip()) > 50:  # Basic quality check
                return text
        except:
            pass
        
        # Fallback to PyPDF2
        return cls.extract_text_pypdf2(pdf_bytes)
