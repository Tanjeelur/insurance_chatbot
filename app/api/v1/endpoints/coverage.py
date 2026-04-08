
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Dict, Optional
import uuid
from datetime import datetime

from app.schemas.coverage import CoverageResponse, HealthResponse
from app.services.pdf_extractor import PDFExtractor
from app.services.insurance_analyzer import InsuranceAnalyzer
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    tags=["coverage"]
)

def get_pdf_extractor() -> PDFExtractor:
    """Dependency to get PDF extractor service"""
    return PDFExtractor()

def get_insurance_analyzer() -> InsuranceAnalyzer:
    """Dependency to get insurance analyzer service"""
    return InsuranceAnalyzer()

@router.post("/analyze-coverage", response_model=CoverageResponse)
async def analyze_coverage(
    policy_disclosure: UploadFile = File(..., description="Policy Disclosure Statement PDF"),
    schedule_coverage: Optional[UploadFile] = File(None, description="Schedule of Coverage PDF (optional)"),
    insurance_type: str = Form(..., description="Type of insurance (e.g., auto, home, health, construction etc)"),
    question: str = Form(..., description="Your question about insurance coverage"),
    pdf_extractor: PDFExtractor = Depends(get_pdf_extractor),
    analyzer: InsuranceAnalyzer = Depends(get_insurance_analyzer)
):
    """Upload insurance documents and get immediate coverage analysis for your question"""
    start = time.perf_counter()
    logger.info("── New analysis request ──────────────────────────────")
    logger.info("  insurance_type : %s", insurance_type)
    logger.info("  question       : %s", question[:120])
    logger.info("  policy_disclosure : %s (%s)", policy_disclosure.filename, policy_disclosure.content_type)
    logger.info("  schedule_coverage : %s", f"{schedule_coverage.filename} ({schedule_coverage.content_type})" if schedule_coverage else "not provided")

    # Validate file types
    allowed_types = ["application/pdf"]
    if policy_disclosure.content_type not in allowed_types:
        logger.warning("Validation failed: policy_disclosure is not a PDF (%s)", policy_disclosure.content_type)
        raise HTTPException(status_code=400, detail="Policy Disclosure must be a PDF file")
    if schedule_coverage is not None and schedule_coverage.content_type not in allowed_types:
        logger.warning("Validation failed: schedule_coverage is not a PDF (%s)", schedule_coverage.content_type)
        raise HTTPException(status_code=400, detail="Schedule of Coverage must be a PDF file")

    # Validate question
    if not question.strip():
        logger.warning("Validation failed: empty question")
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info("  [1/4] Validation passed")

    try:
        # Read & extract policy disclosure
        logger.info("  [2/4] Extracting text from PDFs ...")
        policy_bytes = await policy_disclosure.read()
        policy_text = pdf_extractor.extract_text(policy_bytes)
        logger.info("        policy_disclosure → %d chars extracted", len(policy_text))

        schedule_section = ""
        if schedule_coverage is not None:
            schedule_bytes = await schedule_coverage.read()
            schedule_text = pdf_extractor.extract_text(schedule_bytes)
            schedule_section = f"\n\n=== SCHEDULE OF COVERAGE ===\n{schedule_text}"
            logger.info("        schedule_coverage  → %d chars extracted", len(schedule_text))
        else:
            logger.info("        schedule_coverage  → skipped (not provided)")

        combined_text = f"=== POLICY DISCLOSURE STATEMENT ===\n{policy_text}{schedule_section}"
        logger.info("        combined text      → %d chars total", len(combined_text))

        # AI analysis
        logger.info("  [3/4] Sending to OpenAI (%s) ...", analyzer.settings.OPENAI_MODEL)
        ai_start = time.perf_counter()
        result = analyzer.analyze_coverage(combined_text, question, insurance_type)
        ai_elapsed = (time.perf_counter() - ai_start) * 1000
        logger.info("        OpenAI responded in %.0fms", ai_elapsed)
        logger.info("        clarity_score=%s  wording_review=%s", result["clarity_score"], result["policy_wording_review"])

        # Build response
        logger.info("  [4/4] Building response ...")
        response = CoverageResponse(
            policy_name=result["policy_name"],
            policy_price=str(result["policy_price"]),
            policy_renewal_date=result["policy_renewal_date"],
            clarity_score=result["clarity_score"],
            policy_wording_review=result["policy_wording_review"],
            explanation=result["explanation"],
            disclaimer=result["disclaimer"],
            policy_notes=result["policy_notes"]
        )

        total_elapsed = (time.perf_counter() - start) * 1000
        logger.info("  ✓ Request complete in %.0fms", total_elapsed)
        logger.info("─" * 54)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("  ✗ Unhandled error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

