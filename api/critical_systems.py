# api/critical_systems.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import traceback
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler
from lib.db import get_db
from lib.session_guard import require_user

ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

FIELDS = "id, assessment_id, name, description, high_impact, high_developmental, pro_poor, ranking, created_at"


def cors(origin: str) -> dict:
    return {
        "Access-Control-Allow-Origin": origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0],
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


def row_to_dict(row) -> dict:
    return {
        "id": row[0], "assessment_id": row[1], "name": row[2], "description": row[3],
        "high_impact": bool(row[4]), "high_developmental": bool(row[5]),
        "pro_poor": bool(row[6]), "ranking": row[7], "created_at": row[8],
    }


class handler(BaseHTTPRequestHandler):
    def _json(self, code, payload, origin=""):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in cors(origin).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in cors(self.headers.get("Origin", "")).items():
            self.send_header(k, v)
        self.end_headers()

    def _user_or_401(self, origin):
        try:
            return require_user(self.headers), None
        except PermissionError as e:
            return None, self._json(401, {"error": str(e)}, origin)

    def _qs(self):
        return parse_qs(urlparse(self.path).query)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _owns_assessment(self, db, aid, user_id):
        """Return True if the user owns the assessment."""
        row = db.execute(
            "SELECT id FROM assessments WHERE id = ? AND user_id = ?",
            (aid, user_id),
        ).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    def do_GET(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        aid = self._qs().get("assessment_id", [None])[0]
        if not aid:
            return self._json(400, {"error": "missing_assessment_id"}, origin)

        try:
            db = get_db()
            if not self._owns_assessment(db, aid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)
            rows = db.execute(
                f"SELECT {FIELDS} FROM critical_systems "
                "WHERE assessment_id = ? "
                "ORDER BY COALESCE(ranking, 999), id",
                (aid,),
            ).fetchall()
            return self._json(200, {"critical_systems": [row_to_dict(r) for r in rows]}, origin)
        except Exception as e:
            print(f"[critical_systems GET] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_POST(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        try:
            data = self._body()
        except Exception:
            return self._json(400, {"error": "invalid_json"}, origin)

        aid = data.get("assessment_id")
        name = (data.get("name") or "").strip()
        if not aid or not name or len(name) > 200:
            return self._json(400, {"error": "invalid_input"}, origin)

        try:
            db = get_db()
            if not self._owns_assessment(db, aid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            row = db.execute(
                "INSERT INTO critical_systems "
                "(assessment_id, name, description, high_impact, high_developmental, pro_poor, ranking) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING " + FIELDS,
                (
                    aid,
                    name,
                    data.get("description") or None,
                    1 if data.get("high_impact") else 0,
                    1 if data.get("high_developmental") else 0,
                    1 if data.get("pro_poor") else 0,
                    data.get("ranking"),
                ),
            ).fetchone()
            db.commit()

            # Touch the assessment's updated_at so the list sorts correctly
            db.execute("UPDATE assessments SET updated_at = datetime('now') WHERE id = ?", (aid,))
            db.commit()

            return self._json(201, {"critical_system": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[critical_systems POST] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_PATCH(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        csid = self._qs().get("id", [None])[0]
        if not csid:
            return self._json(400, {"error": "missing_id"}, origin)

        try:
            data = self._body()
        except Exception:
            return self._json(400, {"error": "invalid_json"}, origin)

        try:
            db = get_db()
            row = db.execute(
                "SELECT assessment_id FROM critical_systems WHERE id = ?", (csid,)
            ).fetchone()
            if not row or not self._owns_assessment(db, row[0], user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            allowed = {"name", "description", "high_impact", "high_developmental", "pro_poor", "ranking"}
            updates = [(k, data[k]) for k in allowed if k in data]
            if not updates:
                return self._json(400, {"error": "no_fields"}, origin)

            for k, v in updates:
                if k in ("high_impact", "high_developmental", "pro_poor") and v is not None:
                    updates[updates.index((k, v))] = (k, 1 if v else 0)

            set_clause = ", ".join(f"{k} = ?" for k, _ in updates)
            params = [v for _, v in updates] + [csid]

            db.execute(f"UPDATE critical_systems SET {set_clause} WHERE id = ?", params)
            db.commit()

            new_row = db.execute(f"SELECT {FIELDS} FROM critical_systems WHERE id = ?", (csid,)).fetchone()
            return self._json(200, {"critical_system": row_to_dict(new_row)}, origin)
        except Exception as e:
            print(f"[critical_systems PATCH] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_DELETE(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        csid = self._qs().get("id", [None])[0]
        if not csid:
            return self._json(400, {"error": "missing_id"}, origin)

        try:
            db = get_db()
            row = db.execute(
                "SELECT assessment_id FROM critical_systems WHERE id = ?", (csid,)
            ).fetchone()
            if not row or not self._owns_assessment(db, row[0], user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            db.execute("DELETE FROM critical_systems WHERE id = ?", (csid,))
            db.commit()
            return self._json(200, {"status": "deleted"}, origin)
        except Exception as e:
            print(f"[critical_systems DELETE] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    def do_DELETE(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        if user["role"] != "admin":
            return self._json(403, {"error": "forbidden",
                                    "hint": "Only admins may delete."}, origin)
        return self._json(403, {"error": "admin_delete_not_implemented"}, origin)