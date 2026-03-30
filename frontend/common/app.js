const API = "http://127.0.0.1:5000"

// ---------------- HELPER ----------------
function authHeaders(){
    return {
        "Content-Type":"application/json",
        "Authorization":"Bearer " + localStorage.getItem("token")
    }
}

// ---------------- CART ----------------
let cart = []

function addToCart(name, price, time){
    cart.push({name, price, time})
    renderCart()
}

function removeItem(i){
    cart.splice(i,1)
    renderCart()
}

function renderCart(){
    let html=""
    let total=0

    cart.forEach((i,idx)=>{
        total+=i.price
        html+=`
        <div class="card">
            ${i.name} - ₹${i.price}
            <button onclick="removeItem(${idx})">Remove</button>
        </div>`
    })

    html+=`<h4>Total: ₹${total}</h4>`

    const el = document.getElementById("cart")
    if(el) el.innerHTML = html
}

// ---------------- CHECKOUT ----------------
function checkout(){

    let user = JSON.parse(localStorage.getItem("user"))
    let params = new URLSearchParams(window.location.search)
    let canteen = params.get("canteen")

    fetch(API+"/order/create",{
        method:"POST",
        headers: authHeaders(),
        body:JSON.stringify({
            canteen_id:canteen,
            student_id:user.id,
            items:cart
        })
    })
    .then(r=>r.json())
    .then(d=>{
        localStorage.setItem("order",d.order_id)
        window.location="order_status.html"
    })
}

// ---------------- STUDENT POLLING ----------------
function pollStudent(){

    let id = localStorage.getItem("order")

    setInterval(()=>{

        fetch(API+"/order/status/"+id,{
            headers: authHeaders()
        })
        .then(r=>r.json())
        .then(o=>{

            if(!o.status) return

            document.getElementById("status").innerText=o.status
            document.getElementById("price").innerText=o.price
            document.getElementById("expected").innerText=o.expected_time

            let itemsHTML=""
            o.items.forEach(i=>{
                itemsHTML+=`<p>• ${i.name}</p>`
            })

            document.getElementById("items").innerHTML=itemsHTML

        })

    },2000)
}

// ---------------- CANTEEN DASHBOARD ----------------
function loadOrders(){

    setInterval(()=>{

        fetch(API+"/canteen/orders",{
            headers: authHeaders()
        })
        .then(r=>r.json())
        .then(data=>{

            let html=""

            data.forEach(o=>{

                let highlight = o.queue_position === 1 ? "style='border:3px solid red'" : ""

                html+=`
                <div class="card" ${highlight}>

                <h3>Order ${o.order_id}</h3>

                <p><b>Status:</b> ${o.status}</p>
                <p><b>Priority:</b> ${o.priority}</p>
                <p><b>Queue:</b> ${o.queue_position}</p>

                <p><b>Items:</b></p>

                <ul>
                ${o.items.map(i=>`<li>${i.name}</li>`).join("")}
                </ul>

                <button onclick="update(${o.order_id},'accept')">Accept</button>
                <button onclick="update(${o.order_id},'preparing')">Preparing</button>
                <button onclick="update(${o.order_id},'ready')">Ready</button>
                <button onclick="update(${o.order_id},'complete')">Complete</button>

                </div>
                `
            })

            document.getElementById("orders").innerHTML=html

        })

    },2000)
}

// ---------------- UPDATE STATUS ----------------
function update(id,type){

    let url=""

    if(type=="accept") url="/order/accept"
    if(type=="preparing") url="/order/preparing"
    if(type=="ready") url="/order/ready"
    if(type=="complete") url="/order/complete"

    fetch(API+url,{
        method:"POST",
        headers: authHeaders(),
        body:JSON.stringify({order_id:id})
    })
}
function protectPage(requiredRole){

    const token = localStorage.getItem("token")
    const user = JSON.parse(localStorage.getItem("user"))

    // 🚫 NO LOGIN
    if(!token || token === "undefined" || token === null){
        window.location.href = "../student/login.html"
        return
    }

    // 🚫 INVALID USER DATA
    if(!user || !user.role){
        localStorage.clear()
        window.location.href = "../student/login.html"
        return
    }

    // 🚫 WRONG ROLE
    if(requiredRole && user.role !== requiredRole){
        alert("Unauthorized access")
        localStorage.clear()
        window.location.href = "../student/login.html"
        return
    }
}
function logout(){
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    localStorage.removeItem("order")

    window.location = "../student/login.html"
}
function checkSession(){

    const token = localStorage.getItem("token")

    if(!token){
        window.location = "../student/login.html"
        return
    }

    // optional: decode later if needed
}

setInterval(checkSession, 10000)