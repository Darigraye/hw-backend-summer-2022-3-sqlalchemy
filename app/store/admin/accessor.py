import typing
from hashlib import sha256
from pprint import pprint

from sqlalchemy import select, insert
from sqlalchemy.engine import ChunkedIteratorResult

from app.admin.models import Admin, AdminModel
from app.base.base_accessor import BaseAccessor

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        if not await self.get_by_email(app.config.admin.email):
            await self.create_admin(app.config.admin.email,
                                    app.config.admin.password)

    async def get_by_email(self, email: str) -> Admin | None:
        query_get_by_email = select(AdminModel).where(AdminModel.email == email)
        async with self.app.database.session() as session:
            res = await session.scalars(query_get_by_email)
            wrapped_data = res.first()
            if wrapped_data:
                return Admin(id=wrapped_data.id, email=wrapped_data.email, password=wrapped_data.password)

    async def create_admin(self, email: str, password: str) -> Admin:
        admin = AdminModel(
            email=email,
            password=sha256(password.encode()).hexdigest()
        )
        async with self.app.database.session() as session:
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
        return Admin(id=admin.id, email=admin.email, password=admin.password)
