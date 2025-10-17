# app/main.py
from fastapi import FastAPI
from .config import APP_ENV

app = FastAPI(title="OC5 Attrition API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "env": APP_ENV}