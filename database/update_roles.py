import os
import asyncio
import libsql_client
from dotenv import load_dotenv

load_dotenv()

async def update_schema():
    url = os.getenv("TURSO_DATABASE_URL").replace("libsql://", "https://")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    
    async with libsql_client.create_client(url, auth_token=auth_token) as client:
        await client.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                role TEXT CHECK(role IN ('admin', 'client'))
            )
        """)
        try:
            await client.execute("ALTER TABLE assessments ADD COLUMN client_id TEXT")
        except Exception:
            pass # Skips if the column already exists
        print("✅ Users table created and assessments linked.")

asyncio.run(update_schema())