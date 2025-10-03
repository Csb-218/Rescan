from fastapi import HTTPException
from httpx import Response
from app.schemas import OllamaResponse,JDResumeMatch,Result,JD,Resume,TypeEnum
from app.utils import match_score_logic 
from app.config import ollamaClient
import json

async def log(event_name, info):
    print(event_name, info)

# async def ollama_extract_text_from_image(image_path:str,prompt:str) -> str | None:
#     from app.config import ollamaClient
#     from httpx import Response
#     print(f"Using Ollama Client: {ollamaClient}")
#     # print(image_path)
#     data = {
#         "model" : "gemma3:4b-it-qat",
#         "prompt": prompt,
#         "stream" : False,
#         "images" : [
#             image_path.replace('data:image/png;base64,','')
#         ]
#     }
#     print(prompt)

#     try : 
#         response: Response = await ollamaClient.post(url="/api/generate", json=data, timeout=40)
    
#         print(response.json())
#         result = response.json()
#         if response.status_code == 200:
#             result = response.json()
#             return result['response']
#         else:
#             raise HTTPException(status_code=response.status_code, detail=f"Request failed: {response.text}")
        

#     except Exception as e:
#         print(f"Error occurred: {e}")
#         return
   

async def ollama_convert_raw_text_to_json(raw_text:str,type:TypeEnum) -> dict | None:

    try:

        json_schema = JD.model_json_schema() if type == TypeEnum.jd else Resume.model_json_schema()

        system_prompt:str = f'''

        Instruction: Read the text provided. It can be either a job description or a resume. Read the text carefully and extract all the relevant information and fill in a json format provided below .
        Note : Calculate years of experience precisely.

        Text:
        ###
        {raw_text}
        ###

        ---------------------------------------------------------------------------------------------------------------------
        Json Schema : 
        ###
        {json_schema}
        ###
        '''

        body:dict = {
                "model": "granite3.1-moe:1b",
                "prompt": system_prompt,
                "stream": False,
                "format" : json_schema
        }

        response: Response = await ollamaClient.post(url="/api/generate", json=body, extensions={"trace": log},timeout=240)
        if response.status_code == 200:
            raw_response = response.json()
            parsed_response:Result = Result.model_validate(raw_response)
            validated_response:JD | Resume = JD.model_validate(json.loads(parsed_response.response)) if type == TypeEnum.jd else Resume.model_validate(json.loads(parsed_response.response))
            result_json:dict = json.loads(validated_response.model_dump_json())
            return result_json
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Request failed: {response.text}")
    except Exception as e:
        print(f"Error occurred: {e}")
        return


async def ollama_match_resume_jd(jd:dict,resume:dict)-> object | None :
        
    try :       
            
            system_prompt:str = f'''
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
        6. Use the calculated YOE to assess if the candidate meets the JD’s required years of experience.  

        Output strictly in the given JSON schema, without explanations, markdown, or extra keys.  

        ---------------------------------------------------  
        job description:  
        {jd}  
        ---------------------------------------------------  

        ---------------------------------------------------  
        resume:  
        {resume}  
        ---------------------------------------------------  

        IMPORTANT:  
        {match_score_logic}  

'''

            body:dict = {
                "model": "llama3.2:latest",
                "prompt": system_prompt,
                "stream": False,
                "format" : JDResumeMatch.model_json_schema()
            }
        
            response:Response = await ollamaClient.post(url='/api/generate', json=body, extensions={"trace": log},timeout=240)


            if response.status_code != 200:
                 print(f"Request failed with status {response.status_code}: {response.json()}")
                 raise HTTPException(status_code=response.status_code, detail=f"Request failed")
                 
 
            raw_response = response.json()
            # print(99,raw_response,'\n')
            validated_response = OllamaResponse.model_validate({"result":raw_response})
            # print('100',validated_response,'\n')
            result = JDResumeMatch.model_validate_json(json_data=validated_response.result.response)
            # print(result)
            result_json:object = json.loads(result.model_dump_json())
            return result_json

    except Exception as err:
            print(f"Error during analysis: {type(err).__name__}")
            print(f"Error details: {str(err)}")
            import traceback
            traceback.print_exc()  # Print full stack trace
            return None
