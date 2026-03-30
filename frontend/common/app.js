// ══════════════════════════════════════════════════
// API URL — Change this after deploying to Render!
// Local:   http://127.0.0.1:5001
// Render:  https://your-app-name.onrender.com
// ══════════════════════════════════════════════════
const API = "http://127.0.0.1:5001"

// ─── HELPERS ───
function authHeaders(){
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + localStorage.getItem("token")
    }
}

// ─── CART ───
let cart = []

function addToCart(name, price, time){
    cart.push({ name, price, time })
    renderCart()
    // Flash the cart panel
    const panel = document.querySelector(".cart-panel")
    if(panel){ panel.style.borderColor = "var(--accent)"; setTimeout(()=>panel.style.borderColor="",600) }
}

function removeItem(i){
    cart.splice(i, 1)
    renderCart()
}

function renderCart(){
    const el = document.getElementById("cart")
    if(!el) return

    const countEl = document.querySelector(".cart-count")

    if(cart.length === 0){
        el.innerHTML = `<div class="cart-empty">🛒<br>Your cart is empty<br><span style="font-size:12px">Add items from the menu</span></div>`
        if(countEl) countEl.textContent = "0"
        return
    }

    let total = 0
    let html = ""

    cart.forEach((item, idx) => {
        total += item.price
        html += `
        <div class="cart-item">
            <span class="cart-item-name">${item.name}</span>
            <span class="cart-item-price">₹${item.price}</span>
            <button class="btn-xs btn-danger" onclick="removeItem(${idx})" title="Remove">✕</button>
        </div>`
    })

    el.innerHTML = html
    if(countEl) countEl.textContent = cart.length

    const totalEl = document.getElementById("cart-total")
    if(totalEl) totalEl.textContent = "₹" + total
}

// ─── CHECKOUT ───
function checkout(){
    if(cart.length === 0){ alert("Your cart is empty!"); return }

    const user = JSON.parse(localStorage.getItem("user"))
    const params = new URLSearchParams(window.location.search)
    const canteen = params.get("canteen")
    const btn = document.getElementById("checkoutBtn")

    if(btn){ btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Placing order...' }

    fetch(API + "/order/create", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ canteen_id: canteen, student_id: user.id, items: cart })
    })
    .then(r => r.json())
    .then(d => {
        localStorage.setItem("order", d.order_id)
        window.location = "order_status.html"
    })
    .catch(() => {
        alert("Failed to place order. Please try again.")
        if(btn){ btn.disabled = false; btn.innerHTML = "🛒 Place Order" }
    })
}

// ─── STATUS TRACKER ───
const STATUS_STEPS = ["WAITING","ACCEPTED","PREPARING","READY","COMPLETED"]
const STATUS_ICONS  = ["⏳","✅","👨‍🍳","🔔","🎉"]
const STATUS_LABELS = ["Waiting","Accepted","Preparing","Ready","Done"]

function updateTracker(status){
    const idx = STATUS_STEPS.indexOf(status)
    STATUS_STEPS.forEach((s, i) => {
        const dot = document.getElementById("dot-" + i)
        const step = document.getElementById("step-" + i)
        if(!dot || !step) return
        dot.classList.remove("done","active")
        step.classList.remove("done","active")
        if(i < idx){ dot.classList.add("done"); step.classList.add("done"); dot.innerHTML = "✓" }
        else if(i === idx){ dot.classList.add("active"); step.classList.add("active"); dot.innerHTML = STATUS_ICONS[i] }
        else { dot.innerHTML = STATUS_ICONS[i] }
    })
}

