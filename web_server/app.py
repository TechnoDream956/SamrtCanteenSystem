from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import time, json, os, subprocess

app = Flask(__name__)

# ── CORS: Simple wildcard for production, more robust for cross-site fetches
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
CORS(app, origins=ALLOWED_ORIGINS, 
     supports_credentials=False,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

# ── JWT: reads JWT_SECRET_KEY or API_SECRET (Railway sets API_SECRET) ─────────
app.config["JWT_SECRET_KEY"] = (
    os.environ.get("JWT_SECRET_KEY") or
    os.environ.get("API_SECRET") or
    "local-dev-secret-change-in-prod"
)
jwt = JWTManager(app)
# --- GLOBAL ERROR HANDLER FOR CORS-SAFE ERROR REPORTING ---
@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException): return e
    # Return JSON with CORS headers for everything else
    return jsonify({"error": f"🔥 SERVER CRASH: {str(e)}"}), 500

# ── Database: PostgreSQL on Railway, SQLite locally ───────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Railway sometimes gives postgres:// — psycopg2 needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)

def db_conn():
    """Return a connection + placeholder character for the active DB."""
    if USE_POSTGRES:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn, "%s"
    else:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), "canteen.db")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn, "?"

def row_to_dict(row, cursor=None):
    """Convert a DB row to a plain dict regardless of DB engine."""
    if USE_POSTGRES:
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))
    else:
        return dict(row)

# ── Init DB ───────────────────────────────────────────────────────────────────
def init_db():
    conn, ph = db_conn()
    cur = conn.cursor()

    if USE_POSTGRES:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id             SERIAL PRIMARY KEY,
            name           TEXT,
            email          TEXT UNIQUE,
            password       TEXT,
            role           TEXT DEFAULT 'student',
            canteen_id     INTEGER,
            phone          TEXT,
            enrollment_no  TEXT,
            phone_verified INTEGER DEFAULT 0,
            registered_at  DOUBLE PRECISION DEFAULT 0,
            last_login     DOUBLE PRECISION DEFAULT 0
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS canteens(
            id   SERIAL PRIMARY KEY,
            name TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            order_id      BIGINT PRIMARY KEY,
            canteen_id    INTEGER,
            student_id    INTEGER,
            items         TEXT,
            items_count   INTEGER,
            price         DOUBLE PRECISION,
            expected_time INTEGER,
            status        TEXT,
            created_time  DOUBLE PRECISION,
            accepted_time DOUBLE PRECISION,
            ready_time    DOUBLE PRECISION
        )""")
    else:
        import sqlite3
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT,
            email          TEXT UNIQUE,
            password       TEXT,
            role           TEXT DEFAULT 'student',
            canteen_id     INTEGER,
            phone          TEXT,
            enrollment_no  TEXT,
            phone_verified INTEGER DEFAULT 0,
            registered_at  REAL DEFAULT 0,
            last_login     REAL DEFAULT 0
        )""")
        # Migrate existing tables safely
        for col, typ in [("registered_at","REAL DEFAULT 0"),("last_login","REAL DEFAULT 0"),
                         ("phone","TEXT"),("enrollment_no","TEXT"),("phone_verified","INTEGER DEFAULT 0")]:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
            except Exception:
                pass

        cur.execute("""
        CREATE TABLE IF NOT EXISTS canteens(
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            order_id      INTEGER PRIMARY KEY,
            canteen_id    INTEGER,
            student_id    INTEGER,
            items         TEXT,
            items_count   INTEGER,
            price         REAL,
            expected_time INTEGER,
            status        TEXT,
            created_time  REAL,
            accepted_time REAL,
            ready_time    REAL
        )""")

    conn.commit()
    conn.close()

init_db()

# ── Seed canteens ─────────────────────────────────────────────────────────────
def seed():
    conn, ph = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM canteens")
    row = cur.fetchone()
    count = row[0]
    if count == 0:
        for name in ["Maggi Hotspot", "Southern Stories", "SnapEats", "Infinity Kitchen"]:
            cur.execute(f"INSERT INTO canteens(name) VALUES ({ph})", (name,))
        conn.commit()
    conn.close()

seed()

# ── In-memory OTP store {email: {otp, expires, verified}} ───────────────────
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
otp_store = {}

