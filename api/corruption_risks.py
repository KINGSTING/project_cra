# api/corruption_risks.py
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

DIMENSIONS = {
    "service_delivery",
    "institutional_leadership",
    "financial_procurement_asset",
    "human_resource",
    "corruption_risk_mgmt",
    "internal_reporting_investigation",
}

FIELDS = ("id, process_step_id, corruption_risk, corruption_scheme, probability, impact, "
          "inherent_risk, inherent_band, mitigating_control, control_rating, "
          "residual_risk, residual_band, integrity_measure, dimension, created_at")


def cors(origin: str) -> dict:
    return {
        "Access-Control-Allow-Origin": origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0],
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


def risk_band(score: float) -> str:
    if score >= 11: return "H"
    if score >= 6:  return "M"
    return "L"


def compute_risk(probability, impact, control_rating):
    """Return (inherent_risk, inherent_band, residual_band) per the IMP Handbook."""
    if probability is None or impact is None:
        return None, None, None
    inherent = (probability + impact) / 2
    in_band = risk_band(inherent)
    order = ["L", "M", "H"]
    i = order.index(in_band)
    if control_rating == "H":
        i = max(0, i - 1)
    elif control_rating == "L":
        i = min(2, i + 1)
    return inherent, in_band, order[i]


def row_to_dict(row) -> dict:
    return {
        "id": row[0], "process_step_id": row[1],
        "corruption_risk": row[2], "corruption_scheme": row[3],
        "probability": row[4], "impact": row[5],
        "inherent_risk": row[6], "inherent_band": row[7],
        "mitigating_control": row[8], "control_rating": row[9],
        "residual_risk": row[10], "residual_band": row[11],
        "integrity_measure": row[12], "dimension": row[13],
        "created_at": row[14],
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

    def _owns_step(self, db, step_id, user_id):
        row = db.execute(
            "SELECT a.user_id FROM process_steps ps "
            "JOIN critical_systems cs ON ps.critical_system_id = cs.id "
            "JOIN assessments a ON cs.assessment_id = a.id "
            "WHERE ps.id = ?",
            (step_id,),
        ).fetchone()
        return row is not None and row[0] == user_id

    def _owns_risk(self, db, risk_id, user_id):
        row = db.execute(
            "SELECT ps.id FROM corruption_risks cr "
            "JOIN process_steps ps ON cr.process_step_id = ps.id "
            "WHERE cr.id = ?",
            (risk_id,),
        ).fetchone()
        return row is not None and self._owns_step(db, row[0], user_id)

    def _validate(self, data):
        prob = data.get("probability")
        imp = data.get("impact")
        try:
            prob = int(prob) if prob not in (None, "") else None
            imp = int(imp) if imp not in (None, "") else None
        except (TypeError, ValueError):
            return None, "invalid_probability_or_impact"
        if prob is not None and not (1 <= prob <= 15):
            return None, "probability_out_of_range"
        if imp is not None and not (1 <= imp <= 15):
            return None, "impact_out_of_range"
        ctrl = data.get("control_rating")
        if ctrl not in (None, "", "H", "M", "L"):
            return None, "invalid_control_rating"
        dim = data.get("dimension")
        if dim and dim not in DIMENSIONS:
            return None, "invalid_dimension"
        return {"probability": prob, "impact": imp, "control_rating": ctrl or None}, None

    # ------------------------------------------------------------------
    def do_GET(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        sid = self._qs().get("process_step_id", [None])[0]
        if not sid:
            return self._json(400, {"error": "missing_process_step_id"}, origin)

        try:
            db = get_db()
            if not self._owns_step(db, sid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)
            rows = db.execute(
                f"SELECT {FIELDS} FROM corruption_risks "
                "WHERE process_step_id = ? ORDER BY id",
                (sid,),
            ).fetchall()
            return self._json(200, {"corruption_risks": [row_to_dict(r) for r in rows]}, origin)
        except Exception as e:
            print(f"[corruption_risks GET] {type(e).__name__}: {e}")
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

        sid = data.get("process_step_id")
        if not sid:
            return self._json(400, {"error": "missing_process_step_id"}, origin)

        clean, verr = self._validate(data)
        if verr:
            return self._json(400, {"error": verr}, origin)

        inherent, in_band, res_band = compute_risk(
            clean["probability"], clean["impact"], clean["control_rating"]
        )

        try:
            db = get_db()
            if not self._owns_step(db, sid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            row = db.execute(
                "INSERT INTO corruption_risks "
                "(process_step_id, corruption_risk, corruption_scheme, probability, impact, "
                " inherent_risk, inherent_band, mitigating_control, control_rating, "
                " residual_risk, residual_band, integrity_measure, dimension) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING " + FIELDS,
                (
                    sid,
                    data.get("corruption_risk") or None,
                    data.get("corruption_scheme") or None,
                    clean["probability"],
                    clean["impact"],
                    inherent, in_band,
                    data.get("mitigating_control") or None,
                    clean["control_rating"],
                    data.get("residual_risk") or None,
                    res_band,
                    data.get("integrity_measure") or None,
                    data.get("dimension") or None,
                ),
            ).fetchone()
            db.commit()
            return self._json(201, {"corruption_risk": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[corruption_risks POST] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_PATCH(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        rid = self._qs().get("id", [None])[0]
        if not rid:
            return self._json(400, {"error": "missing_id"}, origin)

        try:
            data = self._body()
        except Exception:
            return self._json(400, {"error": "invalid_json"}, origin)

        try:
            db = get_db()
            if not self._owns_risk(db, rid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            clean, verr = self._validate(data)
            if verr:
                return self._json(400, {"error": verr}, origin)

            # Read current row to fill in missing fields for risk recomputation
            cur = db.execute(
                "SELECT probability, impact, control_rating FROM corruption_risks WHERE id = ?",
                (rid,),
            ).fetchone()
            prob = clean["probability"] if "probability" in data else cur[0]
            imp  = clean["impact"]      if "impact"      in data else cur[1]
            ctrl = clean["control_rating"] if "control_rating" in data else cur[2]

            inherent, in_band, res_band = compute_risk(prob, imp, ctrl)

            allowed = {"corruption_risk", "corruption_scheme", "probability", "impact",
                       "mitigating_control", "control_rating", "residual_risk",
                       "integrity_measure", "dimension"}
            updates = [(k, data[k]) for k in allowed if k in data]

            # Always refresh computed fields
            updates.append(("inherent_risk", inherent))
            updates.append(("inherent_band", in_band))
            updates.append(("residual_band", res_band))

            set_clause = ", ".join(f"{k} = ?" for k, _ in updates)
            params = [v for _, v in updates] + [rid]

            db.execute(f"UPDATE corruption_risks SET {set_clause} WHERE id = ?", params)
            db.commit()

            row = db.execute(f"SELECT {FIELDS} FROM corruption_risks WHERE id = ?", (rid,)).fetchone()
            return self._json(200, {"corruption_risk": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[corruption_risks PATCH] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_DELETE(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        if user["role"] != "admin":
            return self._json(403, {"error": "forbidden"}, origin)
        return self._json(403, {"error": "admin_delete_not_implemented"}, origin)# api/corruption_risks.py
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

DIMENSIONS = {
    "service_delivery",
    "institutional_leadership",
    "financial_procurement_asset",
    "human_resource",
    "corruption_risk_mgmt",
    "internal_reporting_investigation",
}

FIELDS = ("id, process_step_id, corruption_risk, corruption_scheme, probability, impact, "
          "inherent_risk, inherent_band, mitigating_control, control_rating, "
          "residual_risk, residual_band, integrity_measure, dimension, created_at")


def cors(origin: str) -> dict:
    return {
        "Access-Control-Allow-Origin": origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0],
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


def risk_band(score: float) -> str:
    if score >= 11: return "H"
    if score >= 6:  return "M"
    return "L"


def compute_risk(probability, impact, control_rating):
    """Return (inherent_risk, inherent_band, residual_band) per the IMP Handbook."""
    if probability is None or impact is None:
        return None, None, None
    inherent = (probability + impact) / 2
    in_band = risk_band(inherent)
    order = ["L", "M", "H"]
    i = order.index(in_band)
    if control_rating == "H":
        i = max(0, i - 1)
    elif control_rating == "L":
        i = min(2, i + 1)
    return inherent, in_band, order[i]


def row_to_dict(row) -> dict:
    return {
        "id": row[0], "process_step_id": row[1],
        "corruption_risk": row[2], "corruption_scheme": row[3],
        "probability": row[4], "impact": row[5],
        "inherent_risk": row[6], "inherent_band": row[7],
        "mitigating_control": row[8], "control_rating": row[9],
        "residual_risk": row[10], "residual_band": row[11],
        "integrity_measure": row[12], "dimension": row[13],
        "created_at": row[14],
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

    def _owns_step(self, db, step_id, user_id):
        row = db.execute(
            "SELECT a.user_id FROM process_steps ps "
            "JOIN critical_systems cs ON ps.critical_system_id = cs.id "
            "JOIN assessments a ON cs.assessment_id = a.id "
            "WHERE ps.id = ?",
            (step_id,),
        ).fetchone()
        return row is not None and row[0] == user_id

    def _owns_risk(self, db, risk_id, user_id):
        row = db.execute(
            "SELECT ps.id FROM corruption_risks cr "
            "JOIN process_steps ps ON cr.process_step_id = ps.id "
            "WHERE cr.id = ?",
            (risk_id,),
        ).fetchone()
        return row is not None and self._owns_step(db, row[0], user_id)

    def _validate(self, data):
        prob = data.get("probability")
        imp = data.get("impact")
        try:
            prob = int(prob) if prob not in (None, "") else None
            imp = int(imp) if imp not in (None, "") else None
        except (TypeError, ValueError):
            return None, "invalid_probability_or_impact"
        if prob is not None and not (1 <= prob <= 15):
            return None, "probability_out_of_range"
        if imp is not None and not (1 <= imp <= 15):
            return None, "impact_out_of_range"
        ctrl = data.get("control_rating")
        if ctrl not in (None, "", "H", "M", "L"):
            return None, "invalid_control_rating"
        dim = data.get("dimension")
        if dim and dim not in DIMENSIONS:
            return None, "invalid_dimension"
        return {"probability": prob, "impact": imp, "control_rating": ctrl or None}, None

    # ------------------------------------------------------------------
    def do_GET(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        sid = self._qs().get("process_step_id", [None])[0]
        if not sid:
            return self._json(400, {"error": "missing_process_step_id"}, origin)

        try:
            db = get_db()
            if not self._owns_step(db, sid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)
            rows = db.execute(
                f"SELECT {FIELDS} FROM corruption_risks "
                "WHERE process_step_id = ? ORDER BY id",
                (sid,),
            ).fetchall()
            return self._json(200, {"corruption_risks": [row_to_dict(r) for r in rows]}, origin)
        except Exception as e:
            print(f"[corruption_risks GET] {type(e).__name__}: {e}")
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

        sid = data.get("process_step_id")
        if not sid:
            return self._json(400, {"error": "missing_process_step_id"}, origin)

        clean, verr = self._validate(data)
        if verr:
            return self._json(400, {"error": verr}, origin)

        inherent, in_band, res_band = compute_risk(
            clean["probability"], clean["impact"], clean["control_rating"]
        )

        try:
            db = get_db()
            if not self._owns_step(db, sid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            row = db.execute(
                "INSERT INTO corruption_risks "
                "(process_step_id, corruption_risk, corruption_scheme, probability, impact, "
                " inherent_risk, inherent_band, mitigating_control, control_rating, "
                " residual_risk, residual_band, integrity_measure, dimension) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING " + FIELDS,
                (
                    sid,
                    data.get("corruption_risk") or None,
                    data.get("corruption_scheme") or None,
                    clean["probability"],
                    clean["impact"],
                    inherent, in_band,
                    data.get("mitigating_control") or None,
                    clean["control_rating"],
                    data.get("residual_risk") or None,
                    res_band,
                    data.get("integrity_measure") or None,
                    data.get("dimension") or None,
                ),
            ).fetchone()
            db.commit()
            return self._json(201, {"corruption_risk": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[corruption_risks POST] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_PATCH(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        rid = self._qs().get("id", [None])[0]
        if not rid:
            return self._json(400, {"error": "missing_id"}, origin)

        try:
            data = self._body()
        except Exception:
            return self._json(400, {"error": "invalid_json"}, origin)

        try:
            db = get_db()
            if not self._owns_risk(db, rid, user["id"]):
                return self._json(404, {"error": "not_found"}, origin)

            clean, verr = self._validate(data)
            if verr:
                return self._json(400, {"error": verr}, origin)

            # Read current row to fill in missing fields for risk recomputation
            cur = db.execute(
                "SELECT probability, impact, control_rating FROM corruption_risks WHERE id = ?",
                (rid,),
            ).fetchone()
            prob = clean["probability"] if "probability" in data else cur[0]
            imp  = clean["impact"]      if "impact"      in data else cur[1]
            ctrl = clean["control_rating"] if "control_rating" in data else cur[2]

            inherent, in_band, res_band = compute_risk(prob, imp, ctrl)

            allowed = {"corruption_risk", "corruption_scheme", "probability", "impact",
                       "mitigating_control", "control_rating", "residual_risk",
                       "integrity_measure", "dimension"}
            updates = [(k, data[k]) for k in allowed if k in data]

            # Always refresh computed fields
            updates.append(("inherent_risk", inherent))
            updates.append(("inherent_band", in_band))
            updates.append(("residual_band", res_band))

            set_clause = ", ".join(f"{k} = ?" for k, _ in updates)
            params = [v for _, v in updates] + [rid]

            db.execute(f"UPDATE corruption_risks SET {set_clause} WHERE id = ?", params)
            db.commit()

            row = db.execute(f"SELECT {FIELDS} FROM corruption_risks WHERE id = ?", (rid,)).fetchone()
            return self._json(200, {"corruption_risk": row_to_dict(row)}, origin)
        except Exception as e:
            print(f"[corruption_risks PATCH] {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "server_error"}, origin)

    # ------------------------------------------------------------------
    def do_DELETE(self):
        origin = self.headers.get("Origin", "")
        user, err = self._user_or_401(origin)
        if err: return

        if user["role"] != "admin":
            return self._json(403, {"error": "forbidden"}, origin)
        return self._json(403, {"error": "admin_delete_not_implemented"}, origin)