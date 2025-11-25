"""FastAPI + FastMCP のエントリーポイント骨子。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Iterator

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from .db import (
    Artifact,
    ArtifactCreate,
    Knowledge,
    KnowledgeCreate,
    Mission,
    MissionCreate,
    Project,
    Task,
    TaskCreate,
    TaskGroup,
    TaskGroupCreate,
    get_session,
    init_db,
)
from .mcp import build_mcp_server
from .settings import Settings, get_settings


def build_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI アプリを構築する。"""

    app_settings = settings or get_settings()
    app = FastAPI(title=app_settings.app_name, debug=app_settings.debug)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """単純なヘルスチェック応答を返す。"""

        return {"status": "ok", "app": app_settings.app_name}

    def get_db() -> Iterator[Session]:
        session = get_session(app_settings.database_url)
        try:
            yield session
        finally:
            session.close()

    db_dependency = Depends(get_db)

    @app.on_event("startup")
    async def startup_db() -> None:  # pragma: no cover - framework hook
        init_db(app_settings.database_url)

    api_router = APIRouter(prefix="/api")

    def _project_for_slug(session: Session, slug: str) -> Project:
        project = session.exec(select(Project).where(Project.slug == slug)).first()
        if project is None:
            project = Project(slug=slug, title=slug)
            session.add(project)
            session.commit()
            session.refresh(project)
        return project

    @api_router.get("/missions", tags=["missions"])
    def list_missions(session: Session = db_dependency) -> list[dict]:
        """ミッション一覧。"""

        rows = session.exec(
            select(Mission, Project).where(Mission.project_id == Project.id)
        ).all()
        result: list[dict] = []
        for mission, project in rows:
            result.append(
                {
                    "id": mission.id,
                    "project_slug": project.slug,
                    "title": mission.title,
                    "summary": mission.summary,
                    "status": mission.status,
                }
            )
        return result

    @api_router.post("/missions", tags=["missions"])
    def create_mission(
        payload: MissionCreate, session: Session = db_dependency
    ) -> dict:
        """ミッションを作成。"""

        project = _project_for_slug(session, payload.project_slug)
        mission = Mission(
            project_id=project.id,
            title=payload.title,
            summary=payload.summary,
            status=payload.status,
        )
        session.add(mission)
        session.commit()
        session.refresh(mission)
        return {
            "id": mission.id,
            "project_slug": project.slug,
            "title": mission.title,
            "status": mission.status,
        }

    @api_router.get("/task-groups", tags=["task_groups"])
    def list_task_groups(session: Session = db_dependency) -> list[TaskGroup]:
        return session.exec(select(TaskGroup)).all()

    @api_router.post("/task-groups", tags=["task_groups"])
    def create_task_group(
        payload: TaskGroupCreate, session: Session = db_dependency
    ) -> TaskGroup:
        group = TaskGroup(
            mission_id=payload.mission_id, name=payload.name, sequence=payload.sequence
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        return group

    @api_router.get("/tasks", tags=["tasks"])
    def list_tasks(session: Session = db_dependency) -> list[Task]:
        return session.exec(select(Task)).all()

    @api_router.post("/tasks", tags=["tasks"])
    def create_task(payload: TaskCreate, session: Session = db_dependency) -> Task:
        mission = session.get(Mission, payload.mission_id)
        if mission is None:
            raise HTTPException(status_code=404, detail="mission not found")
        task = Task(
            mission_id=payload.mission_id,
            kind=payload.kind,
            summary=payload.summary,
            status=payload.status,
            assignee_agent_id=payload.assignee_agent_id,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @api_router.get("/artifacts", tags=["artifacts"])
    def list_artifacts(session: Session = db_dependency) -> list[Artifact]:
        return session.exec(select(Artifact)).all()

    @api_router.post("/artifacts", tags=["artifacts"])
    def create_artifact(
        payload: ArtifactCreate, session: Session = db_dependency
    ) -> Artifact:
        artifact = Artifact(
            mission_id=payload.mission_id,
            task_id=payload.task_id,
            name=payload.name,
            type=payload.type,
            uri=payload.uri,
            meta=payload.meta or {},
        )
        session.add(artifact)
        session.commit()
        session.refresh(artifact)
        return artifact

    @api_router.get("/knowledge", tags=["knowledge"])
    def list_knowledge(session: Session = db_dependency) -> list[Knowledge]:
        return session.exec(select(Knowledge)).all()

    @api_router.post("/knowledge", tags=["knowledge"])
    def create_knowledge(
        payload: KnowledgeCreate, session: Session = db_dependency
    ) -> Knowledge:
        knowledge = Knowledge(
            mission_id=payload.mission_id,
            title=payload.title,
            summary=payload.summary,
            source_artifact_id=payload.source_artifact_id,
            tags=payload.tags or [],
        )
        session.add(knowledge)
        session.commit()
        session.refresh(knowledge)
        return knowledge

    app.include_router(api_router)

    # FastMCP ネイティブマウント
    try:
        server = build_mcp_server(app_settings)
    except ImportError:
        server = None

    if server is not None:
        mcp_app = server.http_app(
            path="/",
            stateless_http=app_settings.stateless_http,
            json_response=True,
        )

        mount_base = app_settings.mcp_mount_path or "/mcp"
        if not mount_base.startswith("/"):
            mount_base = f"/{mount_base}"

        @asynccontextmanager
        async def lifespan_context(_: FastAPI):
            # FastMCP 側の lifespan を確実に起動する
            if hasattr(mcp_app, "lifespan"):
                async with mcp_app.lifespan(mcp_app):  # type: ignore[attr-defined]
                    yield
            else:  # pragma: no cover - fallback
                yield

        app.router.lifespan_context = lifespan_context
        app.mount(mount_base, mcp_app)
    else:

        @app.get("/mcp", include_in_schema=False)
        async def mcp_unavailable() -> dict[str, str]:
            """fastmcp 未導入時の簡易応答。"""

            return {"detail": "fastmcp not available"}

    return app


app = build_app()
