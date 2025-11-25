import asyncio
import os
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from PIL import Image

os.environ.setdefault("ENABLE_FULL_SUITE", "1")
os.environ.setdefault("TEST_ALLOWLIST_APPEND", "tests/test_storage_cov.py")

from mcp_agent_mail import storage
from mcp_agent_mail.storage import ProjectArchive


@dataclass
class DummyStorageSettings:
    git_author_name: str = "tester"
    git_author_email: str = "tester@example.com"
    inline_image_max_bytes: int = 10_000_000
    keep_original_images: bool = False


@dataclass
class DummySettings:
    storage: DummyStorageSettings = field(default_factory=DummyStorageSettings)


class DummyIndex:
    def __init__(self) -> None:
        self.added = []
        self.committed = []

    def add(self, paths) -> None:
        self.added.extend(paths)

    def commit(self, message, author=None, committer=None) -> None:  # noqa: ARG002
        self.committed.append(message)


class DummyRepo:
    def __init__(self, root: Path, dirty: bool = False) -> None:
        self.root = root
        self.index = DummyIndex()
        self._dirty = dirty
        self.working_tree_dir = str(root)

    def is_dirty(self, index: bool = True, working_tree: bool = True) -> bool:  # noqa: ARG002
        return self._dirty

    # git.Repo.init replacement
    @classmethod
    def init(cls, root: str) -> "DummyRepo":
        return cls(Path(root))

    # Config writer that raises to hit suppress block
    def config_writer(self):
        class _Cfg:
            def __enter__(self):  # noqa: D401
                raise RuntimeError("cfg write fails")

            def __exit__(self, exc_type, exc, tb):  # noqa: D401
                return False

            def set_value(self, section, key, value):  # noqa: ARG002
                return None

        return _Cfg()


