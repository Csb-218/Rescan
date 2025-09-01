from fastapi import UploadFile 

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

