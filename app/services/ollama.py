from fastapi import HTTPException
async def ollama_extract_text_from_image(image_path:str,prompt:str) -> str:
    from app.config import ollamaClient
    from httpx import Response
    print(f"Using Ollama Client: {ollamaClient}")
    # print(image_path)
    data = {
        "model" : "gemma3:4b-it-qat",
        "prompt": prompt,
        "stream" : False,
        "images" : [
            image_path.replace('data:image/png;base64,','')
        ]
    }
    print(prompt)

    try : 
        response: Response = await ollamaClient.post(url="/api/generate", json=data, timeout=40)
    
        print(response.json())
        result = response.json()
        if response.status_code == 200:
            result = response.json()
            return result['response']
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Request failed: {response.text}")
        

    except Exception as e:
        print(f"Error occurred: {e}")
        return
   
