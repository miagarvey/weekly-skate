from __future__ import annotations
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Tuple, List

from flask import Flask, request, redirect, url_for, render_template, abort
from pydantic import BaseModel, field_validator

# Optional Twilio (safe to leave unset; we'll "dry-run" to console)
try:
    from twilio.rest import Client
except Exception:
    Client = None  # type: ignore

app = Flask(__name__)

# --- Config & env ---
DB_PATH = os.environ.get("DB_PATH", "skate.db")
DEFAULT_QUOTA = int(os.environ.get("DEFAULT_QUOTA", "16"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
TWILIO_DRY_RUN = os.environ.get("TWILIO_DRY_RUN", "0") == "1"

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.environ.get("TWILIO_FROM")

def twilio_client():
    if TWILIO_SID and TWILIO_AUTH and Client is not None:
        return Client(TWILIO_SID, TWILIO_AUTH)
    return None

# --- DB bootstrap ---
SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS weeks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  iso_year INTEGER NOT NULL,
  iso_week INTEGER NOT NULL,
  quota INTEGER NOT NULL,
  goalie_notified INTEGER NOT NULL DEFAULT 0,
  UNIQUE(iso_year, iso_week)
);

CREATE TABLE IF NOT EXISTS signups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  week_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(week_id) REFERENCES weeks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS broadcasts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phone TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

with closing(db()) as conn:
    conn.executescript(SCHEMA)
    # ensure keys exist
    cur = conn.execute("SELECT value FROM settings WHERE key='goalie_phone'")
    if cur.fetchone() is None:
        conn.execute("INSERT INTO settings(key, value) VALUES('goalie_phone','')")
    conn.commit()

# --- Helpers ---
def get_week_key(dt: datetime | None = None) -> Tuple[int, int]:
    dt = dt or datetime.now()
    iso_year, iso_week, _ = dt.isocalendar()
    return iso_year, iso_week

def get_or_create_current_week() -> int:
    y, w = get_week_key()
    with closing(db()) as conn:
        row = conn.execute(
            "SELECT id FROM weeks WHERE iso_year=? AND iso_week=?",
            (y, w)
        ).fetchone()
        if row:
            return row[0]
        conn.execute(
            "INSERT INTO weeks(iso_year, iso_week, quota) VALUES(?,?,?)",
            (y, w, DEFAULT_QUOTA)
        )
        conn.commit()
        return conn.execute(
            "SELECT id FROM weeks WHERE iso_year=? AND iso_week=?",
            (y, w)
        ).fetchone()[0]

def get_week_info(week_id: int):
    with closing(db()) as conn:
        week = conn.execute(
            "SELECT iso_year, iso_week, quota, goalie_notified FROM weeks WHERE id=?",
            (week_id,)
        ).fetchone()
        signups = conn.execute(
            "SELECT name, phone, created_at FROM signups WHERE week_id=? ORDER BY created_at ASC",
            (week_id,)
        ).fetchall()
        return week, signups

def set_quota(week_id: int, quota: int):
    with closing(db()) as conn:
        conn.execute("UPDATE weeks SET quota=? WHERE id=?", (quota, week_id))
        conn.commit()

def is_e164(phone: str) -> bool:
    phone = phone.strip()
    return phone.startswith("+") and phone[1:].isdigit() and 8 <= len(phone) <= 16

def add_broadcast_number(phone: str):
    with closing(db()) as conn:
        conn.execute("INSERT INTO broadcasts(phone) VALUES(?)", (phone,))
        conn.commit()

def remove_broadcast_number(phone: str):
    with closing(db()) as conn:
        conn.execute("DELETE FROM broadcasts WHERE phone=?", (phone,))
        conn.commit()

def get_broadcast_numbers() -> List[str]:
    with closing(db()) as conn:
        return [r[0] for r in conn.execute("SELECT phone FROM broadcasts ORDER BY id").fetchall()]

def get_goalie_phone() -> str:
    with closing(db()) as conn:
        return conn.execute("SELECT value FROM settings WHERE key='goalie_phone'").fetchone()[0]

def set_goalie_phone(phone: str):
    with closing(db()) as conn:
        conn.execute("UPDATE settings SET value=? WHERE key='goalie_phone'", (phone,))
        conn.commit()

def mark_goalie_notified(week_id: int):
    with closing(db()) as conn:
        conn.execute("UPDATE weeks SET goalie_notified=1 WHERE id=?", (week_id,))
        conn.commit()

# --- Validation models ---
class Signup(BaseModel):
    name: str
    phone: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name required")
        return v

    @field_validator("phone")
    @classmethod
    def phone_e164_or_blank(cls, v):
        if v is None or v.strip() == "":
            return None
        v = v.strip()
        if is_e164(v):
            return v
        raise ValueError("Phone must be +E.164 like +15551234567 or leave blank")

# --- Messaging ---
def format_signup_list(signups) -> str:
    if not signups:
        return "No signups yet."
    lines = ["Weekly Skate Signups:"]
    for idx, (name, phone, created_at) in enumerate(signups, 1):
        p = phone or "(no phone)"
        t = created_at.split(".")[0].replace("T", " ")
        lines.append(f"{idx}. {name} {p} – {t}")
    return "\n".join(lines)

def send_sms(to: str, body: str):
    if TWILIO_DRY_RUN:
        print(f"[SMS DRY-RUN to {to}]\n{body}\n---")
        return
    client = twilio_client()
    if client and (TWILIO_FROM or os.environ.get("TWILIO_MESSAGING_SERVICE_SID")):
        try:
            params = {"to": to, "body": body}
            if os.environ.get("TWILIO_MESSAGING_SERVICE_SID"):
                params["messaging_service_sid"] = os.environ["TWILIO_MESSAGING_SERVICE_SID"]
            else:
                params["from_"] = TWILIO_FROM
            msg = client.messages.create(**params)
            print(f"[SMS SENT] to {to} sid={msg.sid}")
        except Exception as e:
            print(f"[SMS ERROR] to {to}: {e}")
    else:
        print(f"[SMS DRY-RUN to {to}]\n{body}\n---")

def broadcast_signups(signups) -> int:
    nums = get_broadcast_numbers()
    if not nums:
        return 0
    body = format_signup_list(signups)
    for n in nums:
        send_sms(n, body)
    return len(nums)

def notify_goalie_if_needed(week_id: int):
    # check state and possibly send
    (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
    if goalie_notified:
        return False
    if len(signups) >= quota:
        goalie_phone = get_goalie_phone()
        if not goalie_phone:
            print("[goalie_notify] quota reached but no goalie phone set")
            return False
        body = (
            f"Quota reached for Week {iso_week}, {iso_year}!\n"
            f"Total signups: {len(signups)} (quota {quota}).\n"
            f"Please secure a goalie.\n\n" + format_signup_list(signups)
        )
        send_sms(goalie_phone, body)
        mark_goalie_notified(week_id)
        return True
    return False

# --- Admin auth helper ---
def require_admin():
    token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ","").strip()
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        abort(401)

# --- Routes ---
@app.get("/")
def home():
    week_id = get_or_create_current_week()
    (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
    return render_template(
        "home.html",
        iso_year=iso_year,
        iso_week=iso_week,
        quota=quota,
        count=len(signups),
        signups=signups
    )

@app.post("/signup")
def submit_signup():
    week_id = get_or_create_current_week()
    # validate
    try:
        data = Signup(name=request.form.get("name",""), phone=request.form.get("phone"))
    except Exception as e:
        return redirect(url_for("home") + f"?error={str(e)}")

    # insert
    with closing(db()) as conn:
        conn.execute(
            "INSERT INTO signups(week_id, name, phone, created_at) VALUES(?,?,?,?)",
            (week_id, data.name, data.phone, datetime.utcnow().isoformat())
        )
        conn.commit()

    # auto-notify goalie if quota hit (one-time)
    notify_goalie_if_needed(week_id)
    return redirect(url_for("home"))

# --- Admin panel ---
@app.get("/admin")
def admin():
    require_admin()
    week_id = get_or_create_current_week()
    (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
    numbers = get_broadcast_numbers()
    goalie_phone = get_goalie_phone()
    return render_template(
        "admin.html",
        token=request.args.get("token",""),
        iso_year=iso_year, iso_week=iso_week,
        quota=quota, count=len(signups),
        goalie_notified=bool(goalie_notified),
        numbers=numbers, goalie_phone=goalie_phone
    )

@app.post("/admin/quota")
def admin_set_quota():
    require_admin()
    week_id = get_or_create_current_week()
    q = int(request.form.get("quota","0"))
    if q < 1:
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=bad_quota")
    set_quota(week_id, q)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/broadcast/add")
def admin_add_number():
    require_admin()
    phone = request.form.get("phone","").strip()
    if not is_e164(phone):
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=bad_phone")
    add_broadcast_number(phone)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/broadcast/remove")
def admin_remove_number():
    require_admin()
    phone = request.form.get("phone","").strip()
    remove_broadcast_number(phone)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/broadcast/send")
def admin_broadcast():
    require_admin()
    week_id = get_or_create_current_week()
    _, signups = get_week_info(week_id)
    broadcast_signups(signups)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/goalie")
def admin_set_goalie():
    require_admin()
    phone = request.form.get("goalie_phone","").strip()
    if phone and not is_e164(phone):
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=bad_goalie")
    set_goalie_phone(phone)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/notify-goalie")
def admin_notify_goalie():
    require_admin()
    week_id = get_or_create_current_week()
    notify_goalie_if_needed(week_id)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/test-sms")
def admin_test_sms():
    require_admin()
    phone = request.form.get("test_phone","").strip() or get_goalie_phone()
    if not phone:
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=no_phone")
    send_sms(phone, "Test from Weekly Skate admin.")
    return redirect(url_for("admin", token=request.args.get("token","")) + "?ok=test_sent")


# (Optional) quick health
@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    app.run(debug=True)
