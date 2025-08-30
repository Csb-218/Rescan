import pytest
from fastapi import testclient
import sys
from importlib import reload
import app.services.ollama

@pytest.mark.asyncio
async def test_analyze_advanced(monkeypatch):
    # Create mock functions
    async def mock_ollama_match(*args, **kwargs):
        return {"match_percentage": 85.0, "details": "Good match"}
    

    
    # Apply patches
    monkeypatch.setattr('app.services.ollama.ollama_match_resume_jd', mock_ollama_match)

    
    # Reload the module to ensure our mocks are used
    
    
    # Import app after patching
    from main import app
    test_client = testclient.TestClient(app)
    
    # Prepare files
    with open("tests/jd_test.pdf", "rb") as f:
        jd_file = f.read()
    with open("tests/resume_test.pdf", "rb") as f:
        resume_file = f.read()

    files = {
        "jd": ("jd.pdf", jd_file, "application/pdf"),
        "resume": ("resume.pdf", resume_file, "application/pdf")
    }
    
    # Make request
    response = test_client.post("/analyze/advanced", files=files)
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200
    assert response.json() == {'result': {'details': 'Good match', 'match_percentage': 85.0}}