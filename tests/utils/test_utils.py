import pytest
from app.utils import validate_and_save_files
from pathlib import Path
from fastapi import UploadFile , HTTPException
import builtins

class MockUploadFile(UploadFile):
        def __init__(self, filename: str, content_type: str, size: int):
            import io
            super().__init__(filename=filename, file=io.BytesIO(b"mock file content"))
            from starlette.datastructures import Headers
            self.headers = Headers({"content-type": content_type})
            self.size = size
        async def read(self, size=-1):
            return b"mock file content"
        
# Create a mock for the open() function
class MockOpen:
        def __init__(self, path, mode, *args, **kwargs):
            self.path = path
            self.mode = mode
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def close(self):
            pass
            
        def write(self, content):
            # Just simulate writing, don't actually do it
            pass

@pytest.mark.asyncio
async def test_validate_and_save_files(monkeypatch):
    """
    Test the `validate_and_save_files` function for successful file validation and saving.
    This test uses monkeypatching to mock external dependencies and responses:
    - Mocks the file uploads and their properties.
    - Verifies that the function returns the expected tuple of saved file paths.
    Args:
        monkeypatch: pytest's monkeypatch fixture for patching objects.
    Asserts:
        The result of `validate_and_save_files` matches the expected tuple of saved file paths.
    """

    jd_file = MockUploadFile("jd.pdf", "application/pdf", 10)
    resume_file = MockUploadFile("resume.pdf", "application/pdf", 10)

    monkeypatch.setattr(builtins, "open", MockOpen)
    monkeypatch.setattr("app.utils.UPLOAD_DIR", Path("mock_uploads"))
    monkeypatch.setattr("app.utils.HTTPException", Exception)
    

    jd,resume,saved_paths = await validate_and_save_files(jd=jd_file, resume=resume_file)

    assert jd.filename == "jd.pdf"
    assert resume.filename == "resume.pdf"
    assert isinstance(saved_paths, list)
    assert len(saved_paths) == 2

@pytest.mark.asyncio
async def test_validate_and_save_files_invalid_type(monkeypatch):
    """
    Test that validate_and_save_files raises an HTTPException when provided files have invalid types.
    This test uses monkeypatch to mock file operations and dependencies, and verifies that
    an exception is raised when the JD and resume files are not of the expected types.
    """

    jd_file = MockUploadFile("jd.txt", "text/plain", 10)
    resume_file = MockUploadFile("resume.png", "image/png", 10)

    monkeypatch.setattr(builtins, "open", MockOpen)
    monkeypatch.setattr("app.utils.UPLOAD_DIR", Path("mock_uploads"))
    monkeypatch.setattr("app.utils.HTTPException", HTTPException)

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_save_files(jd=jd_file, resume=resume_file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid file type. Only PDF files are allowed."

@pytest.mark.asyncio
async def test_validate_save_files_resume_empty(monkeypatch):
    """
    Test that validate_and_save_files raises an HTTPException when provided files are empty.
    This test uses monkeypatch to mock file operations and dependencies, and verifies that
    an exception is raised when the JD and resume files are empty.
    """

    jd_file = MockUploadFile("jd.pdf", "application/pdf",10)
    # resume_file = MockUploadFile("resume.pdf", "application/pdf")

    monkeypatch.setattr(builtins, "open", MockOpen)
    monkeypatch.setattr("app.utils.UPLOAD_DIR", Path("mock_uploads"))
    monkeypatch.setattr("app.utils.HTTPException", HTTPException)

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_save_files(jd=jd_file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Both JD and Resume files must be provided."

@pytest.mark.asyncio
async def test_validate_save_files_jd_empty(monkeypatch):
    """
    Test that validate_and_save_files raises an HTTPException when provided files are empty.
    This test uses monkeypatch to mock file operations and dependencies, and verifies that
    an exception is raised when the JD and resume files are empty.
    """

    # jd_file = MockUploadFile("jd.pdf", "application/pdf")
    resume_file = MockUploadFile("resume.pdf", "application/pdf", 10)

    monkeypatch.setattr(builtins, "open", MockOpen)
    monkeypatch.setattr("app.utils.UPLOAD_DIR", Path("mock_uploads"))
    monkeypatch.setattr("app.utils.HTTPException", HTTPException)

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_save_files(resume=resume_file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Both JD and Resume files must be provided."

@pytest.mark.asyncio
async def test_validate_save_files_empty(monkeypatch):
    """
    Test that validate_and_save_files raises an HTTPException when provided files are empty.
    This test uses monkeypatch to mock file operations and dependencies, and verifies that
    an exception is raised when the JD and resume files are empty.
    """

    monkeypatch.setattr(builtins, "open", MockOpen)
    monkeypatch.setattr("app.utils.UPLOAD_DIR", Path("mock_uploads"))
    monkeypatch.setattr("app.utils.HTTPException", HTTPException)

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_save_files()

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Both JD and Resume files must be provided."

@pytest.mark.asyncio
async def test_validate_save_files_jd_size_zero(monkeypatch):
    """
    Test that validate_and_save_files raises an HTTPException when the JD file is empty.
    This test uses monkeypatch to mock file operations and dependencies, and verifies that
    an exception is raised when the JD file is empty.
    """

    jd_file = MockUploadFile("jd.pdf", "application/pdf", 0)
    resume_file = MockUploadFile("resume.pdf", "application/pdf", 0)

    monkeypatch.setattr(builtins, "open", MockOpen)
    monkeypatch.setattr("app.utils.UPLOAD_DIR", Path("mock_uploads"))
    monkeypatch.setattr("app.utils.HTTPException", HTTPException)

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_save_files(jd=jd_file, resume=resume_file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Both JD and Resume files must not be empty."

@pytest.mark.asyncio
async def test_validate_save_files_size_exceed(monkeypatch):
    """
    Test that validate_and_save_files raises an HTTPException when the file size exceeds the limit.
    This test uses monkeypatch to mock file operations and dependencies, and verifies that
    an exception is raised when the file size exceeds the allowed limit.
    """

    jd_file = MockUploadFile("jd.pdf", "application/pdf", 6 * 1024 * 1024)  # 6 MB
    resume_file = MockUploadFile("resume.pdf", "application/pdf", 6 * 1024 * 1024)  # 6 MB

    monkeypatch.setattr(builtins, "open", MockOpen)
    monkeypatch.setattr("app.utils.UPLOAD_DIR", Path("mock_uploads"))
    monkeypatch.setattr("app.utils.HTTPException", HTTPException)

    with pytest.raises(HTTPException) as exc_info:
        await validate_and_save_files(jd=jd_file, resume=resume_file)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "File size exceeds the 5 MB limit."