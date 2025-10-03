
from fastapi import APIRouter, Depends, HTTPException 
from fastapi.responses import JSONResponse
import os
from app.services.ollama import ollama_match_resume_jd , ollama_convert_raw_text_to_json
from app.utils import extract_text_from_pdf , validate_and_save_files , match_calculator , validate_and_save_file
from app.utils.jd_utils import JDParser
from app.utils.resume_utlis import ResumeParser
from app.schemas import TypeEnum
# from pyresparser import ResumeParser as parser_pyresparser


AnalyzeRouter = APIRouter(
    prefix="/api/analyze",
    tags=["analyze"],
    responses={
        200: {"description": "Successful operation"},
        400: {"description": "Bad request"}
    }
)


@AnalyzeRouter.post(
    path="/read_file" ,
    summary="Analyzes Resume and JD match" ,
    responses={
        200:{
           "result": {
                "jd": "resume_cs_bhagwant.pdf",
                "content": "C.S Bhagwant\n9861289352 | csbhagwant@gmail.com | LinkedIn | Github | Twitter\nEXPERIENCE\nFreelance Fullstack Developer Nov 2024 - Jan 2025\nFounders Careers (Remote)\n● ...",
             }
        },
        400:{"message":"Both Resume and JD(Job Description) are required."}
    }
    )

async def readFile(files: tuple = Depends(validate_and_save_file)) :
    jd, saved_paths = files
    
   
    try : 
        jd_content =  extract_text_from_pdf(saved_paths[0])
        parsed_jd = await ollama_convert_raw_text_to_json(jd_content, TypeEnum.jd)
        result = {
            "jd": jd.filename,
            "content": parsed_jd
        }

        return JSONResponse(content={"result": result}, status_code=200 )
    
    except Exception as err:
        print(f"Error during analysis: {err}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the files.")

    finally:
        # Cleanup saved files
        for path in saved_paths:
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")


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
    
   
    try : 
        jd_content =  extract_text_from_pdf(saved_paths[0])
        resume_content =  extract_text_from_pdf(saved_paths[1])
        jd_parser = JDParser(jd_content)
        print(11,jd_parser)
        req_skills = jd_parser.extract_skills()
        print(12,req_skills)
        resume_parser = ResumeParser(resume_content, required_skills=req_skills)
        print(13,resume_parser)
        match_percentage = match_calculator(jd_content, resume_content)
        print(14,match_percentage)
        result = {
            "jd": jd.filename,
            "analyzed_jd" : jd_parser.parse(),
            "resume": resume.filename,
            "analyzed_resume" : resume_parser.parse(),
            "match percentage": f"{match_percentage:.2f}%"
        }

        return JSONResponse(content={"result": result}, status_code=200 )
    
    except Exception as err:
        print(f"Error during analysis: {err}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the files.")

    finally:
        # Cleanup saved files
        for path in saved_paths:
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")


@AnalyzeRouter.post(
    path='/parse',
    summary='Parses Resume and JD content'
)
async def parse(files: tuple = Depends(validate_and_save_files)):
    jd, resume, saved_paths = files
    # data = parser_pyresparser(saved_paths[1]).get_extracted_data()
    # print(data)
    try:
        jd_content = extract_text_from_pdf(saved_paths[0])
        jd_json = await ollama_convert_raw_text_to_json(jd_content, TypeEnum.jd)
        # jd_parsed = JD.model_validate(jd_response)
        resume_content = extract_text_from_pdf(saved_paths[1])
        resume_json = await ollama_convert_raw_text_to_json(resume_content, TypeEnum.resume)
        # resume_parsed = Resume.model_validate(resume_json)
        return JSONResponse(content={"jd": jd_json, "resume": resume_json}, status_code=200)

    except Exception as err:
        print(f"Error during parsing: {err}")
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

    try : 

        jd_content =  extract_text_from_pdf(saved_paths[0])
        jd_json = await ollama_convert_raw_text_to_json(jd_content, TypeEnum.jd)
        resume_content =  extract_text_from_pdf(saved_paths[1])
        resume_json = await ollama_convert_raw_text_to_json(resume_content, TypeEnum.resume)

        if not jd_json or not resume_json:
            raise HTTPException(status_code=500, detail="Failed to parse JD or Resume content.")
        
        result = await ollama_match_resume_jd(jd_json, resume_json)
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

