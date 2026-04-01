from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Organization(Base, TimestampMixin):
    __tablename__ = "tenant_organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class Department(Base, TimestampMixin):
    __tablename__ = "tenant_departments"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_tenant_department_org_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("tenant_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("tenant_departments.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "tenant_users"
    __table_args__ = (UniqueConstraint("organization_id", "email", name="uq_tenant_user_org_email"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("tenant_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class Role(Base, TimestampMixin):
    __tablename__ = "tenant_roles"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_tenant_role_org_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("tenant_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Permission(Base, TimestampMixin):
    __tablename__ = "tenant_permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserRole(Base, TimestampMixin):
    __tablename__ = "tenant_user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_tenant_user_role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("tenant_users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("tenant_roles.id", ondelete="CASCADE"), nullable=False, index=True)


class RolePermission(Base, TimestampMixin):
    __tablename__ = "tenant_role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_tenant_role_permission"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id: Mapped[str] = mapped_column(ForeignKey("tenant_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id: Mapped[str] = mapped_column(ForeignKey("tenant_permissions.id", ondelete="CASCADE"), nullable=False, index=True)


class UserDepartment(Base, TimestampMixin):
    __tablename__ = "tenant_user_departments"
    __table_args__ = (UniqueConstraint("user_id", "department_id", name="uq_tenant_user_department"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("tenant_users.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id: Mapped[str] = mapped_column(ForeignKey("tenant_departments.id", ondelete="CASCADE"), nullable=False, index=True)
