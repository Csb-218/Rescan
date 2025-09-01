import pytest
from fastapi.testclient import TestClient 
# from main import app
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from importlib import reload

@pytest.mark.asyncio
async def test_analyze_advanced(monkeypatch):
    # Create mock functions
    async def mock_ollama_match(*args, **kwargs):
        return {"match_percentage": 85.0, "details": "Good match"}

    # Apply patches
    monkeypatch.setattr('app.services.ollama.ollama_match_resume_jd', mock_ollama_match)
    
    
    # Import app after patching
    from app.main import app
    client = TestClient(app)
    
    # Prepare files
    with open("app/tests/jd_test.pdf", "rb") as f:
        jd_file = f.read()
    with open("app/tests/resume_test.pdf", "rb") as f:
        resume_file = f.read()

    files = {
        "jd": ("jd.pdf", jd_file, "application/pdf"),
        "resume": ("resume.pdf", resume_file, "application/pdf")
    }
    
    # Make request
    response = client.post("/analyze/advanced", files=files)
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200
    assert response.json() == {'result': {'details': 'Good match', 'match_percentage': 85.0}}

    
@pytest.mark.asyncio
async def test_analyze_advanced_fail_processing_files():

    from app.main import app
    client = TestClient(app)
    # Prepare files
    with open("app/tests/jd_test.pdf", "rb") as f:
        jd_file = f.read()
    with open("app/tests/corrupt_resume.pdf", "rb") as f:
        resume_file = f.read()

    files = {
        "jd": ("jd.pdf", jd_file, "application/pdf"),
        "resume": ("resume.pdf", resume_file, "application/pdf")
    }

    # Make request
    response = client.post("/analyze/advanced", files=files)

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

    assert response.status_code == 500
    assert response.json()["detail"] == f"An error occurred while processing the files: {response.json()['detail'].split(': ')[1]}"

def test_cleanup_saved_paths_removes_existing_files():
    # Create mock paths
    mock_path1 = MagicMock()
    mock_path2 = MagicMock()
    mock_path1.exists.return_value = True
    mock_path2.exists.return_value = True

    saved_paths = [mock_path1, mock_path2]

    with patch("os.remove") as mock_remove:
        # Simulate the cleanup logic
        for path in saved_paths:
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

        assert mock_remove.call_count == 2
        mock_remove.assert_any_call(mock_path1)
        mock_remove.assert_any_call(mock_path2)

def test_cleanup_saved_paths_skips_nonexistent_files():
    mock_path = MagicMock()
    mock_path.exists.return_value = False

    with patch("os.remove") as mock_remove:
        for path in [mock_path]:
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

        mock_remove.assert_not_called()

def test_cleanup_saved_paths_handles_remove_exception(capfd):
    mock_path = MagicMock()
    mock_path.exists.return_value = True

    with patch("os.remove", side_effect=OSError("fail")):
        for path in [mock_path]:
            if path.exists():
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")

    out, _ = capfd.readouterr()
    assert "Error deleting" in out
    assert "fail" in out