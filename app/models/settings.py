from typing import List

from pydantic import BaseModel, EmailStr, Field


class EmailConfig(BaseModel):
    id: str
    email: EmailStr
    remark: str = ""
    enabled: bool = True


class NotificationTemplate(BaseModel):
    id: str
    name: str
    subject: str
    content: str
    enabled: bool = True


class SettingsData(BaseModel):
    emailConfigs: List[EmailConfig] = Field(default_factory=list)
    notificationTemplates: List[NotificationTemplate] = Field(default_factory=list)
