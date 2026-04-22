import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List

from app.schemas.coverage import CoverageResponse, HealthResponse
from app.services.pdf_extractor import PDFExtractor
from app.services.insurance_analyzer import InsuranceAnalyzer
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["coverage"])

# ── Dependency injection ───────────────────────────────────────────────────────

def get_pdf_extractor() -> PDFExtractor:
    return PDFExtractor()

def get_insurance_analyzer() -> InsuranceAnalyzer:
    return InsuranceAnalyzer()

# ── Constants ──────────────────────────────────────────────────────────────────

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB per file


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _read_and_validate_files(
    files: List[UploadFile],
    label: str,
    pdf_extractor: PDFExtractor,
) -> List[str]:
    """
    Read, size-check, type-check, and extract text from a list of uploaded files.
    Returns a list of extracted text strings (one per file).
    Raises HTTPException on any validation failure.
    """
    texts = []
    for f in files:
        # Content-type check
        if f.content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning(
                "Validation failed: %s '%s' is not a PDF (%s)",
                label, f.filename, f.content_type
            )
            raise HTTPException(
                status_code=400,
                detail=f"{label} '{f.filename}' must be a PDF file (got {f.content_type})"
            )

        raw = await f.read()

        # Size check
        if len(raw) > MAX_FILE_SIZE_BYTES:
            logger.warning(
                "Validation failed: %s '%s' exceeds size limit (%d bytes)",
                label, f.filename, len(raw)
            )
            raise HTTPException(
                status_code=413,
                detail=f"{label} '{f.filename}' exceeds the 20 MB file size limit."
            )

        text = pdf_extractor.extract_text(raw)

        # Empty extraction check
        if not text.strip():
            logger.warning(
                "Extraction warning: %s '%s' produced no readable text (scanned or corrupt PDF?)",
                label, f.filename
            )
            raise HTTPException(
                status_code=422,
                detail=(
                    f"{label} '{f.filename}' produced no readable text. "
                    "The file may be scanned, image-only, or corrupt."
                )
            )

        logger.info("        %s '%s' → %d chars extracted", label, f.filename, len(text))
        texts.append(text)

    return texts


# ── Route ──────────────────────────────────────────────────────────────────────

@router.post("/analyze-coverage", response_model=CoverageResponse)
async def analyze_coverage(
    policy_disclosure: List[UploadFile] = File(
        ..., description="Policy Disclosure Statement PDFs (one or more)"
    ),
    schedule_coverage: List[UploadFile] = File(
        default=[], description="Schedule of Coverage PDFs (optional)"
    ),
    insurance_type: str = Form(
        ..., description="Type of insurance (e.g. home, contents, landlord, auto)"
    ),
    question: str = Form(..., description="Your question about insurance coverage"),
    pdf_extractor: PDFExtractor = Depends(get_pdf_extractor),
    analyzer: InsuranceAnalyzer = Depends(get_insurance_analyzer),
):
    """Upload insurance policy documents and receive an immediate, structured coverage analysis."""

    start = time.perf_counter()
    logger.info("── New analysis request ──────────────────────────────")
    logger.info("  insurance_type    : %s", insurance_type)
    logger.info("  question          : %s", question[:120])
    logger.info(
        "  policy_disclosure : %d file(s): %s",
        len(policy_disclosure),
        ", ".join(f.filename for f in policy_disclosure),
    )
    logger.info(
        "  schedule_coverage : %d file(s): %s",
        len(schedule_coverage),
        ", ".join(f.filename for f in schedule_coverage) if schedule_coverage else "not provided",
    )

    # ── [1/4] Validate inputs ──────────────────────────────────────────────────
    if not question.strip():
        logger.warning("Validation failed: empty question")
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not insurance_type.strip():
        logger.warning("Validation failed: empty insurance_type")
        raise HTTPException(status_code=400, detail="Insurance type cannot be empty.")

    logger.info("  [1/4] Input validation passed")

    try:
        # ── [2/4] Extract PDF text ─────────────────────────────────────────────
        logger.info("  [2/4] Extracting text from PDFs ...")

        policy_texts = await _read_and_validate_files(
            policy_disclosure, "Policy Disclosure", pdf_extractor
        )
        policy_text = "\n\n".join(policy_texts)

        schedule_text = ""
        if schedule_coverage:
            schedule_texts = await _read_and_validate_files(
                schedule_coverage, "Schedule of Coverage", pdf_extractor
            )
            schedule_text = "\n\n=== SCHEDULE OF COVERAGE ===\n" + "\n\n".join(schedule_texts)
        else:
            logger.info("        schedule_coverage → skipped (not provided)")

        combined_text = f"=== POLICY DISCLOSURE STATEMENT ===\n{policy_text}{schedule_text}"
        logger.info("        combined text → %d chars total", len(combined_text))

        # ── [3/4] AI analysis ──────────────────────────────────────────────────
        logger.info("  [3/4] Sending to OpenAI (%s) ...", analyzer.settings.OPENAI_MODEL)
        ai_start = time.perf_counter()
        result = analyzer.analyze_coverage(combined_text, question, insurance_type)
        ai_elapsed = (time.perf_counter() - ai_start) * 1000
        logger.info("        OpenAI responded in %.0f ms", ai_elapsed)
        logger.info(
            "        explanation_points=%d  policy_notes=%d",
            len(result["explanation"]),
            len(result["policy_notes"]),
        )

        # ── [4/4] Build response ───────────────────────────────────────────────
        logger.info("  [4/4] Building response ...")
        response = CoverageResponse(
            policy_name=result["policy_name"],
            user_question=result["user_question"],
            direct_answer=result["direct_answer"],
            explanation=result["explanation"],
            explanation_summary=result["explanation_summary"],
            policy_notes=result["policy_notes"],
            policy_price=result["policy_price"],
            final_summary=result["final_summary"],
        )

        total_elapsed = (time.perf_counter() - start) * 1000
        logger.info("  ✓ Request complete in %.0f ms", total_elapsed)
        logger.info("─" * 54)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("  ✗ Unhandled error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")