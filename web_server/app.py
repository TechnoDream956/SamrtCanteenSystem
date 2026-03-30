from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, time, json, os

app = Flask(__name__)
CORS(app)

# ---------------- SECURITY ----------------
app.config["JWT_SECRET_KEY"] = "CHANGE_THIS_SECRET_IN_PROD"
jwt = JWTManager(app)

# ---------------- DB PATH ----------------
DB_PATH = os.path.join(os.path.dirname(__file__), "canteen.db")
print("DB PATH:", DB_PATH)

# ---------------- DB CONNECT ----------------
def db_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# ---------------- INIT DB (FIXED) ----------------
def init_db():
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        canteen_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS canteens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        order_id INTEGER PRIMARY KEY,
        canteen_id INTEGER,
        student_id INTEGER,
        items TEXT,
        items_count INTEGER,
        price REAL,
        expected_time INTEGER,
        status TEXT,
        created_time REAL,
        accepted_time REAL,
        ready_time REAL
    )
    """)

    conn.commit()
    conn.close()

# ---------------- CALL INIT ----------------
init_db()

# ---------------- SEED ----------------
def seed():
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM canteens")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO canteens(name) VALUES(?)", [
            ("Maggi Hotspot",),
            ("Southern Stories",),
            ("SnapEats",),
            ("Infinity Kitchen",)
        ])
        conn.commit()

    conn.close()

seed()

# ---------------- PRIORITY ----------------
def calc_priority(o):
    waiting = time.time() - o["created_time"]
    return (o["expected_time"]*2) + (o["items_count"]*3) - (waiting/10)

# ---------------- REGISTER ----------------
import sqlite3

@app.route("/register", methods=["POST"])
def register():
    d = request.json
    conn = db_conn()
    cur = conn.cursor()

    try:
        hashed = generate_password_hash(d["password"])

        cur.execute("""
        INSERT INTO users(name,email,password,role,canteen_id)
        VALUES(?,?,?,?,?)
        """,(d["name"], d["email"], hashed, d["role"], d.get("canteen_id")))

        conn.commit()
        conn.close()

        return jsonify({"msg":"registered"})

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error":"user already exists"}), 400

    except Exception as e:
        conn.close()
        print("REGISTER ERROR:", e)   # 👈 IMPORTANT DEBUG
        return jsonify({"error": str(e)}), 500

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    d = request.json
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=?", (d["email"],))
    u = cur.fetchone()

    conn.close()

    if not u or not check_password_hash(u[3], d["password"]):
        return jsonify({"error":"invalid credentials"}), 401

    token = create_access_token(identity={
        "id": u[0],
        "role": u[4],
        "canteen_id": u[5]
    })

    return jsonify({
        "token": token,
        "id": u[0],
        "name": u[1],
        "role": u[4],
        "canteen_id": u[5]
    })

# ---------------- CREATE ORDER ----------------
@app.route("/order/create", methods=["POST"])
@jwt_required()
def create_order():
    user = get_jwt_identity()
    if user["role"] != "student":
        return jsonify({"error":"only students"}), 403

    d = request.json
    conn = db_conn()
    cur = conn.cursor()

    oid = int(time.time()*1000)
    items = d["items"]

    total_price = sum(i["price"] for i in items)
    total_time  = sum(i["time"] for i in items)

    cur.execute("""
    INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """,(oid, d["canteen_id"], user["id"],
         json.dumps(items), len(items),
         total_price, total_time,
         "WAITING", time.time(), None, None))

    conn.commit()
    conn.close()

    return jsonify({"order_id": oid})

# ---------------- CANTEEN ORDERS ----------------
@app.route("/canteen/orders", methods=["GET"])
@jwt_required()
def canteen_orders():
    user = get_jwt_identity()
    if user["role"] != "canteen":
        return jsonify({"error":"only canteen"}), 403

    conn = db_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM orders WHERE canteen_id=?", (user["canteen_id"],))
    rows = cur.fetchall()
    conn.close()

    result = []

    for r in rows:
        o = {
            "order_id": r[0],
            "canteen_id": r[1],
            "student_id": r[2],
            "items": json.loads(r[3]),
            "items_count": r[4],
            "price": r[5],
            "expected_time": r[6],
            "status": r[7],
            "created_time": r[8]
        }
        o["priority"] = round(calc_priority(o), 2)
        result.append(o)

    result.sort(key=lambda x: x["priority"])

    for i,o in enumerate(result):
        o["queue_position"] = i+1

    return jsonify(result)

# ---------------- STATUS ----------------
@app.route("/order/status/<int:oid>")
@jwt_required()
def order_status(oid):
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM orders WHERE order_id=?", (oid,))
    r = cur.fetchone()

    conn.close()

    if not r:
        return jsonify({})

    return jsonify({
        "status": r[7],
        "items": json.loads(r[3]),
        "price": r[5],
        "expected_time": r[6]
    })

# ---------------- STATE MACHINE ----------------
def allowed(cur, nxt):
    flow = {
        "WAITING":["ACCEPTED"],
        "ACCEPTED":["PREPARING"],
        "PREPARING":["READY"],
        "READY":["COMPLETED"],
        "COMPLETED":[]
    }
    return nxt in flow.get(cur,[])

def set_status(oid, nxt):
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("SELECT status FROM orders WHERE order_id=?", (oid,))
    r = cur.fetchone()

    if not r:
        conn.close()
        return False

    if allowed(r[0], nxt):
        cur.execute("UPDATE orders SET status=? WHERE order_id=?", (nxt, oid))
        conn.commit()

    conn.close()
    return True

@app.route("/order/accept", methods=["POST"])
@jwt_required()
def accept():
    set_status(request.json["order_id"], "ACCEPTED")
    return jsonify({"ok":1})

@app.route("/order/preparing", methods=["POST"])
@jwt_required()
def preparing():
    set_status(request.json["order_id"], "PREPARING")
    return jsonify({"ok":1})

@app.route("/order/ready", methods=["POST"])
@jwt_required()
def ready():
    set_status(request.json["order_id"], "READY")
    return jsonify({"ok":1})

@app.route("/order/complete", methods=["POST"])
@jwt_required()
def complete():
    set_status(request.json["order_id"], "COMPLETED")
    return jsonify({"ok":1})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)