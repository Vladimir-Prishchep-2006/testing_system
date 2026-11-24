// Общие функции для всех страниц: запросы к API, сообщения, форматирование.

// Экранирование: всё, что пришло с сервера, вставляется в HTML только через esc()
const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// 1490 -> «1 490 ₸», 0 -> «Бесплатно»
const money = (n) => (n === 0 ? "Бесплатно" : n.toLocaleString("ru-RU") + " ₸");

// Обёртка над fetch: превращает ошибки API в исключения с понятным текстом
async function api(path, options = {}) {
  const res = await fetch("/api" + path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(errorText(data, res.status));
  return data;
}

// 422 приходит списком ошибок Pydantic, остальные ошибки — строкой в detail
function errorText(data, status) {
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => e.loc.slice(1).join(".") + ": " + e.msg).join("; ");
  }
  return data.detail || "Ошибка " + status;
}

function notify(text, ok = false) {
  const el = document.getElementById("msg");
  el.textContent = text;
  el.className = (ok ? "ok" : "err") + " show";
  setTimeout(() => el.classList.remove("show"), 4000);
}