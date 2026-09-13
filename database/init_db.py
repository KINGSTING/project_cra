import os
import asyncio
import libsql_client
from dotenv import load_dotenv

# Load the Turso credentials from the .env file Vercel gave you
load_dotenv()

async def initialize_schema():
    url = os.getenv("TURSO_DATABASE_URL").replace("libsql://", "https://")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    
    print("Connecting to Turso Cloud...")
    
    # Connect to the remote Turso database over HTTP
    async with libsql_client.create_client(url, auth_token=auth_token) as client:
        
        print("Creating Table 1: Assessments (Module 1)...")
        await client.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                assessment_id TEXT PRIMARY KEY,
                agency_name TEXT,
                assessment_profile TEXT,
                status TEXT
            )
        """)
        
        print("Creating Table 2: Processes (Module 1 & 2)...")
        await client.execute("""
            CREATE TABLE IF NOT EXISTS processes (
                process_id TEXT PRIMARY KEY,
                assessment_id TEXT,
                process_name TEXT,
                screening_rationale TEXT,
                is_selected BOOLEAN,
                FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
            )
        """)

        print("Creating Table 3: Risks (Module 3)...")
        await client.execute("""
            CREATE TABLE IF NOT EXISTS risks (
                risk_id TEXT PRIMARY KEY,
                process_id TEXT,
                event_statement TEXT,
                inherent_likelihood INTEGER,
                inherent_consequence INTEGER,
                inherent_risk_level TEXT,
                risk_owner TEXT,
                FOREIGN KEY (process_id) REFERENCES processes(process_id)
            )
        """)
        
        print("✅ Success! The CRA relational schema is live on Turso.")

# Run the async function
asyncio.run(initialize_schema())