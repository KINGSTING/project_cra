import os, asyncio
from pathlib import Path
import libsql_client
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')
url = os.getenv("TURSO_DATABASE_URL", "").replace("libsql://", "https://")
token = os.getenv("TURSO_AUTH_TOKEN", "")

async def setup():
    async with libsql_client.create_client(url, auth_token=token) as client:
        await client.execute("""
            CREATE TABLE IF NOT EXISTS risk_register (
                risk_id TEXT PRIMARY KEY,
                client_id TEXT,
                process_area TEXT,
                risk_event TEXT,
                likelihood INTEGER,
                impact INTEGER,
                mitigation_control TEXT
            )
        """)
    print("✅ Risk register table created.")

asyncio.run(setup())