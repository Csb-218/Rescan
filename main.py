from typing import Union
from fastapi import FastAPI
from app.routes import AnalyzeRouter
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(AnalyzeRouter)
