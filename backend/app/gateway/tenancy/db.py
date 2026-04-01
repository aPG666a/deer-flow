from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.gateway.tenancy.models import Base

DATABASE_URL = os.getenv("DEER_FLOW_TENANCY_DATABASE_URL", "postgresql+psycopg://deerflow:deerflow@localhost:5432/deerflow")

engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_tenancy_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_tenancy_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