SMTP_EMAIL    = os.environ.get("SMTP_EMAIL", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def send_email(to_addr, otp):
    msg            = MIMEMultipart("alternative")
    msg["Subject"] = f"🍽️ B.U Eats — Your Verification Code: {otp}"
    msg["From"]    = f"B.U Eats <{SMTP_EMAIL}>"
    msg["To"]      = to_addr

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0f0f1a;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <div style="font-size:48px;">&#x1F37D;&#xFE0F;</div>
        <h2 style="color:#ff9f4a;margin:8px 0;font-size:22px;">B.U Eats Verification</h2>
        <p style="color:#9998aa;font-size:13px;">Use the code below to verify your email</p>
      </div>
      <div style="background:#1e1d2e;border-radius:12px;padding:24px;text-align:center;margin:20px 0;">
        <div style="font-size:42px;font-weight:900;letter-spacing:10px;color:#ffe393;font-family:monospace;">{otp}</div>
        <p style="color:#9998aa;font-size:12px;margin-top:8px;">Valid for <b style="color:#ff9f4a;">10 minutes</b>. Do not share with anyone.</p>
      </div>
      <p style="color:#9998aa;font-size:11px;text-align:center;">If you didn't request this, ignore this email.</p>
    </div>"""

    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP("smtp-mail.outlook.com", 587) as s:
        s.starttls()
        s.login(SMTP_EMAIL, SMTP_PASSWORD)
        s.sendmail(SMTP_EMAIL, to_addr, msg.as_string())

@app.route("/send-otp", methods=["POST"])
def send_otp():
    email = (request.json.get("email") or "").strip().lower()
    if not email.endswith("@bennett.edu.in"):
        return jsonify({"error": "Only @bennett.edu.in emails are accepted."}), 400

    # --- CALL C++ FOR OTP GENERATION ---
    res = call_canteen_tool(["--generate-otp"])
    if not res or res.returncode != 0:
        return jsonify({"error": "Failed to generate OTP in C++."}), 500
    
    otp = res.stdout.strip()
    otp_store[email] = {"otp": otp, "expires": time.time() + 600, "verified": False}

    dev_mode = not bool(SMTP_EMAIL and SMTP_PASSWORD)

    if not dev_mode:
        try:
            send_email(email, otp)
        except Exception as e:
            return jsonify({"error": f"Email send failed: {str(e)}"}), 500
        return jsonify({"msg": f"OTP sent to {email}", "dev_mode": False})

    # Dev mode — no SMTP configured, return OTP in response
    return jsonify({"msg": "DEV MODE: OTP generated via C++ (no SMTP configured)",
                    "dev_mode": True, "otp": otp})

# ── VERIFY OTP ────────────────────────────────────────────────────────────────
@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    email = (request.json.get("email") or "").strip().lower()
    otp   = (request.json.get("otp")   or "").strip()

    record = otp_store.get(email)
    if not record:
        return jsonify({"error": "No OTP found for this email. Request a new one."}), 400
    if time.time() > record["expires"]:
        otp_store.pop(email, None)
        return jsonify({"error": "OTP expired. Request a new one."}), 400
    if record["otp"] != otp:
        return jsonify({"error": "Wrong OTP. Try again."}), 400

    otp_store[email]["verified"] = True
    return jsonify({"msg": "Email verified!"})

# ── AUTHENTICATION BRIDGE (C++) ──────────────────────────────────────────────
# We use the C++ 'auth_tool' for core logic to satisfy performance and logic requirements.

def call_canteen_tool(args):
    """Helper to call our C++ canteen utility with Render-safe path resolution."""
    try:
        # Path resolution that works both locally and on Render Linux
        base_dir = os.path.dirname(os.path.dirname(__file__))
        binary = os.path.join(base_dir, "backend", "bin", "canteen_tool")
        
        # Performance check
        if not os.path.exists(binary):
            print(f"CRITICAL: C++ Binary missing at {binary}")
            return None
            
        result = subprocess.run([binary] + args, capture_output=True, text=True)
        return result
    except Exception as e:
        print(f"C++ Canteen Tool Error: {e}")
        return None

@app.route("/password-reset/request", methods=["POST"])
def password_reset_request():
    """Step 1: Request reset - Logic powered by C++ generateOTP."""
    email = (request.json.get("email") or "").strip().lower()
    
    conn, ph = db_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE email = {ph}", (email,))
    user = cur.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "No account found with this email."}), 404

    # --- CALL C++ FOR OTP GENERATION ---
    res = call_canteen_tool(["--generate-otp"])
    if not res or res.returncode != 0:
        return jsonify({"error": "Failed to generate recovery code in C++."}), 500
    
    otp = res.stdout.strip()
    otp_store[email] = {"otp": otp, "expires": time.time() + 600, "verified": False}

    dev_mode = not bool(SMTP_EMAIL and SMTP_PASSWORD)

    if not dev_mode:
        try:
            msg            = MIMEMultipart("alternative")
            msg["Subject"] = f"🔐 B.U Eats — Password Reset Code: {otp}"
            msg["From"]    = f"B.U Eats <{SMTP_EMAIL}>"
            msg["To"]      = email
            
            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0f0f1a;border-radius:16px;">
              <div style="text-align:center;margin-bottom:24px;">
                <div style="font-size:48px;">&#x1F512;</div>
                <h2 style="color:#ff9f4a;margin:8px 0;font-size:22px;">Password Reset</h2>
                <p style="color:#9998aa;font-size:13px;">Use the code below to reset your password</p>
              </div>
              <div style="background:#1e1d2e;border-radius:12px;padding:24px;text-align:center;margin:20px 0;">
                <div style="font-size:42px;font-weight:900;letter-spacing:10px;color:#ffe393;font-family:monospace;">{otp}</div>
                <p style="color:#9998aa;font-size:12px;margin-top:8px;">Valid for <b style="color:#ff9f4a;">10 minutes</b>.</p>
              </div>
            </div>"""
            msg.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP("smtp-mail.outlook.com", 587) as s:
                s.starttls()
                s.login(SMTP_EMAIL, SMTP_PASSWORD)
                s.sendmail(SMTP_EMAIL, email, msg.as_string())
        except Exception as e:
            return jsonify({"error": f"Email send failed: {str(e)}"}), 500
        return jsonify({"msg": f"OTP sent to {email}", "dev_mode": False})

    return jsonify({"msg": "DEV MODE: Reset OTP generated via C++", "dev_mode": True, "otp": otp})

@app.route("/password-reset/confirm", methods=["POST"])
def password_reset_confirm():
    """Step 2: Confirm reset - Logic powered by C++ validatePassword."""
    email = (request.json.get("email") or "").strip().lower()
    otp   = (request.json.get("otp")   or "").strip()
    new_password = (request.json.get("password") or "").strip()

    # --- CALL C++ FOR PASSWORD VALIDATION ---
    res = call_canteen_tool(["--validate-password", new_password])
    if not res or res.returncode != 0:
        return jsonify({"error": "Password does not meet C++ security requirements (must be >= 6 chars and contain a digit)."}), 400

    record = otp_store.get(email)
    if not record:
        return jsonify({"error": "No OTP found. Request a new one."}), 400
    if time.time() > record["expires"]:
        otp_store.pop(email, None)
        return jsonify({"error": "OTP expired. Request a new one."}), 400
    
    # --- CALL C++ FOR OTP VERIFICATION ---
    res = call_canteen_tool(["--verify-otp", otp, record["otp"]])
    if not res or res.returncode != 0:
        return jsonify({"error": "Wrong OTP. Identity verification failed in C++."}), 400

    # Verification successful, update hashed password in database
    hashed = generate_password_hash(new_password)
    conn, ph = db_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"UPDATE users SET password = {ph} WHERE email = {ph}", (hashed, email))
        conn.commit()
        otp_store.pop(email, None)
        return jsonify({"msg": "Password reset successfully!"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

# ── Priority algorithm (C++ Powered) ──────────────────────────────────────────
def calc_priority(o):
    """Calls C++ to determine order priority based on wait time and load."""
    waiting = time.time() - o["created_time"]
    res = call_canteen_tool(["--calc-priority", str(waiting), str(o["expected_time"]), str(o["items_count"])])
    if res and res.returncode == 0:
        try: return float(res.stdout.strip())
        except: pass
    # Fallback to local python (should not happen if C++ is built)
    return (o["expected_time"] * 2) + (o["items_count"] * 3) - (waiting / 10)

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status":   "ok",
        "service":  "B.U Eats API",
        "db":       "postgres" if USE_POSTGRES else "sqlite",
        "version":  "2.0"
    })

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

