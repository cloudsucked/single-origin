from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str


class DetailErrorResponse(BaseModel):
    detail: str
