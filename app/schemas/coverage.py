from pydantic import BaseModel
from typing import List


class CoverageRequest(BaseModel):
    question: str

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Is storm damage to my roof covered under this policy?"
            }
        }


class CoverageResponse(BaseModel):
    policy_name: str = "N/A"
    user_question: str
    direct_answer: str          # NEW: one-line verdict returned first
    explanation: List[str]
    explanation_summary: str
    policy_notes: List[str]
    policy_price: str
    final_summary: str

    class Config:
        json_schema_extra = {
            "example": {
                "policy_name": "CGU Steadfast Home Insurance (Listed Events Cover)",
                "user_question": "Am I covered for water coming through my walls?",
                "direct_answer": "Conditional — depends on whether entry was caused by an insured event.",
                "explanation": [
                    "Storm, Flood, Rainwater, Wind covers water damage caused directly by storm or rainwater.",
                    "Storm, Flood, Rainwater, Wind excludes ingress caused by structural defects, faulty design, or workmanship.",
                    "Escape of Liquid covers sudden escape from pipes or fixtures but excludes gradual seepage.",
                    "Listed Events Cover means damage is only covered where linked to a named insured event.",
                ],
                "explanation_summary": (
                    "Coverage depends on whether water entry was caused by a listed insured event "
                    "or by a structural or gradual cause."
                ),
                "policy_notes": [
                    "Water damage exclusion — structural ingress not covered (Storm, Flood, Rainwater, Wind)",
                    "Structural defect exclusion — faulty design/workmanship excluded (Storm, Flood, Rainwater, Wind)",
                    "Gradual damage exclusion — seepage and non-sudden damage excluded (Escape of Liquid)",
                    "Source repair exclusion — defective pipe or fitting not covered (Escape of Liquid)",
                    "Listed events limitation — only named events trigger cover (Listed Events Cover)",
                    "Excess payable — deducted per claim (Excess / Paying Claims)",
                ],
                "policy_price": "Not listed in provided documents",
                "final_summary": (
                    "Coverage is determined by the Storm, Flood, Rainwater, Wind and Escape of Liquid "
                    "clauses within a Listed Events Cover structure."
                ),
            }
        }


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model: str