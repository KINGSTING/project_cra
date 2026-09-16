# database/init_db.py
import os
import turso_serverless
from dotenv import load_dotenv

load_dotenv(".env.local")

print("Connecting to Turso Cloud...")
conn = turso_serverless.connect(
    os.environ["TURSO_DATABASE_URL"],
    auth_token=os.environ["TURSO_AUTH_TOKEN"],
)

statements = [
    ("Table 1: Assessments (Module 1)", """
        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id TEXT PRIMARY KEY,
            agency_name TEXT,
            assessment_profile TEXT,
            status TEXT
        )
    """),
    ("Table 2: Processes (Module 1 & 2)", """
        CREATE TABLE IF NOT EXISTS processes (
            process_id TEXT PRIMARY KEY,
            assessment_id TEXT,
            process_name TEXT,
            screening_rationale TEXT,
            is_selected BOOLEAN,
            FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
        )
    """),
    ("Table 3: Risks (Module 3)", """
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
    """),
    ("Table 4: Email verifications (Phase 3 auth)", """
        CREATE TABLE IF NOT EXISTS email_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            agency TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """),
    ("Index: email_verifications(email)", """
        CREATE INDEX IF NOT EXISTS idx_email_verif_email
        ON email_verifications(email)
    """),
    ("Index: email_verifications(token_hash)", """
        CREATE INDEX IF NOT EXISTS idx_email_verif_hash
        ON email_verifications(token_hash)
    """),
    ("Table 5: Users (auth, Phase 3)", """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            agency TEXT,
            role TEXT NOT NULL DEFAULT 'client',
            verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """),
    ("Table 6: Agencies (Phase 3)", """
        CREATE TABLE IF NOT EXISTS agencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """),
]

failed = []
for label, sql in statements:
    try:
        conn.execute(sql)
        print(f"✅ {label}")
    except Exception as e:
        print(f"❌ {label} — {type(e).__name__}: {e}")
        failed.append(label)

conn.commit()
conn.close()

print()
if failed:
    print(f"⚠️  Finished with {len(failed)} failure(s): {failed}")
else:
    print("✅ Success! The CRA relational schema is live on Turso.")