const API_BASE = "http://127.0.0.1:5000";

// DEMO order id (real system me auto generate hoga)
let CURRENT_ORDER_ID = 101;

// STUDENT SIDE
function placeOrder(itemName, price, expectedTime) {
    fetch(API_BASE + "/order/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            order_id: CURRENT_ORDER_ID,
            expected_time: expectedTime,
            price: price
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log(data);
        alert("Order placed successfully");
        window.location.href = "order_status.html";
    });
}

// CANTEEN SIDE
function acceptOrder() {
    fetch(API_BASE + "/order/accept", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            order_id: CURRENT_ORDER_ID
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Order accepted");
        console.log(data);
    });
}

function markReady() {
    fetch(API_BASE + "/order/ready", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            order_id: CURRENT_ORDER_ID
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Order marked ready");
        console.log(data);
    });
}

function completeOrder() {
    fetch(API_BASE + "/order/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            order_id: CURRENT_ORDER_ID
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(
            "Delay: " + data.delay + " min\nFinal Price: ₹" + data.final_price
        );
    });
}
