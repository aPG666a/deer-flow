from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.gateway.tenancy.db import get_tenancy_session
from app.gateway.tenancy.models import Department, Organization, Permission, Role, RolePermission, User, UserDepartment, UserRole
from app.gateway.tenancy.schemas import (
    DepartmentCreate,
    OrganizationCreate,
    PermissionCreate,
    RoleCreate,
    RolePermissionGrant,
    UserCreate,
    UserDepartmentGrant,
    UserRoleGrant,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _insert(session: AsyncSession, model: object) -> object:
    session.add(model)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate or invalid relation") from exc
    await session.refresh(model)
    return model


@router.get("/organizations")
async def list_organizations(session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    data = (await session.scalars(select(Organization).order_by(Organization.created_at.desc()))).all()
    return {"items": [{"id": i.id, "code": i.code, "name": i.name} for i in data]}


@router.post("/organizations", status_code=201)
async def create_organization(payload: OrganizationCreate, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, Organization(code=payload.code, name=payload.name))
    return {"id": item.id, "code": item.code, "name": item.name}


@router.get("/departments")
async def list_departments(organization_id: str, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    data = (await session.scalars(select(Department).where(Department.organization_id == organization_id))).all()
    return {"items": [{"id": i.id, "name": i.name, "parent_id": i.parent_id} for i in data]}


@router.post("/departments", status_code=201)
async def create_department(payload: DepartmentCreate, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, Department(organization_id=payload.organization_id, name=payload.name, parent_id=payload.parent_id))
    return {"id": item.id, "organization_id": item.organization_id, "name": item.name, "parent_id": item.parent_id}


@router.get("/users")
async def list_users(organization_id: str, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    data = (await session.scalars(select(User).where(User.organization_id == organization_id))).all()
    return {"items": [{"id": i.id, "email": i.email, "display_name": i.display_name, "status": i.status} for i in data]}


@router.post("/users", status_code=201)
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, User(organization_id=payload.organization_id, email=payload.email, display_name=payload.display_name))
    return {"id": item.id, "organization_id": item.organization_id, "email": item.email, "display_name": item.display_name}


@router.get("/roles")
async def list_roles(organization_id: str, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    data = (await session.scalars(select(Role).where(Role.organization_id == organization_id))).all()
    return {"items": [{"id": i.id, "code": i.code, "name": i.name} for i in data]}


@router.post("/roles", status_code=201)
async def create_role(payload: RoleCreate, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, Role(organization_id=payload.organization_id, code=payload.code, name=payload.name, description=payload.description))
    return {"id": item.id, "organization_id": item.organization_id, "code": item.code, "name": item.name}


@router.get("/permissions")
async def list_permissions(session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    data = (await session.scalars(select(Permission).order_by(Permission.code.asc()))).all()
    return {"items": [{"id": i.id, "code": i.code, "name": i.name} for i in data]}


@router.post("/permissions", status_code=201)
async def create_permission(payload: PermissionCreate, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, Permission(code=payload.code, name=payload.name, description=payload.description))
    return {"id": item.id, "code": item.code, "name": item.name}


@router.post("/grants/user-role", status_code=201)
async def grant_user_role(payload: UserRoleGrant, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, UserRole(user_id=payload.user_id, role_id=payload.role_id))
    return {"id": item.id, "user_id": item.user_id, "role_id": item.role_id}


@router.post("/grants/role-permission", status_code=201)
async def grant_role_permission(payload: RolePermissionGrant, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, RolePermission(role_id=payload.role_id, permission_id=payload.permission_id))
    return {"id": item.id, "role_id": item.role_id, "permission_id": item.permission_id}


@router.post("/grants/user-department", status_code=201)
async def grant_user_department(payload: UserDepartmentGrant, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    item = await _insert(session, UserDepartment(user_id=payload.user_id, department_id=payload.department_id))
    return {"id": item.id, "user_id": item.user_id, "department_id": item.department_id}


@router.get("/organizations/{organization_id}/access-matrix")
async def get_access_matrix(organization_id: str, session: AsyncSession = Depends(get_tenancy_session)) -> dict:
    users = (await session.scalars(select(User).where(User.organization_id == organization_id))).all()
    user_role_rows = (await session.execute(select(UserRole.user_id, Role.code).join(Role, Role.id == UserRole.role_id).where(Role.organization_id == organization_id))).all()
    role_perm_rows = (
        await session.execute(select(Role.code, Permission.code).join(RolePermission, RolePermission.permission_id == Permission.id).join(Role, Role.id == RolePermission.role_id).where(Role.organization_id == organization_id))
    ).all()

    role_permissions: dict[str, list[str]] = {}
    for role_code, perm_code in role_perm_rows:
        role_permissions.setdefault(role_code, []).append(perm_code)

    user_roles: dict[str, list[str]] = {}
    for user_id, role_code in user_role_rows:
        user_roles.setdefault(user_id, []).append(role_code)

    matrix = []
    for user in users:
        roles = user_roles.get(user.id, [])
        perms = sorted({perm for role_code in roles for perm in role_permissions.get(role_code, [])})
        matrix.append({"user_id": user.id, "email": user.email, "roles": roles, "permissions": perms})

    return {"organization_id": organization_id, "matrix": matrix}
