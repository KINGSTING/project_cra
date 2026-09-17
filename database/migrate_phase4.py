# database/migrate_phase4.py
import os
import turso_serverless
from dotenv import load_dotenv

load_dotenv(".env.local")

print("Connecting to Turso Cloud...")
conn = turso_serverless.connect(
    os.environ["TURSO_DATABASE_URL"],
    auth_token=os.environ["TURSO_AUTH_TOKEN"],
)

# Drop the old assessments/processes/risks tables — no production data yet.
# This lets us move to INTEGER PKs with proper foreign keys, matching users.
print("\nDropping legacy CRA tables (assessments, processes, risks)...")
for t in ("risks", "processes", "assessments"):
    conn.execute(f"DROP TABLE IF EXISTS {t}")

statements = [
    # ---- assessments (one per agency cycle) ----
    ("Table: assessments", """
        CREATE TABLE assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            agency TEXT NOT NULL,
            title TEXT NOT NULL,
            cycle_year INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """),
    ("Index: assessments(user_id)", """
        CREATE INDEX idx_assessments_user ON assessments(user_id)
    """),

    # ---- Template 1: Critical Systems ----
    ("Table: critical_systems", """
        CREATE TABLE critical_systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            high_impact INTEGER NOT NULL DEFAULT 0,
            high_developmental INTEGER NOT NULL DEFAULT 0,
            pro_poor INTEGER NOT NULL DEFAULT 0,
            ranking INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
        )
    """),
    ("Index: critical_systems(assessment_id)", """
        CREATE INDEX idx_cs_assessment ON critical_systems(assessment_id)
    """),

    # ---- Template 2: Process Matrix (steps) ----
    ("Table: process_steps", """
        CREATE TABLE process_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            critical_system_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            description TEXT NOT NULL,
            accountable_officer TEXT,
            inputs TEXT,
            outputs TEXT,
            duration TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (critical_system_id) REFERENCES critical_systems(id) ON DELETE CASCADE
        )
    """),
    ("Index: process_steps(critical_system_id)", """
        CREATE INDEX idx_ps_cs ON process_steps(critical_system_id)
    """),

    # ---- Template 3: Corruption Risk Register ----
    ("Table: corruption_risks", """
        CREATE TABLE corruption_risks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_step_id INTEGER NOT NULL,
            corruption_risk TEXT,
            corruption_scheme TEXT,
            probability INTEGER,
            impact INTEGER,
            inherent_risk REAL,
            inherent_band TEXT,
            mitigating_control TEXT,
            control_rating TEXT,
            residual_risk TEXT,
            residual_band TEXT,
            integrity_measure TEXT,
            dimension TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (process_step_id) REFERENCES process_steps(id) ON DELETE CASCADE
        )
    """),
    ("Index: corruption_risks(process_step_id)", """
        CREATE INDEX idx_cr_step ON corruption_risks(process_step_id)
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
    print("✅ Phase 4 schema is live.")