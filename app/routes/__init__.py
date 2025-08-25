from unittest import result
from fastapi import APIRouter, Depends, HTTPException , UploadFile , File
from fastapi.responses import JSONResponse
import os
from app.services.ollama import ollama_extract_text_from_image
from app.utils import extract_text_from_pdf , validate_and_save_files , match_calculator , match_score_logic , result_schema ,image_to_base64
from app.utils.jd_utils import JDParser
from app.utils.resume_utlis import ResumeParser
from app.schemas import OllamaResponse,JDResumeMatch,Result,ImageToText
import json



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
    # print(saved_paths)
    # return JSONResponse(
    #                 content={"result": "received"}, 
    #                 status_code=200
    #             )
     # Check if resume is pdf
    resume_extension = saved_paths[1].suffix.lower().replace('.', '')
    print(resume_extension)
    match resume_extension:
        case 'pdf':
            resume_content =  extract_text_from_pdf(saved_paths[1])
        case 'png' | 'jpg' | 'jpeg':
            base64_image = image_to_base64(str(saved_paths[1]))
            # Get only the "properties" from the schema, removing "required", "title", and "type"
            schema = ImageToText.model_json_schema()
            properties_only = json.dumps(schema.get("properties", {}), indent=2)
            prompt = f"""
               Extract information from the image and return a filled json object with the following properties:
               {properties_only}
            """
            resume_content = await ollama_extract_text_from_image(base64_image,prompt)
            print(resume_content)

    jd_content =  extract_text_from_pdf(saved_paths[0])

    try : 

        system_prompt = f'''
        You are an expert career assistant and recruiter. 
        Your task is to analyze a job description (JD) and a candidate resume, then provide structured feedback on how well they match. 

        Follow these rules:
        1. Extract key requirements from the JD (skills, education, years of experience, tools/technologies).
        2. Extract key qualifications from the resume.
        3. Compare JD vs Resume and identify:
        - Matching skills
        - Missing skills
        - Relevant experiences
        - Gaps in education or years of experience
        4. Give an overall match score from 0–100 with justification.
        5. Suggest how the resume could be improved to better match the JD.

        IMPORTANT:
        {match_score_logic}
        
        Respond ONLY in the json schema provided.
            
        ---------------------------------------------------
        job description :  
        {jd_content}
        ----------------------------------------------------
 
        ----------------------------------------------------
        resume : 
        {resume_content}
        ----------------------------------------------------

        Do not add explanations, markdown formatting, or extra keys.

        '''
        model:str = "llama3.2"
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        body = {
            "model": model,
            "prompt": system_prompt,
            "stream": False,
            "temperature": 0.2,
            "format": {
                "type": "object",
                "properties": json.loads(json.dumps(result_schema, indent=2)),
                "required": [
                    "jd_skills",
                    "resume_skills",
                    "matching_skills",
                    "missing_skills",
                    "YOE_required",
                    "YOE_provided",
                    "YOE_match",
                    "education_required",
                    "education_provided",
                    "education_match",
                    "match_score",
                    "improvement_suggestions",
                    "_pass"
                ]
            }
            
        }
        print('\n')
        # print(body)
        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            try:
                raw_response = response.json()
                # Create a Result object first
                result_obj = Result(
                    model=raw_response.get("model", ""),
                    created_at=raw_response.get("created_at", ""),
                    response=raw_response.get("response", ""),
                    done_reason=str(raw_response.get("done_reason", "")), 
                    done=raw_response.get("done", False),
                    context=raw_response.get("context", []),
                    total_duration=raw_response.get("total_duration", 0),
                    load_duration=raw_response.get("load_duration", 0),
                    prompt_eval_count=raw_response.get("prompt_eval_count", 0),
                    prompt_eval_duration=raw_response.get("prompt_eval_duration", 0),
                    eval_count=raw_response.get("eval_count", 0),
                    eval_duration=raw_response.get("eval_duration", 0)
                )
                
                # Create OllamaResponse with the Result object
                validated_response = OllamaResponse(result=result_obj)
                
                # Parse the response content as JDResumeMatch
                content = json.loads(validated_response.result.response)
                analyzed_result = JDResumeMatch(**content)
                
                return JSONResponse(
                    content={"result": json.loads(analyzed_result.json())}, 
                    status_code=200
                )

            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Invalid JSON in response: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Validation error: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Request failed: {response.text}"
            )

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

# @AnalyzeRouter.post(
#     path="/image-read",
#     response_description="Extracted text from image",
# )

# async def ollama_extract_text_from_image( prompt: str,files: tuple = Depends(validate_and_save_files)) -> str:
#     from app.config import ollamaClient
#     from httpx import Response
#     jd, resume , saved_paths = files
#     print(f"Using Ollama Client: {ollamaClient}")
#     image_path = saved_paths[1]
#     base64_image = image_to_base64(str(image_path))
#     data = {
#         "model" : "gemma3:4b-it-qat",
#         "prompt": prompt,
#         "stream" : False,
#         "images" : [
#             base64_image.replace('data:image/png;base64,','')
#         ]
#     }
#     print(prompt)

#     try : 
#         response: Response = await ollamaClient.post(url="/api/generate", json=data, timeout=40)
#         print(response.text)
#         print(response.json())
#         if response.status_code == 200:
#             result = response.json()
#             return result['response']
#         else:
#             raise HTTPException(status_code=response.status_code, detail=f"Request failed: {response.text}")

#     except Exception as e:
#         print(f"Error occurred: {e}")
#         raise HTTPException(status_code=500, detail=f"Error occurred: {e}")