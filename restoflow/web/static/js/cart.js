const CART_KEY = "restoflow_cart";
let cart = JSON.parse(localStorage.getItem(CART_KEY) || "[]");

if (/^\/order\/\d+/.test(window.location.pathname)) {
  cart = [];
  localStorage.removeItem(CART_KEY);
}

const itemsBox = document.getElementById("cart-items");
const totalBox = document.getElementById("cart-total");
const jsonBox = document.getElementById("items-json");
const checkoutBtn = document.getElementById("checkout-btn");
const orderType = document.getElementById("order-type");
const tableLabel = document.getElementById("table-label");
const addressLabel = document.getElementById("address-label");

function save() { localStorage.setItem(CART_KEY, JSON.stringify(cart)); }

function syncOrderType() {
  if (!orderType) return;
  if (tableLabel) tableLabel.hidden = orderType.value !== "dine_in";
  if (addressLabel) addressLabel.hidden = orderType.value !== "delivery";
}

function render() {
  if (!itemsBox) return;
  itemsBox.innerHTML = "";
  let total = 0;
  cart.forEach(item => {
    total += item.price * item.qty;
    const row = document.createElement("div");
    row.className = "cart-row";
    row.innerHTML = `<span>${item.name} × ${item.qty}
      <button type="button" data-plus="${item.id}">+</button>
      <button type="button" data-minus="${item.id}">−</button></span>
      <span>${item.price * item.qty} ₽
      <button type="button" data-remove="${item.id}">×</button></span>`;
    itemsBox.appendChild(row);
  });
  totalBox.textContent = total + " ₽";
  if (jsonBox) jsonBox.value = JSON.stringify(cart.map(i => ({ id: i.id, qty: i.qty })));
  if (checkoutBtn) checkoutBtn.disabled = cart.length === 0;
}

document.addEventListener("click", e => {
  const add = e.target.closest(".add-btn");
  if (add) {
    const id = Number(add.dataset.id);
    const found = cart.find(i => i.id === id);
    if (found) found.qty += 1;
    else cart.push({ id, name: add.dataset.name,
                     price: Number(add.dataset.price), qty: 1 });
    save(); render(); return;
  }
  const plus = e.target.closest("[data-plus]");
  if (plus) {
    const f = cart.find(i => i.id === Number(plus.dataset.plus));
    if (f) f.qty += 1; save(); render(); return;
  }
  const minus = e.target.closest("[data-minus]");
  if (minus) {
    const f = cart.find(i => i.id === Number(minus.dataset.minus));
    if (f) { f.qty -= 1; if (f.qty <= 0) cart = cart.filter(x => x.id !== f.id); }
    save(); render(); return;
  }
  const remove = e.target.closest("[data-remove]");
  if (remove) {
    cart = cart.filter(i => i.id !== Number(remove.dataset.remove));
    save(); render();
  }
});

if (orderType) orderType.addEventListener("change", syncOrderType);
syncOrderType();
render();