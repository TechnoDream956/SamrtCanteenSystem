const API="http://127.0.0.1:5000"

let orderId=null

function getCanteen(){

const params=new URLSearchParams(window.location.search)
return params.get("canteen")

}

function orderItem(item,price,time){

let canteen=getCanteen()

fetch(API+"/order/create",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

canteen_id:canteen,
item:item,
price:price,
expected_time:time

})

})

.then(r=>r.json())
.then(d=>{

localStorage.setItem("order",d.order_id)

window.location="order_status.html"

})

}

function pollStudent(){

orderId=localStorage.getItem("order")

setInterval(()=>{

fetch(API+"/order/status/"+orderId)

.then(r=>r.json())

.then(o=>{

document.getElementById("status").innerText=o.status
document.getElementById("item").innerText=o.item
document.getElementById("price").innerText=o.price
document.getElementById("expected").innerText=o.expected_time

})

},2000)

}

function loadOrders(){

let canteen=getCanteen()

setInterval(()=>{

fetch(API+"/canteen/orders/"+canteen)

.then(r=>r.json())

.then(data=>{

let html=""

data.forEach(o=>{

html+=`
<div class="card">

<h3>Order ${o.order_id}</h3>

<p><b>Item:</b> ${o.item}</p>

<p><b>Status:</b> 
<span class="status ${o.status}">
${o.status}
</span>
</p>

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

function update(id,type){

let endpoint=""

if(type=="accept") endpoint="/order/accept"
if(type=="preparing") endpoint="/order/preparing"
if(type=="ready") endpoint="/order/ready"
if(type=="complete") endpoint="/order/complete"

fetch(API+endpoint,{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

order_id:id

})

})

}