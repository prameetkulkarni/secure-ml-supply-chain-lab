"""Tiny inference API. The app is deliberately boring: the lab is about the
pipeline that builds, signs and admits it, not about the model."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="inference-stub")


class Prompt(BaseModel):
    text: str


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/predict")
def predict(prompt: Prompt) -> dict:
    # Stand-in for a real model call. Stretch goal 1 in the README swaps this
    # for a model file that is scanned and signed like the image is.
    return {"length": len(prompt.text), "label": "long" if len(prompt.text) > 80 else "short"}
