"""Small service with validated input and a health endpoint."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="__PROJECT_NAME__")


class GreetingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"\S")


class GreetingResponse(BaseModel):
    message: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/greet")
def greet(request: GreetingRequest) -> GreetingResponse:
    return GreetingResponse(message=f"Hello, {request.name.strip()}!")
