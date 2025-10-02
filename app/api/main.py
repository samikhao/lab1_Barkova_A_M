from fastapi import FastAPI
from app.api.v1.router import router as api_v1

app = FastAPI(title="web lab1")
app.include_router(api_v1)

@app.get("/health")
def health():
    return {"status": "ok"}
