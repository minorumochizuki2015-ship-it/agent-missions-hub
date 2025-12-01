import pytest

from mcp_agent_mail.db import ensure_schema, get_session, reset_database_state
from mcp_agent_mail.mail_client import MailClient
from mcp_agent_mail.models import Agent, Project


@pytest.mark.asyncio
async def test_mail_client_smoke() -> None:
    reset_database_state()
    await ensure_schema()
    async with get_session() as session:
        proj = Project(slug="proj1", human_key="proj1")
        agent = Agent(project_id=1, name="HumanOverseer", program="ops", model="system")
        session.add(proj)
        await session.commit()
        session.add(agent)
        await session.commit()

    client = MailClient()
    msg = await client.send_message("proj1", "HumanOverseer", "hello", "world")
    listed = await client.list_messages("proj1")
    assert msg.id is not None
    assert listed and listed[0].subject == "hello"

    lease = await client.create_lease("proj1", "HumanOverseer", "docs/*")
    assert lease.id is not None
    released = await client.release_lease(lease.id)
    assert released.released_ts is not None
