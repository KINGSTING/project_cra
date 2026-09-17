# api/assessment_report.py
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


def cors(origin: str) -> dict:
    return {
        "Access-Control-Allow-Origin": origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0],
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Vary": "Origin",
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

    def do_GET(self):
        origin = self.headers.get("Origin", "")
        try:
            user = require_user(self.headers)
        except PermissionError as e:
            return self._json(401, {"error": str(e)}, origin)

        aid = parse_qs(urlparse(self.path).query).get("assessment_id", [None])[0]
        if not aid:
            return self._json(400, {"error": "missing_assessment_id"}, origin)

        try:
            db = get_db()

            a = db.execute(
                "SELECT id, agency, title, cycle_year, status, created_at, updated_at "
                "FROM assessments WHERE id = ? AND user_id = ?",
                (aid, user["id"]),
            ).fetchone()
            if not a:
                return self._json(404, {"error": "not_found"}, origin)

            systems = db.execute(
                "SELECT id, name, description, high_impact, high_developmental, pro_poor, ranking "
                "FROM critical_systems WHERE assessment_id = ? "
                "ORDER BY COALESCE(ranking, 999), id",
                (aid,),
            ).fetchall()

            sys_ids = [s[0] for s in systems]
            steps_by_system = {}
            if sys_ids:
                placeholders = ",".join("?" * len(sys_ids))
                steps = db.execute(
                    f"SELECT id, critical_system_id, step_order, description, accountable_officer, "
                    f"inputs, outputs, duration, remarks FROM process_steps "
                    f"WHERE critical_system_id IN ({placeholders}) ORDER BY step_order, id",
                    tuple(sys_ids),
                ).fetchall()
                for st in steps:
                    steps_by_system.setdefault(st[1], []).append(st)

            all_step_ids = [st[0] for lst in steps_by_system.values() for st in lst]
            risks_by_step = {}
            if all_step_ids:
                placeholders = ",".join("?" * len(all_step_ids))
                risks = db.execute(
                    f"SELECT id, process_step_id, corruption_risk, corruption_scheme, "
                    f"probability, impact, inherent_risk, inherent_band, "
                    f"mitigating_control, control_rating, residual_risk, residual_band, "
                    f"integrity_measure, dimension FROM corruption_risks "
                    f"WHERE process_step_id IN ({placeholders}) ORDER BY id",
                    tuple(all_step_ids),
                ).fetchall()
                for r in risks:
                    risks_by_step.setdefault(r[1], []).append({
                        "id": r[0], "corruption_risk": r[2], "corruption_scheme": r[3],
                        "probability": r[4], "impact": r[5],
                        "inherent_risk": r[6], "inherent_band": r[7],
                        "mitigating_control": r[8], "control_rating": r[9],
                        "residual_risk": r[10], "residual_band": r[11],
                        "integrity_measure": r[12], "dimension": r[13],
                    })

            systems_out = []
            for s in systems:
                steps_out = []
                for st in steps_by_system.get(s[0], []):
                    steps_out.append({
                        "id": st[0], "step_order": st[2], "description": st[3],
                        "accountable_officer": st[4], "inputs": st[5],
                        "outputs": st[6], "duration": st[7], "remarks": st[8],
                        "corruption_risks": risks_by_step.get(st[0], []),
                    })
                systems_out.append({
                    "id": s[0], "name": s[1], "description": s[2],
                    "high_impact": bool(s[3]), "high_developmental": bool(s[4]),
                    "pro_poor": bool(s[5]), "ranking": s[6],
                    "process_steps": steps_out,
                })

            return self._json(200, {
                "assessment": {
                    "id": a[0], "agency": a[1], "title": a[2], "cycle_year": a[3],
                    "status": a[4], "created_at": a[5], "updated_at": a[6],
                },
                "critical_systems": systems_out,
            }, origin)
        except Exception as e:
            print(f"[assessment_report] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)