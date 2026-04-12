from pydantic import BaseModel, EmailStr, Field


class Password(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class SignUp(Password):
    email: EmailStr
    name: str


class LoginReq(Password):
    email: EmailStr


class ForgotPasswordReq(BaseModel):
    email: EmailStr


class ResetPasswordReq(Password):
    token: str