# ── Domain restriction ────────────────────────────────────────────────────────
ALLOWED_DOMAIN = "@bennett.edu.in"

# ── REGISTER ──────────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    d     = request.json
    email = (d.get("email") or "").strip().lower()

    role       = d.get("role", "student")
    canteen_id = d.get("canteen_id", None)
    phone      = (d.get("phone") or "").strip()

    if role == "student" and not email.endswith(ALLOWED_DOMAIN):
        return jsonify({"error": f"Only {ALLOWED_DOMAIN} emails are allowed for students."}), 400

    # Validate email OTP for students
    if role == "student":
        otp_record = otp_store.get(email)
        if not otp_record or not otp_record.get("verified"):
            return jsonify({"error": "Email not verified. Please verify your @bennett.edu.in email first."}), 400

    # Extract enrollment number from email prefix
    enrollment_no = email.split("@")[0].upper() if role == "student" else None

    now    = time.time()
    hashed = generate_password_hash(d["password"])

    conn, ph = db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO users(name, email, password, role, canteen_id, phone, enrollment_no, phone_verified, registered_at) "
            f"VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})",
            (d["name"], email, hashed, role, canteen_id, phone if role=="student" else None,
             enrollment_no, 1 if role=="student" else 0, now)
        )
        conn.commit()
        conn.close()
        # Clear OTP after successful registration
        if role == "student":
            otp_store.pop(email, None)
        return jsonify({"msg": "registered"})

    except Exception as e:
        conn.rollback()
        conn.close()
        err = str(e)
        if "unique" in err.lower() or "duplicate" in err.lower():
            return jsonify({"error": "Email already registered"}), 400
        return jsonify({"error": err}), 500