// ─── STUDENT POLLING ───
function pollStudent(){
    let id = localStorage.getItem("order")
    if(!id) return

    function fetchStatus(){
        fetch(API + "/order/status/" + id, { headers: authHeaders() })
        .then(r => r.json())
        .then(o => {
            if(!o.status) return
            const statusEl = document.getElementById("status-text")
            if(statusEl){ statusEl.textContent = o.status; statusEl.className = "status " + o.status }
            const priceEl = document.getElementById("price")
            if(priceEl) priceEl.textContent = "₹" + o.price
            const expectedEl = document.getElementById("expected")
            if(expectedEl) expectedEl.textContent = o.expected_time + " min"
            let itemsHTML = ""
            if(o.items) o.items.forEach(i => { itemsHTML += `<li>• ${i.name} <span class="text-muted" style="font-size:12px">₹${i.price}</span></li>` })
            const itemsEl = document.getElementById("items")
            if(itemsEl) itemsEl.innerHTML = itemsHTML
            updateTracker(o.status)
        })
    }
    fetchStatus()
    setInterval(fetchStatus, 2500)
}

// ─── CANTEEN ORDERS ───
function loadOrders(){
    let waiting=0, preparing=0, ready=0

    function fetchOrders(){
        fetch(API + "/canteen/orders", { headers: authHeaders() })
        .then(r => r.json())
        .then(data => {
            waiting = data.filter(o=>o.status==="WAITING").length
            preparing = data.filter(o=>o.status==="PREPARING"||o.status==="ACCEPTED").length
            ready = data.filter(o=>o.status==="READY").length

            const wEl = document.getElementById("stat-waiting")
            const pEl = document.getElementById("stat-preparing")
            const rEl = document.getElementById("stat-ready")
            if(wEl) wEl.textContent = waiting
            if(pEl) pEl.textContent = preparing
            if(rEl) rEl.textContent = ready

            let html = ""
            if(data.length === 0){ html = `<div style="text-align:center;padding:60px;color:var(--text-dim)">🎉 No active orders right now</div>`}

            data.forEach(o => {
                const isUrgent = o.queue_position === 1
                const itemsList = o.items.map(i => `<li>${i.name}</li>`).join("")
                html += `
                <div class="order-card ${isUrgent ? 'urgent' : ''}">
                    <div class="order-header">
                        <div>
                            <div class="order-id">#${o.order_id}</div>
                            <div class="order-meta">
                                <span class="badge badge-pos">Queue #${o.queue_position}</span>
                                <span class="status ${o.status}">${o.status}</span>
                            </div>
                        </div>
                        <div style="text-align:right;font-size:13px;color:var(--text-muted)">
                            <div>Priority <strong style="color:var(--accent)">${o.priority}</strong></div>
                            <div>ETA ${o.expected_time} min</div>
                        </div>
                    </div>
                    <ul class="order-items">${itemsList}</ul>
                    <div style="font-size:14px;font-weight:700;color:var(--accent)">Total: ₹${o.price}</div>
                    <div class="order-actions">
                        <button class="btn-sm btn-success" onclick="update(${o.order_id},'accept')">✅ Accept</button>
                        <button class="btn-sm btn-purple" onclick="update(${o.order_id},'preparing')">👨‍🍳 Preparing</button>
                        <button class="btn-sm btn-info"   onclick="update(${o.order_id},'ready')">🔔 Ready</button>
                        <button class="btn-sm btn-ghost"  onclick="update(${o.order_id},'complete')">Done</button>
                    </div>
                </div>`
            })
            const ordersEl = document.getElementById("orders")
            if(ordersEl) ordersEl.innerHTML = html
        })
    }
    fetchOrders()
    setInterval(fetchOrders, 2500)
}

// ─── UPDATE ORDER STATUS ───
function update(id, type){
    const urls = { accept:"/order/accept", preparing:"/order/preparing", ready:"/order/ready", complete:"/order/complete" }
    fetch(API + urls[type], {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ order_id: id })
    })
}

// ─── ROUTE PROTECTION ───
function protectPage(requiredRole){
    const token = localStorage.getItem("token")
    const user = JSON.parse(localStorage.getItem("user") || "null")
    if(!token || token === "undefined"){
        window.location.href = "../student/login.html"; return
    }
    if(!user || !user.role){
        localStorage.clear(); window.location.href = "../student/login.html"; return
    }
    if(requiredRole && user.role !== requiredRole){
        alert("Unauthorized access")
        localStorage.clear(); window.location.href = "../student/login.html"; return
    }
}

// ─── LOGOUT ───
function logout(){
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    localStorage.removeItem("order")
    window.location = "../student/login.html"
}