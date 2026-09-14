import os
import asyncio
from pathlib import Path
import libsql_client
from dotenv import load_dotenv

# Explicitly load root .env
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

url_raw = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")

if not url_raw or not auth_token:
    raise ValueError("❌ Missing TURSO_DATABASE_URL or TURSO_AUTH_TOKEN in environment / .env file.")

url = url_raw.replace("libsql://", "https://")

async def setup():
    async with libsql_client.create_client(url, auth_token=auth_token) as client:
        await client.execute("""
            CREATE TABLE IF NOT EXISTS imc_members (
                member_id TEXT PRIMARY KEY,
                client_id TEXT,
                name TEXT,
                designation TEXT,
                category TEXT,
                special_order_ref TEXT
            )
        """)
    print("✅ IMC roster table created.")

asyncio.run(setup())