# ── LOGIN ─────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    d     = request.json
    email = (d.get("email") or "").strip().lower()

    conn, ph = db_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE email = {ph}", (email,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({"msg": "Invalid email or password"}), 401

    u = row_to_dict(row, cur)

    if not check_password_hash(u["password"], d["password"]):
        conn.close()
        return jsonify({"msg": "Invalid email or password"}), 401

    # Record last login
    cur.execute(f"UPDATE users SET last_login = {ph} WHERE id = {ph}", (time.time(), u["id"]))
    conn.commit()
    conn.close()

    token = create_access_token(identity={
        "id":         u["id"],
        "role":       u["role"],
        "canteen_id": u["canteen_id"]
    })

    return jsonify({
        "access_token": token,
        "user": {
            "id":         u["id"],
            "name":       u["name"],
            "email":      email,
            "role":       u["role"],
            "canteen_id": u["canteen_id"]
        }
    })

# ── CREATE ORDER ──────────────────────────────────────────────────────────────
@app.route("/order/create", methods=["POST"])
@jwt_required()
def create_order():
    user = get_jwt_identity()
    if user["role"] != "student":
        return jsonify({"error": "Only students can place orders"}), 403

    d    = request.json
    conn, ph = db_conn()
    cur  = conn.cursor()

    oid         = int(time.time() * 1000)
    items       = d["items"]
    total_price = sum(i["price"] for i in items)
    total_time  = sum(i["time"]  for i in items)

    cur.execute(f"SELECT COUNT(*) FROM orders WHERE canteen_id = {ph} AND status IN ('WAITING', 'ACCEPTED', 'PREPARING')", (d["canteen_id"],))
    count_row = cur.fetchone()
    active_orders = count_row[0] if count_row else 0
    
    # --- CALL C++ FOR DYNAMIC ETA ---
    res = call_canteen_tool(["--calc-eta", str(total_time), str(active_orders)])
    if res and res.returncode == 0:
        expected_time = int(res.stdout.strip())
    else:
        # Fallback
        expected_time = total_time + (active_orders * 2)

    cur.execute(
        f"INSERT INTO orders VALUES ({ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph},{ph})",
        (oid, d["canteen_id"], user["id"],
         json.dumps(items), len(items),
         total_price, expected_time,
         "WAITING", time.time(), None, None)
    )
    conn.commit()
    conn.close()
    return jsonify({"order_id": oid})

# ── CANTEEN ORDERS ────────────────────────────────────────────────────────────
@app.route("/canteen/orders", methods=["GET"])
@jwt_required()
def canteen_orders():
    user = get_jwt_identity()
    if user["role"] != "canteen":
        return jsonify({"error": "Only canteen staff can view this"}), 403

    conn, ph = db_conn()
    cur  = conn.cursor()
    query = f"""
        SELECT o.*,
               u.name          AS student_name,
               u.enrollment_no AS enrollment_no,
               u.phone         AS student_phone
        FROM orders o
        LEFT JOIN users u ON o.student_id = u.id
        WHERE o.canteen_id = {ph}
    """
    cur.execute(query, (user["canteen_id"],))
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        o = dict(zip([d[0] for d in cur.description], r))
        o["items"]    = json.loads(o["items"])
        o["priority"] = round(calc_priority(o), 2)
        result.append(o)

    result.sort(key=lambda x: x["priority"])
    for i, o in enumerate(result):
        o["queue_position"] = i + 1

    return jsonify(result)

