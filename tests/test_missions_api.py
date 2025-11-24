import pytest_asyncio
from fastapi import FastAPI, status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from mcp_agent_mail.db import get_session
from mcp_agent_mail.models import Artifact, Knowledge, Mission, Project
from mcp_agent_mail.routers import missions


@pytest_asyncio.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(async_engine):
    yield async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def app(session_factory):
    app = FastAPI()
    app.include_router(missions.router)

    async def _override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    yield app


@pytest_asyncio.fixture
async def mission_id(session_factory):
    async with session_factory() as session:
        project = Project(slug="mission-api", human_key="Mission API")
        session.add(project)
        await session.commit()
        mission = Mission(project_id=project.id, title="API Mission")
        session.add(mission)
        await session.commit()
        await session.refresh(mission)
        yield mission.id


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_missions(client: AsyncClient, mission_id: str):
    response = await client.get("/missions/")
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["id"] == mission_id


@pytest.mark.asyncio
async def test_create_artifact_and_knowledge(client: AsyncClient, mission_id: str, session_factory):
    payload = {
        "type": "plan",
        "path": "artifacts/plan-v1.json",
        "version": "v1.0",
        "sha256": "abcde12345",
        "tags": ["plan"],
        "knowledge_summary": "Extracted plan",
    }
    response = await client.post(f"/missions/{mission_id}/artifacts", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["mission_id"] == mission_id
    assert data["knowledge_id"] is not None

    async with session_factory() as session:
        artifact = await session.get(Artifact, data["id"])
        assert artifact is not None
        knowledge = await session.get(Knowledge, data["knowledge_id"])
        assert knowledge is not None
        assert knowledge.summary == "Extracted plan"


@pytest.mark.asyncio
async def test_create_artifact_missing_mission(client: AsyncClient):
    payload = {"type": "plan", "path": "missing", "version": "v1", "sha256": "deadbeef"}
    response = await client.post("/missions/00000000-0000-0000-0000-000000000000/artifacts", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_artifact_invalid_payload(client: AsyncClient, mission_id: str):
    payload = {"path": "invalid"}  # missing required fields
    response = await client.post(f"/missions/{mission_id}/artifacts", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
