from flask import Flask, request, jsonify
import time

app = Flask(__name__)
orders = {}

@app.route("/")
def home():
    return "Campus Canteen System Running"

@app.route("/order/create", methods=["POST"])
def create_order():
    data = request.json
    orders[data["order_id"]] = {
        "status": "CREATED",
        "expected_time": data["expected_time"],
        "base_price": data["price"],
        "accepted_time": None,
        "ready_time": None
    }
    return jsonify({"msg": "Order Created"})

@app.route("/order/accept", methods=["POST"])
def accept():
    oid = request.json["order_id"]
    orders[oid]["status"] = "ACCEPTED"
    orders[oid]["accepted_time"] = time.time()
    return jsonify({"msg": "Order Accepted"})

@app.route("/order/ready", methods=["POST"])
def ready():
    oid = request.json["order_id"]
    orders[oid]["status"] = "READY"
    orders[oid]["ready_time"] = time.time()
    return jsonify({"msg": "Order Ready"})

@app.route("/order/complete", methods=["POST"])
def complete():
    oid = request.json["order_id"]
    o = orders[oid]
    actual = int((o["ready_time"] - o["accepted_time"]) / 60)
    delay = max(0, actual - o["expected_time"])
    discount = min(delay * 2, o["base_price"] // 2)
    final_price = o["base_price"] - discount
    return jsonify({
        "delay": delay,
        "final_price": final_price
    })

if __name__ == "__main__":
    app.run()
