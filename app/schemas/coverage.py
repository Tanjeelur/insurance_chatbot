

from pydantic import BaseModel
from typing import Dict
from datetime import datetime

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
    policy_price: str = "N/A"
    policy_renewal_date: str = "N/A"
    clarity_score: int
    policy_wording_review: str
    explanation: str
    disclaimer: str
    policy_notes: list
    
    class Config:
        json_schema_extra = {
            "example": {
                "policy_name": "Comprehensive Home Insurance",
                "policy_price": "1200.00",
                "policy_renewal_date": "2024-12-01T00:00:00Z",
                "clarity_score": 65,
                "policy_wording_review": "Explicit Mention",
                "explanation": "Coverage appears applicable under storm damage provisions, subject to deductible requirements and specific policy conditions outlined in the schedule documentation.",
                "disclaimer": "This interpretation is document-based only, not advice. Seek independent financial or legal guidance.",
                "policy_notes": [
                    "Policy includes storm damage coverage with a $500 deductible.",
                    "Certain exclusions may apply as detailed in section 4.2 of the policy document."
                ]
            }
        }

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model: str