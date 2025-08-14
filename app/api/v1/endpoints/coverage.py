from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Dict
import uuid
from datetime import datetime

from app.schemas.coverage import CoverageResponse, HealthResponse
from app.services.pdf_extractor import PDFExtractor
from app.services.insurance_analyzer import InsuranceAnalyzer

router = APIRouter()

def get_pdf_extractor() -> PDFExtractor:
    """Dependency to get PDF extractor service"""
    return PDFExtractor()

def get_insurance_analyzer() -> InsuranceAnalyzer:
    """Dependency to get insurance analyzer service"""
    return InsuranceAnalyzer()

@router.post("/analyze-coverage", response_model=CoverageResponse)
async def analyze_coverage(
    policy_disclosure: UploadFile = File(..., description="Policy Disclosure Statement PDF"),
    schedule_coverage: UploadFile = File(..., description="Schedule of Coverage PDF"),
    insurance_type: str = Form(..., description="Type of insurance (e.g., auto, home, health, construction etc)"),
    question: str = Form(..., description="Your question about insurance coverage"),
    pdf_extractor: PDFExtractor = Depends(get_pdf_extractor),
    analyzer: InsuranceAnalyzer = Depends(get_insurance_analyzer)
):
    """Upload insurance documents and get immediate coverage analysis for your question"""
    
    # Validate file types
    allowed_types = ["application/pdf"]
    if policy_disclosure.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Policy Disclosure must be a PDF file")
    if schedule_coverage.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Schedule of Coverage must be a PDF file")
    
    # Validate question
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    
    try:
        # Read PDF files
        policy_bytes = await policy_disclosure.read()
        schedule_bytes = await schedule_coverage.read()
        
        # Extract text from both PDFs
        policy_text = pdf_extractor.extract_text(policy_bytes)
        schedule_text = pdf_extractor.extract_text(schedule_bytes)
        
        # Combine the texts
        combined_text = f"""
=== POLICY DISCLOSURE STATEMENT ===
{policy_text}

=== SCHEDULE OF COVERAGE ===
{schedule_text}
"""
        
        # Analyze coverage immediately
        result = analyzer.analyze_coverage(combined_text, question, insurance_type)
        
        # # Create session ID for tracking
        # session_id = str(uuid.uuid4())
        
        # # Prepare processing info
        # processing_info = {
        #     "policy_pages_extracted": len(policy_text.split('\n\n')),
        #     "schedule_pages_extracted": len(schedule_text.split('\n\n')),
        #     "total_characters": len(combined_text),
        #     "question_length": len(question)
        # }
        
        # Prepare response
        return CoverageResponse(
            percentage_score=result["percentage_score"],
            likelihood_ranking=result["likelihood_ranking"],
            explanation=result["explanation"],
            # session_id=session_id,
            # timestamp=datetime.now().isoformat(),
            # processing_info=processing_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        model="Insurance Document Analyzer with Fine-tuned Instructions"
    )

@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Insurance Document Analyzer API - Modular Architecture",
        "version": "2.0.0",
        "description": "Upload PDS and Schedule PDFs with your coverage question to get immediate analysis",
        "main_endpoint": "/analyze-coverage",
        "features": [
            "Single API call for complete analysis",
            "Fine-tuned model with conservative assessment framework",
            "Structured 40-word explanations",
            "Percentage-based confidence scoring",
            "Professional insurance policy interpretation",
            "Modular FastAPI architecture"
        ]
    }
