from pydantic import EmailStr, Field, field_validator

from app.schemas.base import CamelModel
from app.utils.validators import normalize_role


class RegisterIn(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    role: str = "patient"
    hospital_id: int | None = None

    @field_validator("role")
    @classmethod
    def _role(cls, v):
        return normalize_role(v)


class LoginIn(CamelModel):
    email: EmailStr
    password: str
    role: str | None = None  # the frontend sends the role picked on the login page

    @field_validator("role")
    @classmethod
    def _role(cls, v):
        return normalize_role(v) if v else None


class UserOut(CamelModel):
    id: int
    name: str
    email: str
    role: str
    hospital_id: int | None = None


class TokenOut(CamelModel):
    token: str          # what the React app reads
    access_token: str   # standard OAuth2 field
    token_type: str = "bearer"
    user: UserOut