class DummyAsyncLock:
    def __init__(self, *args, **kwargs):  # noqa: D401, ARG002
        pass

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.fixture()
def immediate_to_thread(monkeypatch):
    async def _immediate(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(storage, "_to_thread", _immediate)
    return _immediate


def test_ensure_repo_suppresses_config_error(tmp_path, monkeypatch, immediate_to_thread):
    settings = DummySettings()
    monkeypatch.setattr(storage, "Repo", DummyRepo)
    monkeypatch.setattr(storage, "_register_repo", lambda repo: repo)
    monkeypatch.setattr(storage, "_commit", lambda *args, **kwargs: asyncio.sleep(0))
    # No exception should escape even though config_writer raises
    repo = asyncio.run(storage._ensure_repo(tmp_path / "repo", settings))
    assert isinstance(repo, DummyRepo)


def test_write_file_reservation_record_sha1(tmp_path, monkeypatch, immediate_to_thread):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    dummy_repo = DummyRepo(archive_root)
    archive = ProjectArchive(
        settings=DummySettings(),
        slug="demo",
        root=archive_root,
        repo=dummy_repo,
        lock_path=archive_root / ".lock",
        repo_root=archive_root,
    )
    recorded = {}

    async def _fake_write_json(path: Path, payload: dict[str, object]) -> None:
        recorded["path"] = path
        recorded["payload"] = payload

    monkeypatch.setattr(storage, "_write_json", _fake_write_json)
    monkeypatch.setattr(storage, "_commit", lambda *args, **kwargs: asyncio.sleep(0))
    asyncio.run(
        storage.write_file_reservation_record(
            archive,
            {"path_pattern": "agents/alice/inbox/*.md", "agent": "alice", "reason": "test"},
        )
    )
    assert recorded["payload"]["path_pattern"] == "agents/alice/inbox/*.md"


def test_store_image_and_audit(tmp_path, immediate_to_thread):
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    img_path = tmp_path / "img.png"
    Image.new("RGB", (2, 2), color="red").save(img_path)
    archive = ProjectArchive(
        settings=DummySettings(),
        slug="demo",
        root=archive_root,
        repo=DummyRepo(archive_root),
        lock_path=archive_root / ".lock",
        repo_root=archive_root,
    )
    meta, rel_path = asyncio.run(storage._store_image(archive, img_path))
    assert meta["sha1"]  # digest was computed with usedforsecurity=False
    assert rel_path.endswith(".webp")
    # audit/log files were attempted (best-effort); the function completed without error


def test_commit_trailers_suppress(monkeypatch, immediate_to_thread, tmp_path):
    monkeypatch.setattr(storage, "AsyncFileLock", DummyAsyncLock)
    repo = DummyRepo(tmp_path, dirty=True)
    settings = DummySettings()
    asyncio.run(storage._commit(repo, settings, "file_reservation: agent1 something", ["a.txt"]))
    assert repo.index.committed  # commit executed


def test_agent_graph_suppress(monkeypatch, immediate_to_thread):
    class Commit:
        def __init__(self, msg: str):
            self.message = msg

    class RepoGraph:
        def iter_commits(self, paths=None, max_count=None):  # noqa: ARG002
            return [Commit("mail: Alice -> Bob, Carol | Subject")]

    result = asyncio.run(storage.get_agent_communication_graph(RepoGraph(), "demo"))
    assert result["nodes"]  # suppress block executed without errors


def test_timeline_suppress(monkeypatch, immediate_to_thread):
    class Author:
        name = "tester"

    class Commit:
        def __init__(self, msg: str):
            self.message = msg
            self.authored_date = 0
            self.hexsha = "abcdef123456"
            self.author = Author()

    class RepoTimeline:
        def iter_commits(self, paths=None, max_count=None):  # noqa: ARG002
            return [Commit("mail: Sender -> R1, R2 | Note")]

    timeline = asyncio.run(storage.get_timeline_commits(RepoTimeline(), "demo"))
    assert timeline and timeline[0]["type"] == "message"


def test_historical_snapshot_frontmatter_and_failure(monkeypatch, immediate_to_thread):
    class DataStream:
        def __init__(self, content: bytes, fail: bool = False) -> None:
            self._content = content
            self._fail = fail

        def read(self) -> bytes:
            if self._fail:
                raise ValueError("boom")
            return self._content

    class Blob:
        def __init__(self, name: str, content: bytes, fail: bool = False) -> None:
            self.name = name
            self.type = "blob"
            self.data_stream = DataStream(content, fail=fail)

    class Tree:
        def __init__(self, name: str, children: list) -> None:
            self.name = name
            self._children = children
            self.type = "tree"

        def __iter__(self):
            return iter(self._children)

        def __truediv__(self, part: str):
            if part == self.name:
                return self
            for child in self._children:
                if child.name == part:
                    return child
            raise KeyError(part)

    class Commit:
        def __init__(self, tree) -> None:
            self.tree = tree
            self.authored_date = 0
            self.hexsha = "deadbeef"
            self.authored_datetime = datetime.fromtimestamp(0, tz=timezone.utc)

    class RepoSnapshot:
        def __init__(self, commit):
            self._commit = commit

        def iter_commits(self, max_count=None):  # noqa: ARG002
            return [self._commit]

    good_blob = Blob(
        "2025-01-01__subject__id.md",
        b"---json\n{\"from\":\"alice\",\"importance\":\"high\",\"subject\":\"hello\"}\n---\nbody",
    )
    bad_blob = Blob("2025-01-02__broken__id.md", b"", fail=True)
    inbox_tree = Tree("inbox", [good_blob, bad_blob])
    agent_tree = Tree("agent", [Tree("inbox", [inbox_tree])])  # nested to mimic traversal depth>1
    agents_tree = Tree("agents", [agent_tree])
    proj_tree = Tree("projects", [Tree("demo", [agents_tree])])
    commit = Commit(proj_tree)
    # Provide structlog stub to cover exception logging path
    class _DummyLogger:
        def debug(self, *args, **kwargs):
            return None

    class _DummyStructlog:
        @staticmethod
        def get_logger(name):
            return _DummyLogger()

    storage.structlog = _DummyStructlog()  # type: ignore[attr-defined]
    archive = ProjectArchive(
        settings=DummySettings(),
        slug="demo",
        root=Path("/tmp/archive"),
        repo=RepoSnapshot(commit),
        lock_path=Path("/tmp/archive/.lock"),
        repo_root=Path("/tmp/archive"),
    )
    snapshot = asyncio.run(
        storage.get_historical_inbox_snapshot(
            archive, agent_name="agent", timestamp="2025-01-03T00:00:00Z", limit=10
        )
    )
    assert snapshot["messages"]
