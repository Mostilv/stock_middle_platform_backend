from pydantic import BaseModel, EmailStr, Field


class AccountProfile(BaseModel):
    username: str
    email: EmailStr | None = None
    role: str | None = None
    display_name: str | None = Field(default=None, alias="display_name")
    avatar_url: str | None = None

    class Config:
        allow_population_by_field_name = True


class AccountProfileUpdate(BaseModel):
    username: str
    display_name: str | None = Field(default=None, alias="display_name")
    avatar_url: str | None = None
    email: EmailStr | None = None

    class Config:
        allow_population_by_field_name = True


class PasswordChangeRequest(BaseModel):
    currentPassword: str
    newPassword: str
