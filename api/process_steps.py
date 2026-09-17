# api/process_steps.py
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

FIELDS = ("id, critical_system_id, step_order, description, accountable_officer, "
          "inputs, outputs, duration, remarks, created_at")


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
        "id": row[0], "critical_system_id": row[1], "step_order": row[2],
        "description": row[3], "accountable_officer": row[4],
        "inputs": row[5], "outputs": row[6], "duration": row[7],
        "remarks": row[8], "created_at": row[9],
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

    def _owns_cs(self, db, cs_id, user_id):
        row = db.execute(
            "SELECT a.user_id FROM critical_systems cs "
            "JOIN assessments a ON cs.assessment_id = a.id "
            "WHERE cs.id = ?",
            (cs_id,),
        ).fetchone()
        return row is not None and row[0] == user_id

    def _owns_step(self, db, step_id, user_id):
        row = db.execute(
            "SELECT cs.id FROM process_steps ps "
            "JOIN critical_systems cs ON ps.critical_system_id = cs.id "
            "WHERE ps.id = ?",
            (step_id,),
        ).fetchone()
        return row is not None and self._owns_cs(db, row[0], user_id)

    # ------------------------------------------------------------------
    def do_GET(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        csid = self._qs().get("critical_system_id", [None])[0]
        if not csid:
            return self._json(400, {"error": "missing_critical_system_id"}, origin)

        try:
            db = get_db()
            if not self._owns_cs(db, csid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)
            rows = db.execute(
                f"SELECT {FIELDS} FROM process_steps "
                "WHERE critical_system_id = ? ORDER BY step_order, id",
                (csid,),
            ).fetchall()
            return self._json(200, {"process_steps": [row_to_dict(r) for r in rows]}, origin)
        except Exception as e:
            print(f"[process_steps GET] {type(e).__name__}: {e}")
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

        cs_id = data.get("critical_system_id")
        desc = (data.get("description") or "").strip()
        try:
            order = int(data.get("step_order") or 1)
        except (TypeError, ValueError):
            return self._json(400, {"error": "invalid_step_order"}, origin)

        if not cs_id or not desc or len(desc) > 500:
            return self._json(400, {"error": "invalid_input"}, origin)

        try:
            db = get_db()
            if not self._owns_cs(db, cs_id, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            row = db.execute(
                "INSERT INTO process_steps "
                "(critical_system_id, step_order, description, accountable_officer, "
                " inputs, outputs, duration, remarks) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING " + FIELDS,
                (
                    cs_id, order, desc,
                    data.get("accountable_officer") or None,
                    data.get("inputs") or None,
                    data.get("outputs") or None,
                    data.get("duration") or None,
                    data.get("remarks") or None,
                ),
            ).fetchone()
            db.commit()
            return self._json(201, {"process_step": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[process_steps POST] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_PATCH(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        sid = self._qs().get("id", [None])[0]
        if not sid:
            return self._json(400, {"error": "missing_id"}, origin)

        try:
            data = self._body()
        except Exception:
            return self._json(400, {"error": "invalid_json"}, origin)

        try:
            db = get_db()
            if not self._owns_step(db, sid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            allowed = {"step_order", "description", "accountable_officer",
                       "inputs", "outputs", "duration", "remarks"}
            updates = [(k, data[k]) for k in allowed if k in data]
            if not updates:
                return self._json(400, {"error": "no_fields"}, origin)

            set_clause = ", ".join(f"{k} = ?" for k, _ in updates)
            params = [v for _, v in updates] + [sid]

            db.execute(f"UPDATE process_steps SET {set_clause} WHERE id = ?", params)
            db.commit()

            row = db.execute(f"SELECT {FIELDS} FROM process_steps WHERE id = ?", (sid,)).fetchone()
            return self._json(200, {"process_step": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[process_steps PATCH] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_DELETE(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        if user["role"] != "admin":
            return self._json(403, {"error": "forbidden",
                                    "hint": "Only admins may delete."}, origin)

        return self._json(403, {"error": "admin_delete_not_implemented"}, origin)