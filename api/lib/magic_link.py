# lib/magic_link.py
import os
import hmac
import hashlib
import secrets
import resend
from datetime import datetime, timedelta, timezone

TOKEN_SECRET = os.environ.get("TOKEN_SECRET")
TOKEN_TTL_MINUTES = 30
DEFAULT_COOLDOWN_SECONDS = 5  # dev; bump to 60+ in prod


def hash_token(token: str) -> str:
    return hmac.new(
        TOKEN_SECRET.encode("utf-8"), token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _escape_html(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _build_html(agency: str, verify_url: str, ttl: int) -> str:
    a, u = _escape_html(agency), _escape_html(verify_url)
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f4f6f8;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1f2937;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:32px 0;">
      <tr><td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">
          <tr><td style="background:#0b3d91;padding:24px 32px;color:#ffffff;">
            <div style="font-size:12px;letter-spacing:1.5px;text-transform:uppercase;opacity:0.85;">Office of the President &middot; Office of the Ombudsman</div>
            <div style="font-size:20px;font-weight:600;margin-top:4px;">IMP-CRA Portal</div>
          </td></tr>
          <tr><td style="padding:32px;">
            <h1 style="margin:0 0 16px;font-size:20px;color:#0b3d91;">Sign in to IMP-CRA</h1>
            <p style="margin:0 0 16px;line-height:1.6;">
              Hello from <strong>{a}</strong>. Click the button below to sign in to the
              Integrity Management Program &ndash; Corruption Risk Assessment Portal.
            </p>
            <p style="margin:0 0 24px;">
              <a href="{u}" style="display:inline-block;background:#0b3d91;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:6px;font-weight:600;">
                Sign in
              </a>
            </p>
            <p style="margin:0 0 8px;font-size:13px;color:#6b7280;line-height:1.6;">
              This link expires in {ttl} minutes. If the button doesn't work, copy this URL:
            </p>
            <p style="margin:0 0 24px;font-size:12px;word-break:break-all;color:#0b3d91;">{u}</p>
            <p style="margin:0;font-size:12px;color:#6b7280;line-height:1.6;">
              If you did not request this, you can safely ignore it.
            </p>
          </td></tr>
          <tr><td style="background:#f9fafb;padding:16px 32px;font-size:11px;color:#9ca3af;text-align:center;">
            Automated message. Please do not reply.
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>
"""


def _build_text(agency: str, verify_url: str, ttl: int) -> str:
    return (
        f"IMP-CRA Portal — sign in\n\n"
        f"Hello from {agency}.\n\n"
        f"Open this link to sign in:\n{verify_url}\n\n"
        f"Expires in {ttl} minutes.\n"
    )


def create_and_send_link(
    db,
    email: str,
    agency: str,
    *,
    app_url: str,
    from_email: str,
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
) -> dict:
    """Generate a token, store its hash, and email the raw token.

    Returns {"status": "sent"} on success, or {"error": "...", ...} on failure.
    """
    # Cooldown check
    recent = db.execute(
        "SELECT created_at FROM email_verifications "
        "WHERE email = ? AND used_at IS NULL "
        "ORDER BY id DESC LIMIT 1",
        (email,),
    ).fetchone()
    if recent:
        try:
            last = datetime.fromisoformat(recent[0].replace("Z", "+00:00"))
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            delta = (datetime.now(timezone.utc) - last).total_seconds()
            if delta < cooldown_seconds:
                return {"error": "rate_limited",
                        "retry_after": int(cooldown_seconds - delta)}
        except Exception:
            pass

    raw_token  = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    expires_at = (datetime.now(timezone.utc)
                  + timedelta(minutes=TOKEN_TTL_MINUTES)).isoformat()

    db.execute(
        "UPDATE email_verifications SET used_at = datetime('now') "
        "WHERE email = ? AND used_at IS NULL",
        (email,),
    )
    db.execute(
        "INSERT INTO email_verifications (email, agency, token_hash, expires_at) "
        "VALUES (?, ?, ?, ?)",
        (email, agency, token_hash, expires_at),
    )
    db.commit()

    verify_url = f"{app_url.rstrip('/')}/verify?token={raw_token}"
    resend.api_key = os.environ.get("RESEND_API_KEY")
    resend.Emails.send({
        "from": from_email,
        "to": [email],
        "subject": "Sign in to IMP-CRA Portal",
        "html": _build_html(agency, verify_url, TOKEN_TTL_MINUTES),
        "text": _build_text(agency, verify_url, TOKEN_TTL_MINUTES),
    })
    return {"status": "sent"}