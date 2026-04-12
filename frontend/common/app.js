// NOTE: This file expects config.js to be loaded first.
// All pages that use app.js MUST include:
//   <script src="../common/config.js"></script>
//   <script src="../common/app.js"></script>

// ── Auth helpers (ROLE-AWARE: works for both student & staff) ─────────────────
function authHeaders(role = "student") {
    const key = `${role}_token`;
    return {
        "Content-Type":  "application/json",
        "Authorization": "Bearer " + localStorage.getItem(key)
    };
}

function protectPage(requiredRole = "student", redirectUrl = "../student/login.html") {
    const key_token = `${requiredRole}_token`;
    const key_user  = `${requiredRole}_user`;
    
    const token = localStorage.getItem(key_token);
    const user  = JSON.parse(localStorage.getItem(key_user) || "null");

    if (!token || token === "undefined") {
        window.location.href = redirectUrl;
        return;
    }
    if (!user || !user.role) {
        localStorage.removeItem(key_token);
        localStorage.removeItem(key_user);
        window.location.href = redirectUrl;
        return;
    }
    if (requiredRole && user.role !== requiredRole) {
        alert("Unauthorized access");
        localStorage.removeItem(key_token);
        localStorage.removeItem(key_user);
        window.location.href = redirectUrl;
        return;
    }
}

function logout(role = "student", redirectUrl = "../student/login.html") {
    const key_token = `${role}_token`;
    const key_user  = `${role}_user`;
    const key_order = `${role}_order`;
    
    localStorage.removeItem(key_token);
    localStorage.removeItem(key_user);
    localStorage.removeItem(key_order);
    window.location = redirectUrl;
}

// Helper to get current user (role-aware)
function getCurrentUser(role = "student") {
    const key_user = `${role}_user`;
    return JSON.parse(localStorage.getItem(key_user) || "null");
}

// Helper to get current token (role-aware)
function getCurrentToken(role = "student") {
    const key_token = `${role}_token`;
    return localStorage.getItem(key_token);
}

// ── Cart ──────────────────────────────────────────────────────────────────────
let cart = [];

function addToCart(name, price, time) {
    cart.push({ name, price, time });
    renderCart();
    showToast(`✅ ${name} added to cart!`);
}

function removeItem(i) {
    const removed = cart.splice(i, 1)[0];
    renderCart();
    showToast(`🗑️ ${removed.name} removed`);
}

function renderCart() {
    let total = 0;
    let html  = "";

    cart.forEach((item, idx) => {
        total += item.price;
        html  += `
        <div class="cart-item" style="display:flex;align-items:center;justify-content:space-between;
             padding:12px 16px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);
             border-radius:12px;margin-bottom:10px;">
          <div>
            <span style="font-weight:600;">${item.name}</span>
            <span style="color:rgba(240,240,255,0.5);font-size:12px;margin-left:8px;">⏱ ${item.time} min</span>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-weight:700;color:#ffd60a;">₹${item.price}</span>
            <button onclick="removeItem(${idx})" style="
              background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);
              color:#fca5a5;border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px;
              transition:all 0.2s;">✕</button>
          </div>
        </div>`;
    });

    const cartEl = document.getElementById("cart");
    const totalEl = document.getElementById("cart-total");
    const countEl = document.getElementById("cart-count");

    if (cartEl)  cartEl.innerHTML  = html || `<p style="color:rgba(255,255,255,0.3);text-align:center;padding:20px;">Your cart is empty</p>`;
    if (totalEl) totalEl.textContent = `₹${total}`;
    if (countEl) countEl.textContent = cart.length;
}

// ── Checkout ──────────────────────────────────────────────────────────────────
function checkout() {
    if (cart.length === 0) {
        showToast("⚠️ Cart is empty!", "error");
        return;
    }

    const params   = new URLSearchParams(window.location.search);
    const canteenId = parseInt(params.get("canteen")) || 1;
    const btn       = document.getElementById("checkoutBtn");

    if (btn) { btn.disabled = true; btn.textContent = "Placing order..."; }

    fetch(API + "/order/create", {
        method:  "POST",
        headers: authHeaders("student"),
        body:    JSON.stringify({ canteen_id: canteenId, items: cart })
    })
    .then(r => {
        if (r.status === 401 || r.status === 422) {
            window.location = "login.html";
            return null;
        }
        return r.json();
    })
    .then(d => {
        if (!d) return;
        if (d.error || d.msg) {
            showToast("❌ " + (d.error || d.msg), "error");
            if (btn) { btn.disabled = false; btn.textContent = "Place Order"; }
            return;
        }
        if (!d.order_id) {
            showToast("❌ Failed to create order", "error");
            if (btn) { btn.disabled = false; btn.textContent = "Place Order"; }
            return;
        }
        localStorage.setItem("student_order", d.order_id);
        window.location = "order_status.html";
    })
    .catch(() => {
        showToast("❌ Could not connect to server.", "error");
        if (btn) { btn.disabled = false; btn.textContent = "Place Order"; }
    });
}

// ── Toast notifications ───────────────────────────────────────────────────────
function showToast(msg, type = "success") {
    const existing = document.getElementById("bu-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = "bu-toast";
    const bg = type === "error" ? "rgba(239,68,68,0.9)" : "rgba(16,185,129,0.9)";
    toast.style.cssText = `
      position:fixed;bottom:28px;right:28px;z-index:9999;
      padding:14px 22px;background:${bg};color:white;
      border-radius:14px;font-family:Poppins,sans-serif;font-size:14px;font-weight:600;
      box-shadow:0 8px 32px rgba(0,0,0,0.4);
      animation:toastIn 0.4s cubic-bezier(0.34,1.56,0.64,1);
      backdrop-filter:blur(10px);max-width:320px;`;
    toast.textContent = msg;

    const style = document.createElement("style");
    style.textContent = `@keyframes toastIn{from{opacity:0;transform:translateY(20px) scale(0.9)}to{opacity:1;transform:translateY(0) scale(1)}}`;
    document.head.appendChild(style);
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ── Session keepalive check ───────────────────────────────────────────────────
setInterval(() => {
    const token = localStorage.getItem("token");
    if (!token && window.location.pathname.includes("menu.html")) {
        window.location = "../student/login.html";
    }
}, 15000);