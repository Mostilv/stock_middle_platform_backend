from typing import Optional

from app.models.account import AccountProfile, AccountProfileUpdate, PasswordChangeRequest
from app.models.user import User, UserUpdate
from app.services.user_service import UserService


class AccountService:
    def __init__(self, user_service: Optional[UserService] = None) -> None:
        self.user_service = user_service or UserService()

    async def get_profile(self, user: User) -> AccountProfile:
        return AccountProfile(
            username=user.username,
            email=user.email,
            role="admin" if user.is_superuser else "user",
            display_name=user.display_name or user.username,
            avatar_url=user.avatar_url,
        )

    async def update_profile(self, user: User, payload: AccountProfileUpdate) -> AccountProfile:
        await self.user_service.update_user(
            user.id,
            UserUpdate(
                username=payload.username or user.username,
                display_name=payload.display_name or payload.username,
                avatar_url=payload.avatar_url or user.avatar_url,
                email=payload.email or user.email,
            ),
        )
        refreshed = await self.user_service.get_user_by_id(user.id) or user
        return await self.get_profile(refreshed)

    async def change_password(self, user: User, payload: PasswordChangeRequest) -> None:
        authenticated = await self.user_service.authenticate_user(
            user.username,
            payload.currentPassword,
        )
        if not authenticated:
            raise ValueError("当前密码错误")
        await self.user_service.update_user(
            user.id,
            UserUpdate(password=payload.newPassword),
        )
