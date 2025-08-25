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
    _pass: bool = False | True  # Default to False, can be overridden based on match_score


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

def parse_resume_analysis(ollama_response: dict) -> JDResumeMatch:
    # Extract string JSON inside `message.content`
    raw_content = ollama_response["result"]["message"]["content"]

    # Convert to dict
    parsed_content = json.loads(raw_content)

    # The real data is inside "properties"
    props = parsed_content.get("properties", {})

    return JDResumeMatch(
        jd_skills=props.get("jd_skills", {}).get("items", []),
        resume_skills=props.get("resume_skills", {}).get("items", []),
        matching_skills=props.get("matching_skills", []),
        missing_skills=props.get("missing_skills", []),
        experience_match=props.get("experience_match", ""),
        education_match=props.get("education_match", ""),
        match_score=props.get("match_score", 0),
        improvement_suggestions=props.get("improvement_suggestions", ""),
        _pass=props.get("match_score", 0) > 70  # example threshold
    )

