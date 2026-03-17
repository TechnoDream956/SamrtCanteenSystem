from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

orders = {}

canteens = {
1:"Maggi Hotspot",
2:"Southern Stories",
3:"SnapEats",
4:"Infinity Kitchen"
}

@app.route("/")
def home():
    return "Smart Canteen API Running"

@app.route("/order/create",methods=["POST"])
def create_order():

    data=request.json

    oid=int(time.time()*1000)

    orders[oid]={

        "order_id":oid,

        "canteen_id":int(data["canteen_id"]),   # IMPORTANT FIX

        "item":data["item"],

        "price":data["price"],

        "expected_time":data["expected_time"],

        "status":"WAITING",

        "accepted_time":None,

        "ready_time":None

    }

    return jsonify({"order_id":oid})

@app.route("/canteen/orders/<int:canteen_id>")
def get_orders(canteen_id):

    result=[]

    for o in orders.values():

        if int(o["canteen_id"]) == int(canteen_id):

            result.append(o)

    return jsonify(result)

@app.route("/order/status/<int:order_id>")
def order_status(order_id):

    if order_id not in orders:
        return jsonify({"error":"not found"})

    return jsonify(orders[order_id])

@app.route("/order/accept",methods=["POST"])
def accept():

    oid=request.json["order_id"]
    o=orders[oid]

    if o["status"]=="WAITING":
        o["status"]="ACCEPTED"
        o["accepted_time"]=time.time()

    return jsonify({"status":o["status"]})

@app.route("/order/preparing",methods=["POST"])
def preparing():

    oid=request.json["order_id"]
    o=orders[oid]

    if o["status"]=="ACCEPTED":
        o["status"]="PREPARING"

    return jsonify({"status":o["status"]})

@app.route("/order/ready",methods=["POST"])
def ready():

    oid=request.json["order_id"]
    o=orders[oid]

    if o["status"]=="PREPARING":
        o["status"]="READY"
        o["ready_time"]=time.time()

    return jsonify({"status":o["status"]})

@app.route("/order/complete",methods=["POST"])
def complete():

    oid=request.json["order_id"]
    o=orders[oid]

    if o["status"]=="READY":
        o["status"]="COMPLETED"

    return jsonify(o)

app.run(port=5000)