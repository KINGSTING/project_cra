# api/assessments.py
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

FIELDS = "id, user_id, agency, title, cycle_year, status, created_at, updated_at"


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
        "id": row[0], "user_id": row[1], "agency": row[2], "title": row[3],
        "cycle_year": row[4], "status": row[5],
        "created_at": row[6], "updated_at": row[7],
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

    # ------------------------------------------------------------------
    def do_GET(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        qs = self._qs()
        aid = qs.get("id", [None])[0]

        try:
            db = get_db()
            if aid:
                row = db.execute(
                    f"SELECT {FIELDS} FROM assessments WHERE id = ? AND user_id = ?",
                    (aid, user["id"]),
                ).fetchone()
                if not row:
                    return self._json(404, {"error": "not_found"}, origin)
                return self._json(200, {"assessment": row_to_dict(row)}, origin)
            else:
                rows = db.execute(
                    f"SELECT {FIELDS} FROM assessments WHERE user_id = ? ORDER BY updated_at DESC",
                    (user["id"],),
                ).fetchall()
                return self._json(200, {"assessments": [row_to_dict(r) for r in rows]}, origin)
        except Exception as e:
            print(f"[assessments GET] {type(e).__name__}: {e}")
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

        title = (data.get("title") or "").strip()
        try:
            cycle_year = int(data.get("cycle_year"))
        except (TypeError, ValueError):
            return self._json(400, {"error": "invalid_cycle_year"}, origin)

        if not title or len(title) > 200:
            return self._json(400, {"error": "invalid_title"}, origin)
        if not (2000 <= cycle_year <= 2100):
            return self._json(400, {"error": "invalid_cycle_year"}, origin)

        try:
            db = get_db()
            row = db.execute(
                "INSERT INTO assessments (user_id, agency, title, cycle_year, status) "
                "VALUES (?, ?, ?, ?, 'draft') RETURNING " + FIELDS,
                (user["id"], user["agency"], title, cycle_year),
            ).fetchone()
            db.commit()
            return self._json(201, {"assessment": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[assessments POST] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_PATCH(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        aid = self._qs().get("id", [None])[0]
        if not aid:
            return self._json(400, {"error": "missing_id"}, origin)

        try:
            data = self._body()
        except Exception:
            return self._json(400, {"error": "invalid_json"}, origin)

        allowed = {"title", "cycle_year", "status"}
        updates = [(k, data[k]) for k in allowed if k in data]
        if not updates:
            return self._json(400, {"error": "no_fields"}, origin)

        set_clause = ", ".join(f"{k} = ?" for k, _ in updates) + ", updated_at = datetime('now')"
        params = [v for _, v in updates] + [aid, user["id"]]

        try:
            db = get_db()
            exists = db.execute(
                "SELECT id FROM assessments WHERE id = ? AND user_id = ?",
                (aid, user["id"]),
            ).fetchone()
            if not exists:
                return self._json(404, {"error": "not_found"}, origin)

            db.execute(f"UPDATE assessments SET {set_clause} WHERE id = ? AND user_id = ?", params)
            db.commit()

            row = db.execute(f"SELECT {FIELDS} FROM assessments WHERE id = ?", (aid,)).fetchone()
            return self._json(200, {"assessment": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[assessments PATCH] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_DELETE(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        aid = self._qs().get("id", [None])[0]
        if not aid:
            return self._json(400, {"error": "missing_id"}, origin)

        try:
            db = get_db()
            exists = db.execute(
                "SELECT id FROM assessments WHERE id = ? AND user_id = ?",
                (aid, user["id"]),
            ).fetchone()
            if not exists:
                return self._json(404, {"error": "not_found"}, origin)

            db.execute("DELETE FROM assessments WHERE id = ? AND user_id = ?", (aid, user["id"]))
            db.commit()
            return self._json(200, {"status": "deleted"}, origin)
        except Exception as e:
            print(f"[assessments DELETE] {type(e).__name__}: {e}")
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