from typing import List, Optional

from pydantic import BaseModel

from app.models.settings import EmailConfig, NotificationTemplate


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginUser(BaseModel):
    username: str
    role: Optional[str] = None
    email: Optional[str] = None
    displayName: Optional[str] = None
    avatarUrl: Optional[str] = None
    emailConfigs: Optional[List[EmailConfig]] = None
    notificationTemplates: Optional[List[NotificationTemplate]] = None


class LoginResponse(BaseModel):
    token: str
    user: LoginUser
