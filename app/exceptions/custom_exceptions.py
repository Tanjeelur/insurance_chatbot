from fastapi import HTTPException

class PDFExtractionError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"PDF extraction error: {detail}")

class AnalysisError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=500, detail=f"Analysis error: {detail}")

class ValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=f"Validation error: {detail}")