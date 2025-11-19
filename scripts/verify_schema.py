import asyncio
import os
import sys
from pathlib import Path
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_agent_mail.db import ensure_schema, get_engine
from mcp_agent_mail.config import get_settings
from sqlalchemy import text


async def verify():
    # Use a temp storage root
    temp_storage = Path("./temp_verify_schema")
    if temp_storage.exists():
        shutil.rmtree(temp_storage)
    temp_storage.mkdir()

    os.environ["STORAGE_ROOT"] = str(temp_storage.absolute())

    print(f"Using storage root: {os.environ['STORAGE_ROOT']}")

    try:
        await ensure_schema()
        print("Schema initialized.")

        engine = get_engine()
        async with engine.connect() as conn:
            # List tables
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result.fetchall()]
            print("Tables found:", tables)

            expected_tables = ["missions", "task_groups", "tasks", "artifacts", "knowledge"]
            missing = [t for t in expected_tables if t not in tables]

            if missing:
                print(f"ERROR: Missing tables: {missing}")
                sys.exit(1)
            else:
                print("SUCCESS: All new tables found.")

            # Check columns for 'missions'
            result = await conn.execute(text("PRAGMA table_info(missions);"))
            columns = [row[1] for row in result.fetchall()]
            print("Missions columns:", columns)

    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        if temp_storage.exists():
            try:
                shutil.rmtree(temp_storage)
            except:
                pass


if __name__ == "__main__":
    asyncio.run(verify())
