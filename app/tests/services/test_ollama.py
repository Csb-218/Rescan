import pytest
from fastapi import HTTPException
from app.config import ollamaClient
# from app.services.ollama import ollama_extract_text_from_image
from app.schemas import JDResumeMatch,OllamaResponse
from app.services.ollama import ollama_match_resume_jd
import json

result = {
                "jd_skills": [ "React/Next.js" ],
                "resume_skills": ["Firebase"],
                "matching_skills": ["HTML"],
                "missing_skills": ["Firebase"],
                "YOE_required": 3,
                "YOE_provided": 2,
                "YOE_match": "If YOE_provided < YOE_required, do not evaluate further and reject.",
                "education_required": "Bachelor of Technology in Computer Science and Engineering",
                "education_provided": "Bachelor of Technology in Computer Science and Engineering",
                "education_match": "If education_provided == education_required, match 20 points.",
                "match_score": 80,
                "improvement_suggestions": None,
                "resume_pass": True
         }

raw_response = {'model': 'llama3.2:latest', 'created_at': '2025-08-29T07:34:08.1276993Z', 'response': json.dumps(result), 'done': True, 'done_reason': 'stop', 'context': [128006, 9125, 128007], 'total_duration': 158669502600, 'load_duration': 3197242500, 'prompt_eval_count': 1559, 'prompt_eval_duration': 103765518800, 'eval_count': 394, 'eval_duration': 51703671200}

@pytest.mark.asyncio
async def test_ollama_match_resume_jd_success(
        monkeypatch
        ):
            
        """
        Test the `ollama_match_resume_jd` function for successful matching of a resume and job description.
        This test uses monkeypatching to mock external dependencies and responses:
        - Mocks the HTTP response from `ollamaClient.post`.
        - Mocks the model validation and JSON loading for `OllamaResponse` and `JDResumeMatch`.
        - Verifies that the function returns the expected dictionary containing the mock result.
        Args:
            monkeypatch: pytest's monkeypatch fixture for patching objects.
        Asserts:
            The result of `ollama_match_resume_jd` matches the expected mock dictionary.
        """
            


        jd = "JD text"
        resume = "Resume text"
            
        global result

        class MockResponse:
                # mock json() method always returns a specific testing dictionary
            @staticmethod
            def json():
                    return raw_response

            @property
            def status_code(self):
                    return 200
            
        class MockJDResumeMatch:
                @staticmethod
                def model_validate_json(*args,**kwargs):
                    return {
                                "mock_key": "mock_response",
                                "result" : result
                            }

                
                @staticmethod
                def model_dump_json(*args, **kwargs):
                        return {"mock_key": "mock_response"}

        class MockOllamaResponse:
                
                def __init__(self, *args, **kwargs):
                        self.result = type('obj',(object,),{
                            "response": result
                        })

            

        async def set_response(*args,**kwargs):
                  return MockResponse()
            
        def mock_model_validate(*args,**kwargs):
                 return MockOllamaResponse()
        def mock_model_validate_json(*args, **kwargs):
                  return MockJDResumeMatch()
            
        def mock_json_loads(*args,**kwargs):
                  return {"mock_key": "mock_response" , "result" : result}

        # patches 
        monkeypatch.setattr(ollamaClient, "post", set_response)
        monkeypatch.setattr(OllamaResponse, "model_validate" , mock_model_validate)
        monkeypatch.setattr(JDResumeMatch, "model_validate_json", mock_model_validate_json)
        monkeypatch.setattr(json, "loads" , mock_json_loads)

        # call the function
        res = await ollama_match_resume_jd(jd, resume)

        # assertions
        assert res == {"mock_key": "mock_response" , "result" : result}


@pytest.mark.asyncio
async def test_ollama_match_resume_jd_no_response(monkeypatch):
    """
    Test the behavior of `ollama_match_resume_jd` when the response from `ollamaClient.post` does not contain the expected data.
    Mocks the HTTP response to return a specific string and checks that the function returns None.
    """

    jd = "JD text"
    resume = "Resume text"

    class MockResponse:
                # mock json() method always returns a specific testing dictionary
                @staticmethod
                def json():
                    return "elfknfi3bf"

                @property
                def status_code(self):
                    return 200
            
    async def set_response(*args,**kwargs):
             return MockResponse()


    monkeypatch.setattr(ollamaClient, "post", set_response)

    res = await ollama_match_resume_jd(jd, resume)

    assert res is None

@pytest.mark.asyncio
async def test_ollama_match_resume_jd_exception(monkeypatch):
    """
    Test the behavior of `ollama_match_resume_jd` when ollamaClient 
    sends a post request on route /api/generate and catches status not equal to 200 .
    .
    """

    jd = "JD text"
    resume = "Resume text"

    class MockResponse:
        # mock json() method always returns a specific testing dictionary
        @staticmethod
        def json():
            return {"error": "Internal Server Error"}

        @property
        def status_code(self):
            return 500

    async def set_response(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(ollamaClient, "post", set_response)

   # Verify that HTTPException is raised with the correct status code
    with pytest.raises(HTTPException) as excinfo:
        await ollama_match_resume_jd(jd, resume)
    
    # Verify the exception has the correct properties
    assert excinfo.value.status_code == 500
    assert "Request failed" in excinfo.value.detail

# async def test_ollama_extract_text_from_image(mock_client):
    # Arrange
#     image_path = "test_image.png"
#     prompt = "Extract text"
#     expected_text = "Extracted text"
#     mock_response = AsyncMock()
#     mock_response.text = expected_text
#     mock_client.post = AsyncMock(return_value=mock_response)

#     # Act
#     result = await ollama_extract_text_from_image(image_path, prompt)

#     # Assert
#     mock_client.post.assert_awaited_once_with(
#         url="/api/generate",
#         json={
#             "model": "gemma3:4b-it-qat",
#             "prompt": prompt,
#             "stream": False,
#             "images": [image_path]
#         },
#         timeout=40
#     )
#     assert mock_client.post.call_count == 1
#     # assert mock_client.post.return_value.json.call_count == 1
#     # check if status 200
#     mock_response.status_code = 200
#     print(mock_client.post.return_value.status_code)
#     assert mock_client.post.return_value.status_code == 200

#     assert result == expected_text
#     assert mock_client.post.return_value.json() == expected_text
#     assert isinstance(result, str)
# # @pytest.mark.asyncio
# # @patch("src.config.ollamaClient")
# # async def test_ollama_extract_text_from_image_success(mock_client):
# #         image_path = "test_image.png"
# #         prompt = "Extract text"
# #         expected_text = "Extracted text"
# #         mock_response = AsyncMock()
# #         mock_response.text = expected_text
# #         mock_client.post = AsyncMock(return_value=mock_response)

# #         result = await ollama_extract_text_from_image(image_path, prompt)

# #         mock_client.post.assert_awaited_once_with(
# #             url="/api/generate",
# #             json={
# #                 "model": "gemma3:4b-it-qat",
# #                 "prompt": prompt,
# #                 "stream": False,
# #                 "images": [image_path.replace('data:image/png;base64,','')]
# #             },
# #             timeout=40
# #         )
# #         assert result == expected_text

# # @pytest.mark.asyncio
# # @patch("src.config.ollamaClient")
# # async def test_ollama_extract_text_from_image_exception(mock_client):
#         image_path = "test_image.png"
#         prompt = "Extract text"
#         mock_client.post = AsyncMock(side_effect=Exception("Network error"))

#         result = await ollama_extract_text_from_image(image_path, prompt)

#         assert result is None





    