import os
import asyncio
import libsql_client
from dotenv import load_dotenv

load_dotenv()

async def update_schema():
    url = os.getenv("TURSO_DATABASE_URL").replace("libsql://", "https://")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    
    async with libsql_client.create_client(url, auth_token=auth_token) as client:
        print("Creating/Updating Users table...")
        
        # Creating the users table with the new 'agency' column
        await client.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                agency TEXT,
                role TEXT CHECK(role IN ('admin', 'client'))
            )
        """)
        
        # Linking assessments to the client
        try:
            await client.execute("ALTER TABLE assessments ADD COLUMN client_id TEXT")
            print("Linked assessments to clients.")
        except Exception:
            print("Client ID column already exists in assessments.")
            pass 
            
        print("✅ Phase 3 Users table successfully initialized.")

asyncio.run(update_schema())