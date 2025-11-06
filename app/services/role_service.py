from datetime import datetime
from typing import List, Optional

from app.models.role import Role, RoleCreate, RoleUpdate
from app.repositories.role_repository import RoleRepository


class RoleService:
    def __init__(self, repository: Optional[RoleRepository] = None) -> None:
        self.repository = repository or RoleRepository()

    async def create_role(self, role_create: RoleCreate) -> Role:
        if await self.repository.find_by_name(role_create.name):
            raise ValueError("角色已存在")

        now = datetime.utcnow()
        role_doc = {
            "name": role_create.name,
            "description": role_create.description,
            "permissions": role_create.permissions,
            "created_at": now,
            "updated_at": now,
        }

        role_id = await self.repository.insert_role(role_doc)
        return await self.get_role_by_id(role_id)

    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        document = await self.repository.find_by_id(role_id)
        return self._document_to_role(document) if document else None

    async def get_role_by_name(self, name: str) -> Optional[Role]:
        document = await self.repository.find_by_name(name)
        return self._document_to_role(document) if document else None

    async def list_roles(self, skip: int = 0, limit: int = 100) -> List[Role]:
        roles: List[Role] = []
        cursor = await self.repository.list_roles(skip, limit)
        async for document in cursor:
            roles.append(self._document_to_role(document))
        return roles

    async def update_role(
        self, role_id: str, role_update: RoleUpdate
    ) -> Optional[Role]:
        update_data = role_update.dict(exclude_unset=True)
        if not update_data:
            return await self.get_role_by_id(role_id)

        update_data["updated_at"] = datetime.utcnow()
        if not await self.repository.update_role(role_id, update_data):
            return None
        return await self.get_role_by_id(role_id)

    async def delete_role(self, role_id: str) -> bool:
        return await self.repository.delete_role(role_id)

    @staticmethod
    def _document_to_role(document: dict) -> Role:
        return Role(
            id=str(document["_id"]),
            name=document["name"],
            description=document.get("description"),
            permissions=document.get("permissions", []),
            created_at=document.get("created_at", datetime.utcnow()),
            updated_at=document.get("updated_at", datetime.utcnow()),
        )
