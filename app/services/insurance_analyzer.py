from typing import Dict
import re
import json
from openai import OpenAI
from app.core.config import get_settings

class InsuranceAnalyzer:
    """Service for analyzing insurance coverage based on policy documents"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.likelihood_ranges = {
            "Highly Unlikely": (0, 20),
            "Unlikely": (21, 50),
            "Somewhat Likely": (51, 65),
            "Likely": (66, 80),
            "Highly Likely": (81, 100)
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
        
        # Ensure percentage score is within valid range
        percentage = result.get("percentage_score", 50)
        if not isinstance(percentage, int) or percentage < 0 or percentage > 100:
            percentage = 50
        
        # Map percentage to correct likelihood ranking
        likelihood_ranking = "Somewhat Likely"  # default
        for ranking, (min_val, max_val) in self.likelihood_ranges.items():
            if min_val <= percentage <= max_val:
                likelihood_ranking = ranking
                break
        
        # Ensure explanation is exactly 40 words
        explanation = result.get("explanation", "Coverage assessment unavailable due to insufficient information in provided documentation.")
        words = explanation.split()
        if len(words) != 40:
            if len(words) > 40:
                explanation = " ".join(words[:40])
            else:
                # Pad with additional context if too short
                padding_words = ["based", "on", "policy", "terms", "and", "conditions", "provided", "in", "documentation"]
                while len(words) < 40 and padding_words:
                    words.append(padding_words.pop(0))
                explanation = " ".join(words[:40])
        
        return {
            "percentage_score": percentage,
            "likelihood_ranking": likelihood_ranking,
            "explanation": explanation
        }

    def analyze_coverage(self, pdf_content: str, question: str, insurance_type: str) -> dict:
        """Analyze insurance coverage based on PDF content and user question"""
        
        # Structure the content
        structured_content = self.clean_and_structure_text(pdf_content)
        
        # Create the enhanced prompt based on model instructions
        prompt = self._create_analysis_prompt(structured_content, question, insurance_type)

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
            
            result = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                # Try to extract JSON from the response if it's wrapped in other text
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    parsed_result = json.loads(json_match.group())
                else:
                    parsed_result = self._get_fallback_response()
            
            # Validate and format response according to model instructions
            validated_result = self.validate_response_format(parsed_result)
            return validated_result
                    
        except Exception as e:
            # Fallback response for any errors
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

CONFIDENCE SCORING FRAMEWORK:
- "Highly Unlikely": 0–20%
- "Unlikely": 21–50%
- "Somewhat Likely": 51–65%
- "Likely": 66–80%
- "Highly Likely": 81–100%

Only exceed 65% when documentation clearly supports coverage without major contingencies. If coverage depends on specific perils, conditional clauses, or unknown circumstances, assign mid-range or lower percentage.

RESPONSE FORMAT (JSON):
{{
    "percentage_score": [integer 0-100],
    "likelihood_ranking": "[Highly Unlikely/Unlikely/Somewhat Likely/Likely/Highly Likely]",
    "explanation": "[EXACTLY 40 words explaining the assessment, referencing relevant PDS/Schedule terms. Include third-party liability flags if applicable and listed event examples if relevant.]"
}}

IMPORTANT:
- Base analysis ONLY on provided documentation
- Maintain highly factual, neutral, professional tone
- Avoid speculation or overconfidence
- Provide conservative assessments with disclaimers for ambiguity
- Focus on policy interpretation, not legal advice

Respond with valid JSON only.
"""
    
    def _get_fallback_response(self) -> dict:
        """Get fallback response when JSON parsing fails"""
        return {
            "percentage_score": 50,
            "likelihood_ranking": "Somewhat Likely",
            "explanation": "Unable to parse model response. Coverage assessment requires manual review of policy documentation for accurate determination of applicable terms and conditions."
        }
    
    def _get_error_fallback_response(self) -> dict:
        """Get fallback response for technical errors"""
        return {
            "percentage_score": 50,
            "likelihood_ranking": "Somewhat Likely",
            "explanation": "Technical error occurred during analysis. Coverage determination requires manual review of policy terms conditions exclusions and applicable circumstances for accurate assessment."
        }