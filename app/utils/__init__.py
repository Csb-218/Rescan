import pdfplumber
from fastapi import HTTPException , File , UploadFile 
from pathlib import Path
from PIL import Image
import base64

# imports for vector similarity
# from sklearn.metrics.pairwise import cosine_similarity
# from sentence_transformers import SentenceTransformer

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # ensure folder exists

ALLOWED_TYPES = {"application/pdf","image/png","image/jpeg","image/jpg"}

def extract_text_from_pdf(pdf_path:str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text from the PDF.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() + '\n'
    return text.strip()

def image_to_base64(image_path:str) -> str:
    """
    Convert an image file to a base64-encoded string.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Base64-encoded string of the image.
    """
    with open(image_path, "rb") as f:
        encoded_image = base64.b64encode(f.read())
        return encoded_image.decode("utf-8")


async def validate_and_save_files(jd: UploadFile = File(...), resume: UploadFile = File(...))-> tuple:

    saved_paths = []

    for f in (jd, resume):
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{f.content_type}' is not allowed.c"
            )
        # Save the file temporarily
        save_path = UPLOAD_DIR / f.filename
        with open(save_path, "wb") as buffer:
            buffer.write(await f.read())
        saved_paths.append(save_path)

    return jd, resume, saved_paths

def match_calculator(jd_content:str , resume_content:str) -> float:
    """
    Calculate the match percentage between JD and resume content.
    
    Args:
        jd_content (str): Job Description content.
        resume_content (str): Resume content.
        
    Returns:
        float: Match percentage.
    """
    # model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    # embeddings = model.encode([resume_content,jd_content],normalize_embeddings=True)

    # sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    # print(f"Similarity Score: {sim}")
    # return sim*100


match_score_logic = """
Match Score Logic

NOTE : If the Resume has less than minimum required experience , the dont evaluate further and straightly reject .

1. Skills (50 points)

    Calculate ratio of matching_skills / jd_skills.

    Score = ratio * 50.

    Example: JD requires 10 skills, resume has 7 → 7/10 = 0.7 → 35/50 points.

2. Experience (30 points)

    If  experience_years >= JD years → full 30.

    If less, partial credit: experience_years / jd_years * 30.

    Example: 
            - JD requires minnimum of 5 years, resume has maximum 3 years then count it as 0.
            - Calculate carefully , if resume has 6 months of experience then count it as 0.5 years and if resume has 3 months of experience then count it as 0.25 years.
            - If experience required is 3-5 years, resume has 4 then count it as 20/25.

3. Education (20 points)

    If education exactly matches (degree or equivalent) → full 20.

    If partially relevant (e.g., JD requires B.Tech but resume has diploma) → 10.

    If missing/wrong → 0.



• match_score = skill_score + experience_score + education_score

_pass = True only if:
 
    • match_score >= 70

    • AND experience >= JD minimum

    • AND at least 90% of jd_skills are matched.

"""

result_schema = {
                        "jd_skills": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "resume_skills": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "matching_skills": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "missing_skills": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                         "YOE_required": {
                            "type": "integer",
                            "description": "Years of experience required by the job description"
                        },
                        "YOE_provided": {
                            "type": "integer",
                            "description": "Years of experience provided by the candidate"
                        },
                        "YOE_match": {
                            "type": "string",
                            "description": "Write if candidate meets minimum experience requirements"
                        },
                        "education_required": {
                            "type": "string",
                            "description": "Education level required by the job description"
                        },
                        "education_provided": {
                            "type": "string",
                            "description": "Education level provided by the candidate"
                        },
                        "education_match": {
                            "type": "string",
                            "description": "Write if candidate meets minimum education requirements"
                        },
                        "match_score": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "improvement_suggestions": {
                            "type": "string"
                        },
                        "_pass": {
                            "type": "boolean"
                        }
                    }