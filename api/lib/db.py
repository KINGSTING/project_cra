# lib/db.py
import os
import turso_serverless


def get_db():
    """Return a synchronous DB-API 2.0 connection to Turso Cloud."""
    return turso_serverless.connect(
        os.environ["TURSO_DATABASE_URL"],
        auth_token=os.environ["TURSO_AUTH_TOKEN"],
    )