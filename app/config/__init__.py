from httpx import AsyncClient
import os

base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
print(f"Using Ollama Base URL: {base_url}")
ollamaClient = AsyncClient(
    base_url=base_url ,
    headers={"Content-Type": "application/json"}
)