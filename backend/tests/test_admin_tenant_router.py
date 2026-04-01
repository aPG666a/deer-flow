import asyncio

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.gateway.routers.admin_tenant import router
from app.gateway.tenancy.db import get_tenancy_session
from app.gateway.tenancy.models import Base


def test_admin_tenant_crud_and_access_matrix():
    async def run_test() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async def override_session():
            async with session_maker() as session:
                yield session

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_tenancy_session] = override_session

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            org = (await client.post("/api/admin/organizations", json={"code": "acme", "name": "Acme"})).json()
            role = (
                await client.post(
                    "/api/admin/roles",
                    json={"organization_id": org["id"], "code": "org_admin", "name": "Org Admin"},
                )
            ).json()
            user = (
                await client.post(
                    "/api/admin/users",
                    json={"organization_id": org["id"], "email": "admin@acme.com", "display_name": "Admin"},
                )
            ).json()
            perm = (await client.post("/api/admin/permissions", json={"code": "tenant.user.manage", "name": "Manage User"})).json()

            grant_role = await client.post("/api/admin/grants/user-role", json={"user_id": user["id"], "role_id": role["id"]})
            grant_perm = await client.post(
                "/api/admin/grants/role-permission",
                json={"role_id": role["id"], "permission_id": perm["id"]},
            )

            assert grant_role.status_code == 201
            assert grant_perm.status_code == 201

            matrix_resp = await client.get(f"/api/admin/organizations/{org['id']}/access-matrix")
            matrix = matrix_resp.json()["matrix"]

            assert matrix_resp.status_code == 200
            assert matrix[0]["email"] == "admin@acme.com"
            assert "org_admin" in matrix[0]["roles"]
            assert "tenant.user.manage" in matrix[0]["permissions"]

    asyncio.run(run_test())
