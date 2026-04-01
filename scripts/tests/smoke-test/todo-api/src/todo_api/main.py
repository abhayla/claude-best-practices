"""Todo API — FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Todo API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}
