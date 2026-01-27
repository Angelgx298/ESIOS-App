import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from esios_ingestor.core.config import settings
from esios_ingestor.core.database import get_db
from esios_ingestor.web.app import app

test_engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)

TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function")
async def db_session():
    """
    Creates a fresh database session for each test.
    """
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session):
    """
    Creates an async HTTP client for testing the FastAPI app.
    Overrides the database dependency to use the test session.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
