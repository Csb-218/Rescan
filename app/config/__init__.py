from httpx import AsyncClient 
import os

base_url = f'''{os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")}'''


ollamaClient = AsyncClient(
    base_url=base_url ,
    headers={"Content-Type": "application/json"}
)