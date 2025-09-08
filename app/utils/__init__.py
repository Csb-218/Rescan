import pdfplumber
from fastapi import HTTPException , File , UploadFile 
from pathlib import Path
from PIL import Image
import base64

# imports for vector similarity
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

UPLOAD_DIR = Path("app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # ensure folder exists

ALLOWED_TYPES = {"application/pdf"}
ALLOWED_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

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


async def validate_and_save_files(jd: UploadFile = File(...), resume: UploadFile = File(...)) -> tuple:
    
    # Check if no resume or jd provided
    if not jd or not resume:
        raise HTTPException(
            status_code=400,
            detail="Both JD and Resume files must be provided."
        )

    saved_paths = []

    for f in (jd, resume):

        #check if not corrupted file
        if not hasattr(f,"content_type"):
            raise HTTPException(
                status_code=400,
                detail="Both JD and Resume files must be provided."
            )

        # check if filetype allowed
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only PDF files are allowed."
            )
        
         # check file size 
        if f.size is None or f.size <= 1 :
             raise HTTPException(
                status_code=400,
                detail="Both JD and Resume files must not be empty."
            )
        
        # check if file size exceeds limit
        if f.size > ALLOWED_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds the 5 MB limit."
            )

        # check if filename is valid
        if not f.filename:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must have a valid filename."
            )

        save_path = UPLOAD_DIR / f.filename
        # Ensure saved_path is a Path object, not a string
        with open(save_path, "wb") as buffer:
            buffer.write(await f.read())
        saved_paths.append(save_path)

    return jd, resume, saved_paths

def match_calculator(jd_content:str , resume_content:str) :
    """
    Calculate the match percentage between JD and resume content.
    
    Args:
        jd_content (str): Job Description content.
        resume_content (str): Resume content.
        
    Returns:
        float: Match percentage.
    """
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    embeddings = model.encode([resume_content,jd_content],normalize_embeddings=True)
    # print(embeddings)
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    print(f"Similarity Score: {sim}")
    return sim*100


match_score_logic = """
Match Score Logic

NOTE : If the Resume has less than minimum required experience , the dont evaluate further and straightly reject .

1. Skills (50 points)

    Calculate ratio of matching_skills / jd_skills.

    Score = ratio * 50.

    Example: JD requires 10 skills, resume has 7 → (7/10)*50 = 35 points.

2. Experience (30 points)

    If  experience_years >= JD years → full 30.

    If less, partial credit: experience_years / jd_years * 30.

    Example: 
            - JD requires minimum of 5 years, resume has maximum 3 years then count it as 0.
            - Calculate carefully , if resume has 6 months of experience then count it as 0.5 years and if resume has 3 months of experience then count it as 0.25 years.
            - If experience required is 3-5 years, resume has 4 then count it as (4/5)*30 = 24 .
            - Always return YOE(Years of Experience).
            

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

                        