# Generated from spec
from fastapi import FastAPI

app = FastAPI(title="generated_module")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    return {"version": "0.1.0"}
