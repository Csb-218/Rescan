from pydantic import BaseModel
import json
from typing import List, Optional

class Reason(BaseModel):
    field: str
    value_required: Optional[str] = None
    value_provided: Optional[str] = None


class ImprovementSuggestion(BaseModel):
    field: str
    suggested_value: Optional[str] = None
    suggested_action: Optional[str] = None


class JDResumeMatch(BaseModel):
    jd_skills: List[str]
    resume_skills: List[str]
    matching_skills: List[str]
    missing_skills: List[str]
    YOE_required: int
    YOE_provided: int
    YOE_match: str
    education_required: str
    education_provided: str
    education_match: str
    match_score: int
    improvement_suggestions: Optional[str] = None
    resume_pass: bool  


class Result(BaseModel):
    model: str
    created_at: str
    response: str
    done_reason: str
    done: bool
    context: List[int]
    total_duration: int
    load_duration: int
    prompt_eval_count: int
    prompt_eval_duration: int
    eval_count: int
    eval_duration: int


class OllamaResponse(BaseModel):
    result: Result

class ImageToText(BaseModel):
    skills : List[str]
    experience : List[str]
    education : List[str]



