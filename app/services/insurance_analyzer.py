from typing import Dict
import re
import json
from openai import OpenAI
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class InsuranceAnalyzer:
    """Service for analyzing insurance coverage based on policy documents"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.likelihood_ranges = {
            "No Mention": (0, 20),
            "Little Mention": (21, 50),
            "Explicit Mention": (51, 65),
            "Highly Explicit Mention": (66, 100)
            
        }
    
    def clean_and_structure_text(self, text: str) -> str:
        """Clean and structure the extracted text for better processing"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Identify and preserve important sections
        sections = [
            "policy summary", "coverage", "exclusions", "deductible", 
            "limits", "conditions", "definitions", "schedule", "listed events"
        ]
        
        lines = text.split('\n')
        structured_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Check if line might be a section header
                if any(section in line.lower() for section in sections):
                    structured_lines.append(f"\n=== {line} ===")
                else:
                    structured_lines.append(line)
        
        return '\n'.join(structured_lines)
    
    def validate_response_format(self, result: dict) -> dict:
        """Validate and correct the response format according to the model instructions"""
        
        # Ensure clarity_score is within valid range
        clarity_score = result.get("clarity_score", 50)
        if not isinstance(clarity_score, int) or clarity_score < 0 or clarity_score > 100:
            clarity_score = 50
        
        # policy notes field validation
        policy_notes = result.get("policy_notes", [])
        policy_name = result.get("policy_name") or "N/A"
        policy_renewal_date = result.get("policy_renewal_date") or "N/A"

        raw_price = result.get("policy_price")
        if not raw_price or str(raw_price).strip().lower() in ("none", "n/a", "null", "", "not available"):
            policy_price = "Not stated in provided documents"
        else:
            policy_price = str(raw_price).strip()

        
        # Map percentage to correct policy_wording_review
        policy_wording_review = "Little Mention"  # default
        for ranking, (min_val, max_val) in self.likelihood_ranges.items():
            if min_val <= clarity_score <= max_val:
                policy_wording_review = ranking
                break
        
        # Ensure explanation is within 40 words - truncate if over, accept if under
        explanation = result.get("explanation") or "Coverage assessment unavailable due to insufficient information in provided documentation."
        words = explanation.split()
        if len(words) > 40:
            explanation = " ".join(words[:40])
        
        # Add the mandatory disclaimer
        disclaimer = "This interpretation is document-based only, not advice. Seek independent financial or legal guidance."
        
        return {
            "policy_name": policy_name,
            "policy_price": policy_price,
            "policy_renewal_date": policy_renewal_date,
            "clarity_score": clarity_score,
            "policy_wording_review": policy_wording_review,
            "explanation": explanation,
            "disclaimer": disclaimer,
            "policy_notes": policy_notes
        }

    def analyze_coverage(self, pdf_content: str, question: str, insurance_type: str) -> dict:
        """Analyze insurance coverage based on PDF content and user question"""

        logger.info("Analyzer: cleaning and structuring text (%d chars)", len(pdf_content))
        structured_content = self.clean_and_structure_text(pdf_content)
        logger.info("Analyzer: structured text ready (%d chars)", len(structured_content))

        prompt = self._create_analysis_prompt(structured_content, question, insurance_type)
        logger.info("Analyzer: prompt built (%d chars) — calling %s", len(prompt), self.settings.OPENAI_MODEL)

        try:
            response = self.client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert insurance policy analyzer. Always respond with valid JSON following the specified format exactly. Be highly conservative in your assessments and ensure explanations are exactly 40 words."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.settings.TEMPERATURE,
                max_tokens=self.settings.MAX_TOKENS
            )
            raw = response.choices[0].message.content.strip()
            usage = response.usage
            logger.info(
                "Analyzer: OpenAI response received — tokens: prompt=%s completion=%s total=%s",
                usage.prompt_tokens, usage.completion_tokens, usage.total_tokens
            )

            # Parse JSON response
            try:
                parsed_result = json.loads(raw)
                logger.info("Analyzer: JSON parsed successfully")
            except json.JSONDecodeError:
                logger.warning("Analyzer: direct JSON parse failed, attempting regex extraction")
                json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                if json_match:
                    parsed_result = json.loads(json_match.group())
                    logger.info("Analyzer: JSON extracted via regex")
                else:
                    logger.error("Analyzer: could not parse JSON from response, using fallback")
                    parsed_result = self._get_fallback_response()

            validated_result = self.validate_response_format(parsed_result)
            logger.info(
                "Analyzer: validation complete — score=%s  review=%s  notes=%d",
                validated_result["clarity_score"],
                validated_result["policy_wording_review"],
                len(validated_result["policy_notes"])
            )
            return validated_result

        except Exception as e:
            logger.error("Analyzer: unexpected error — %s", str(e), exc_info=True)
            return self._get_error_fallback_response()

    def _create_analysis_prompt(self, structured_content: str, question: str, insurance_type: str) -> str:
        """Create the analysis prompt for OpenAI"""
        return f"""
You are an expert insurance policy analyzer specializing in Product Disclosure Statements (PDS) and Schedules of Coverage. You must conduct a meticulous and conservative analysis of the {insurance_type} insurance documentation to answer the user's coverage question.

INSURANCE DOCUMENTS:
{structured_content}

USER QUESTION: {question}

INSURANCE TYPE: {insurance_type.title()} Insurance

ANALYSIS REQUIREMENTS:
1. Conduct a deep, comprehensive review of ALL relevant clauses, definitions, exclusions, and conditions specific to {insurance_type} insurance
2. Ensure strict alignment between the user's question and relevant policy terms
3. Avoid conflation of unrelated coverage areas
4. Search thoroughly for dependencies, gaps, or ambiguities
5. If multiple parties may be responsible (builders, subcontractors, engineers), flag this complexity
6. Use highly cautious framework for confidence scoring
7. If mentioning 'listed events', include at least one concrete example from the policy

CONSERVATIVE FRAMEWORK FOR CLARITY SCORE:
- "No Mention": 0–20%
- "Little Mention": 21–50%
- "Explicit Mention": 51–65%
- "Highly Explicit Mention": 66–100%

Only exceed 65% when documentation clearly supports coverage without major contingencies. If coverage depends on specific perils, conditional clauses, or unknown circumstances, assign mid-range or lower percentage.

RESPONSE FORMAT (JSON):
{{
    "policy_name": "[Policy Name extracted from document, or 'N/A' if not found]",
    "policy_price": "[Premium amount extracted from document. If premium/price is not stated in the provided documents, return exactly: 'Not stated in provided documents']",
    "policy_renewal_date": "[Policy Renewal Date extracted from Schedule, or 'N/A' if not found]",
    "clarity_score": [integer 0-100],
    "policy_wording_review": "[No Mention/Little Mention/Explicit Mention/Highly Explicit Mention]",
    "explanation": "[EXACTLY 40 words explaining the assessment, referencing relevant PDS/Schedule terms. Include third-party liability flags if applicable and listed event examples if relevant.]",
    "policy_notes": [
        "[Note 1: Must include a SPECIFIC value, amount, limit, or named exclusion extracted directly from the document. E.g. 'Flood damage excess is $2,500 per claim' or 'Storm event payout capped at $20,000'. Generic statements without document-sourced figures are NOT acceptable.]",
        "[Note 2: Another specific finding — e.g. a named exclusion, a sub-limit, or a condition that narrows or broadens typical coverage. Quote exact policy wording where possible.]",
        "[Note 3: A third notable detail — e.g. a coverage gap, an unusual clause, or a dollar/percentage figure that materially affects the user's question. Omit this note if no third substantive detail exists.]"
    ]
}}

IMPORTANT:
- Base analysis ONLY on provided documentation
- Maintain highly factual, neutral, professional tone
- Avoid speculation or overconfidence
- Provide conservative assessments with disclaimers for ambiguity
- Focus on policy interpretation, not legal advice
- policy_notes MUST contain specific figures, dollar amounts, named exclusions, or quoted policy wording extracted from the document. Vague notes like "exclusions may apply" or "excess applies to certain claims" are UNACCEPTABLE — always state the actual value or named condition found in the document.
- If the document contains coverage limits, excess amounts, sub-limits, or explicit exclusions relevant to the question, these MUST appear in policy_notes.
- If the policy is a Strata, Body Corporate, or Owners Corporation policy: explicitly clarify in the explanation or policy_notes that this policy covers the shared building structure and common property — NOT individual lot owners' internal unit contents or personal belongings, unless a Lot Owners Fixtures and Improvements section is present and applicable.
- Only include policy_notes that are directly relevant to the user's question. Do not include sections (e.g. liability limits) that are unrelated to what the user asked.

Respond with valid JSON only.
"""
    
    def _get_fallback_response(self) -> dict:
        """Get fallback response when JSON parsing fails"""
        return {
            "policy_name": "N/A",
            "policy_price": "N/A",
            "policy_renewal_date": "N/A",
            "clarity_score": 50,
            "policy_wording_review": "Little Mention",
            "explanation": "Unable to parse model response. Coverage assessment requires manual review of policy documentation for accurate determination of applicable terms and conditions.",
            "disclaimer": "This interpretation is document-based only, not advice. Seek independent financial or legal guidance.",
            "policy_notes": []
        }
    
    def _get_error_fallback_response(self) -> dict:
        """Get fallback response for technical errors"""
        return {
            "policy_name": "N/A",
            "policy_price": "N/A",
            "policy_renewal_date": "N/A",
            "clarity_score": 50,
            "policy_wording_review": "Little Mention",
            "explanation": "Technical error occurred during analysis. Coverage determination requires manual review of policy terms conditions exclusions and applicable circumstances for accurate assessment.",
            "disclaimer": "This interpretation is document-based only, not advice. Seek independent financial or legal guidance.",
            "policy_notes": []
        }