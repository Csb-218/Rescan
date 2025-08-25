import pytest
from unittest.mock import AsyncMock, patch
from app.services.ollama import ollama_extract_text_from_image



@pytest.mark.asyncio
@patch("src.config.ollamaClient")
async def test_ollama_extract_text_from_image(mock_client):
    # Arrange
    image_path = "test_image.png"
    prompt = "Extract text"
    expected_text = "Extracted text"
    mock_response = AsyncMock()
    mock_response.text = expected_text
    mock_client.post = AsyncMock(return_value=mock_response)

    # Act
    result = await ollama_extract_text_from_image(image_path, prompt)

    # Assert
    mock_client.post.assert_awaited_once_with(
        url="/api/generate",
        json={
            "model": "gemma3:4b-it-qat",
            "prompt": prompt,
            "stream": False,
            "images": [image_path]
        },
        timeout=40
    )
    assert mock_client.post.call_count == 1
    # assert mock_client.post.return_value.json.call_count == 1
    # check if status 200
    mock_response.status_code = 200
    print(mock_client.post.return_value.status_code)
    assert mock_client.post.return_value.status_code == 200

    # assert result == expected_text
    # assert mock_client.post.return_value.json() == expected_text
    # assert isinstance(result, str)
@pytest.mark.asyncio
@patch("src.config.ollamaClient")
async def test_ollama_extract_text_from_image_success(mock_client):
        image_path = "test_image.png"
        prompt = "Extract text"
        expected_text = "Extracted text"
        mock_response = AsyncMock()
        mock_response.text = expected_text
        mock_client.post = AsyncMock(return_value=mock_response)

        result = await ollama_extract_text_from_image(image_path, prompt)

        mock_client.post.assert_awaited_once_with(
            url="/api/generate",
            json={
                "model": "gemma3:4b-it-qat",
                "prompt": prompt,
                "stream": False,
                "images": [image_path.replace('data:image/png;base64,','')]
            },
            timeout=40
        )
        assert result == expected_text

@pytest.mark.asyncio
@patch("src.config.ollamaClient")
async def test_ollama_extract_text_from_image_exception(mock_client):
        image_path = "test_image.png"
        prompt = "Extract text"
        mock_client.post = AsyncMock(side_effect=Exception("Network error"))

        result = await ollama_extract_text_from_image(image_path, prompt)

        assert result is None

    