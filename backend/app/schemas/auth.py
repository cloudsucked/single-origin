from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class AuthUser(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str


class AuthResponse(BaseModel):
    token: str
    user: AuthUser