# ── CANTEEN ANALYTICS ─────────────────────────────────────────────────────────
@app.route("/canteen/analytics", methods=["GET"])
@jwt_required()
def canteen_analytics():
    user = get_jwt_identity()
    if user["role"] != "canteen":
        return jsonify({"error": "Only canteen staff"}), 403

    conn, ph = db_conn()
    cur  = conn.cursor()
    # Active orders
    cur.execute(f"SELECT COUNT(*) FROM orders WHERE canteen_id = {ph} AND status IN ('WAITING', 'ACCEPTED', 'PREPARING')", (user["canteen_id"],))
    active_count = cur.fetchone()[0]

    # Today's completed orders & revenue (past 24h)
    day_ago = time.time() - (24 * 3600)
    cur.execute(f"SELECT COUNT(*), SUM(price) FROM orders WHERE canteen_id = {ph} AND status = 'COMPLETED' AND created_time >= {ph}", (user["canteen_id"], day_ago))
    row = cur.fetchone()
    completed_count = row[0] if row and row[0] else 0
    revenue = row[1] if row and row[1] else 0

    conn.close()

    return jsonify({
        "active_orders": active_count,
        "total_orders": completed_count,
        "revenue": revenue
    })

# ── CANTEENS STATUS ───────────────────────────────────────────────────────────
@app.route("/canteens/status", methods=["GET"])
def canteens_status():
    conn, ph = db_conn()
    cur  = conn.cursor()
    cur.execute("SELECT canteen_id, COUNT(*) FROM orders WHERE status IN ('WAITING', 'ACCEPTED', 'PREPARING') GROUP BY canteen_id")
    rows = cur.fetchall()
    conn.close()

    # Default to 0 for the 4 seeded canteens
    result = {1: 0, 2: 0, 3: 0, 4: 0} 
    for r in rows:
        result[r[0]] = r[1]
    
    return jsonify(result)

# ── ORDER STATUS ──────────────────────────────────────────────────────────────
@app.route("/order/status/<int:oid>", methods=["GET"])
@jwt_required()
def order_status(oid):
    conn, ph = db_conn()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM orders WHERE order_id = {ph}", (oid,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Order not found"}), 404

    r = row_to_dict(row, cur)
    return jsonify({
        "status":        r["status"],
        "items":         json.loads(r["items"]),
        "price":         r["price"],
        "expected_time": r["expected_time"]
    })

# ── STUDENT HISTORY ───────────────────────────────────────────────────────────
@app.route("/student/history", methods=["GET"])
@jwt_required()
def student_history():
    user = get_jwt_identity()
    if user["role"] != "student":
        return jsonify({"error": "Only students can view their history"}), 403

    conn, ph = db_conn()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM orders WHERE student_id = {ph} ORDER BY created_time DESC LIMIT 10", (user["id"],))
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        o = row_to_dict(r, cur)
        o["items"] = json.loads(o["items"])
        result.append(o)

    return jsonify(result)

# ── STATE MACHINE (C++ Powered) ───────────────────────────────────────────────
def set_status(oid, next_status):
    conn, ph = db_conn()
    cur  = conn.cursor()
    cur.execute(f"SELECT status FROM orders WHERE order_id = {ph}", (oid,))
    row = cur.fetchone()
    if row:
        current = row[0] if USE_POSTGRES else row["status"]
        
        # --- CALL C++ FOR FLOW VALIDATION ---
        res = call_canteen_tool(["--validate-flow", current, next_status])
        if res and res.returncode == 0:
            cur.execute(f"UPDATE orders SET status = {ph} WHERE order_id = {ph}", (next_status, oid))
            conn.commit()
    conn.close()

@app.route("/order/accept",    methods=["POST"])
@jwt_required()
def accept():
    set_status(request.json["order_id"], "ACCEPTED");   return jsonify({"ok": 1})

@app.route("/order/preparing", methods=["POST"])
@jwt_required()
def preparing():
    set_status(request.json["order_id"], "PREPARING");  return jsonify({"ok": 1})

@app.route("/order/ready",     methods=["POST"])
@jwt_required()
def ready():
    set_status(request.json["order_id"], "READY");      return jsonify({"ok": 1})

@app.route("/order/complete",  methods=["POST"])
@jwt_required()
def complete():
    set_status(request.json["order_id"], "COMPLETED");  return jsonify({"ok": 1})

# ── Run locally ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)