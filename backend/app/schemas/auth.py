from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AIRecommendRequest(BaseModel):
    query: str
    context: str = ""


class AIRecommendResponse(BaseModel):
    answer: str
    query: str
