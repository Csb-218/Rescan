
from fastapi import APIRouter, Depends, HTTPException 
from fastapi.responses import JSONResponse
import os
from app.services.ollama import ollama_match_resume_jd
from app.utils import extract_text_from_pdf , validate_and_save_files , match_calculator 
from app.utils.jd_utils import JDParser
from app.utils.resume_utlis import ResumeParser



AnalyzeRouter = APIRouter(
    prefix="/analyze",
    tags=["analyze"],
    responses={
        200: {"description": "Successful operation"},
        400: {"description": "Bad request"}
    }
)


@AnalyzeRouter.post(
    path="/" ,
    summary="Analyzes Resume and JD match" ,
    responses={
        200:{
           "result": {
                "jd": "resume_cs_bhagwant.pdf",
                "content1": "C.S Bhagwant\n9861289352 | csbhagwant@gmail.com | LinkedIn | Github | Twitter\nEXPERIENCE\nFreelance Fullstack Developer Nov 2024 - Jan 2025\nFounders Careers (Remote)\n● ...",
                "resume": "AI First Full Stack Engineer __ Wednesday.pdf",
                "content2": "AI-first Full Stack Engineer @ Wednesday\nAbout the company:\nWednesday is a global technology consultancy. We integrate technology strategy, engineering,\nand design to ..."
             }
        },
        400:{"message":"Both Resume and JD(Job Description) are required."}
    }
    )

async def analyze(files: tuple = Depends(validate_and_save_files)) :
    jd, resume , saved_paths = files
    print(saved_paths)
    jd_content =  extract_text_from_pdf(saved_paths[0])
    resume_content =  extract_text_from_pdf(saved_paths[1])
    try : 

        jd_parser = JDParser(jd_content)
        req_skills = jd_parser.extract_skills()
        resume_parser = ResumeParser(resume_content, required_skills=req_skills)
        match_percentage = match_calculator(jd_content, resume_content)
        result = {
            "jd": jd.filename,
            "analyzed_jd" : jd_parser.parse(),
            "resume": resume.filename,
            "analyzed_resume" : resume_parser.parse(),
            "match percentage": f"{match_percentage:.2f}%"
        }

        return JSONResponse(content={"result": result}, status_code=200 )
    
    except:
        return HTTPException(status_code=500, detail="An error occurred while processing the files.")

    finally:
        # Cleanup saved files
        for path in saved_paths:
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

@AnalyzeRouter.post(
    path="/advanced" ,
    summary="Analyzes Resume and JD match using llms" ,
    responses={
        200:{
           "result": {
                "jd": "resume_cs_bhagwant.pdf",
                "content1": "C.S Bhagwant\n9861289352 | csbhagwant@gmail.com | LinkedIn | Github | Twitter\nEXPERIENCE\nFreelance Fullstack Developer Nov 2024 - Jan 2025\nFounders Careers (Remote)\n● ...",
                "resume": "AI First Full Stack Engineer __ Wednesday.pdf",
                "content2": "AI-first Full Stack Engineer @ Wednesday\nAbout the company:\nWednesday is a global technology consultancy. We integrate technology strategy, engineering,\nand design to ..."
             }
        },
        400:{"message":"Both Resume and JD(Job Description) are required."}
    }
    )

async def analyze_advanced(files: tuple = Depends(validate_and_save_files)):
    jd, resume , saved_paths = files

    jd_content =  extract_text_from_pdf(saved_paths[0])
    resume_content =  extract_text_from_pdf(saved_paths[1])

    try : 

        result = await ollama_match_resume_jd(jd_content, resume_content)
        return JSONResponse(content={"result": result}, status_code=200)

    except Exception as err:
        print(f"Error during analysis: {err}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while processing the files: {str(err)}"
        )

    finally:
        # Cleanup saved files
        for path in saved_paths:
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

