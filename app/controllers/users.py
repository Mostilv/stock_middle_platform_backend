from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.deps import get_optional_active_user, get_user_service
from app.services.user_service import UserService
from app.models.user import User, UserCreate, UserUpdate
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.post("", response_model=User)
async def create_user(
    payload: UserCreate,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    try:
        return await user_service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """获取用户列表"""
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """获取用户信息"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """更新用户信息"""
    try:
        user = await user_service.update_user(user_id, user_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
        )
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    """删除用户"""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
        )
    return {"message": "用户删除成功"}


class RolesUpdate(BaseModel):
    roles: list[str]


class PermissionsUpdate(BaseModel):
    permissions: list[str]


@router.post("/{user_id}/roles", response_model=User)
async def add_user_roles(
    user_id: str,
    body: RolesUpdate,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.add_roles(user_id, body.roles)


@router.delete("/{user_id}/roles", response_model=User)
async def remove_user_roles(
    user_id: str,
    body: RolesUpdate,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.remove_roles(user_id, body.roles)


@router.post("/{user_id}/permissions", response_model=User)
async def add_user_permissions(
    user_id: str,
    body: PermissionsUpdate,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.add_permissions(user_id, body.permissions)


@router.delete("/{user_id}/permissions", response_model=User)
async def remove_user_permissions(
    user_id: str,
    body: PermissionsUpdate,
    _: User = Depends(get_optional_active_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.remove_permissions(user_id, body.permissions)
