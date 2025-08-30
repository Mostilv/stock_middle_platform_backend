from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.deps import get_current_active_user, get_current_superuser
from app.services.user_service import UserService
from app.models.user import User, UserUpdate

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends()
):
    """获取用户列表（仅管理员）"""
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends()
):
    """获取用户信息（仅管理员）"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends()
):
    """更新用户信息（仅管理员）"""
    user = await user_service.update_user(user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_superuser),
    user_service: UserService = Depends()
):
    """删除用户（仅管理员）"""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return {"message": "用户删除成功"}
