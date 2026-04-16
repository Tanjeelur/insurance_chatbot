
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Dict, List, Optional
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
    policy_disclosure: List[UploadFile] = File(..., description="Policy Disclosure Statement PDFs (one or more)"),
    schedule_coverage: List[UploadFile] = File(default=[], description="Schedule of Coverage PDFs (optional, one or more)"),
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
    logger.info("  policy_disclosure : %d file(s): %s", len(policy_disclosure), ", ".join(f.filename for f in policy_disclosure))
    logger.info("  schedule_coverage : %d file(s): %s", len(schedule_coverage), ", ".join(f.filename for f in schedule_coverage) if schedule_coverage else "not provided")

    # Validate file types
    allowed_types = ["application/pdf"]
    for f in policy_disclosure:
        if f.content_type not in allowed_types:
            logger.warning("Validation failed: policy_disclosure '%s' is not a PDF (%s)", f.filename, f.content_type)
            raise HTTPException(status_code=400, detail=f"Policy Disclosure '{f.filename}' must be a PDF file")
    for f in schedule_coverage:
        if f.content_type not in allowed_types:
            logger.warning("Validation failed: schedule_coverage '%s' is not a PDF (%s)", f.filename, f.content_type)
            raise HTTPException(status_code=400, detail=f"Schedule of Coverage '{f.filename}' must be a PDF file")

    # Validate question
    if not question.strip():
        logger.warning("Validation failed: empty question")
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info("  [1/4] Validation passed")

    try:
        # Read & extract policy disclosure (one or more files)
        logger.info("  [2/4] Extracting text from PDFs ...")
        policy_parts = []
        for f in policy_disclosure:
            text = pdf_extractor.extract_text(await f.read())
            logger.info("        policy_disclosure '%s' → %d chars extracted", f.filename, len(text))
            policy_parts.append(text)
        policy_text = "\n\n".join(policy_parts)

        schedule_section = ""
        if schedule_coverage:
            schedule_parts = []
            for f in schedule_coverage:
                text = pdf_extractor.extract_text(await f.read())
                logger.info("        schedule_coverage '%s' → %d chars extracted", f.filename, len(text))
                schedule_parts.append(text)
            schedule_section = "\n\n=== SCHEDULE OF COVERAGE ===\n" + "\n\n".join(schedule_parts)
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

