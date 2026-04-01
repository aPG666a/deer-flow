from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)


class DepartmentCreate(BaseModel):
    organization_id: str
    name: str
    parent_id: str | None = None


class UserCreate(BaseModel):
    organization_id: str
    email: str
    display_name: str


class RoleCreate(BaseModel):
    organization_id: str
    code: str
    name: str
    description: str | None = None


class PermissionCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class UserRoleGrant(BaseModel):
    user_id: str
    role_id: str


class RolePermissionGrant(BaseModel):
    role_id: str
    permission_id: str


class UserDepartmentGrant(BaseModel):
    user_id: str
    department_id: str
