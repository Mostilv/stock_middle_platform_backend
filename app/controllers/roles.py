from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.deps import get_current_superuser, get_role_service
from app.models.role import Role, RoleCreate, RoleUpdate
from app.services.role_service import RoleService


router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.post("/", response_model=Role)
async def create_role(
    role_create: RoleCreate,
    current_user=Depends(get_current_superuser),
    role_service: RoleService = Depends(get_role_service),
):
    try:
        return await role_service.create_role(role_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[Role])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user=Depends(get_current_superuser),
    role_service: RoleService = Depends(get_role_service),
):
    return await role_service.list_roles(skip=skip, limit=limit)


@router.get("/{role_id}", response_model=Role)
async def get_role(
    role_id: str,
    current_user=Depends(get_current_superuser),
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return role


@router.put("/{role_id}", response_model=Role)
async def update_role(
    role_id: str,
    role_update: RoleUpdate,
    current_user=Depends(get_current_superuser),
    role_service: RoleService = Depends(get_role_service),
):
    role = await role_service.update_role(role_id, role_update)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return role


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user=Depends(get_current_superuser),
    role_service: RoleService = Depends(get_role_service),
):
    success = await role_service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return {"message": "角色删除成功"}
