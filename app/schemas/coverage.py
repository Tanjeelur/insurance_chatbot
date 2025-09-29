# from pydantic import BaseModel
# from typing import Dict
# from datetime import datetime

# class CoverageRequest(BaseModel):
#     question: str
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "question": "Is storm damage to my roof covered under this policy?"
#             }
#         }

# class CoverageResponse(BaseModel):
#     percentage_score: int
#     likelihood_ranking: str
#     explanation: str
#     # session_id: str
#     # timestamp: str
#     # processing_info: Dict
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "percentage_score": 65,
#                 "likelihood_ranking": "Somewhat Likely",
#                 "explanation": "Coverage appears applicable under storm damage provisions, subject to deductible requirements and specific policy conditions outlined in the schedule documentation.",
#                 # "session_id": "123e4567-e89b-12d3-a456-426614174000",
#                 # "timestamp": "2024-08-14T10:30:00Z",
#                 # "processing_info": {
#                 #     "policy_pages_extracted": 15,
#                 #     "schedule_pages_extracted": 3,
#                 #     "total_characters": 45000,
#                 #     "question_length": 50
#                 # }
#             }
#         }

# class HealthResponse(BaseModel):
#     status: str
#     timestamp: str
#     model: str

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
    clarity_score: int
    policy_wording_review: str
    explanation: str
    disclaimer: str
    policy_notes: list
    # timestamp: str
    # processing_info: Dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "clarity_score": 65,
                "policy_wording_review": "Explicit Mention",
                "explanation": "Coverage appears applicable under storm damage provisions, subject to deductible requirements and specific policy conditions outlined in the schedule documentation.",
                "disclaimer": "This interpretation is document-based only, not advice. Seek independent financial or legal guidance.",
                # "session_id": "123e4567-e89b-12d3-a456-426614174000",
                # "timestamp": "2024-08-14T10:30:00Z",
                # "processing_info": {
                #     "policy_pages_extracted": 15,
                #     "schedule_pages_extracted": 3,
                #     "total_characters": 45000,
                #     "question_length": 50
                # }
            }
        }

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model: str