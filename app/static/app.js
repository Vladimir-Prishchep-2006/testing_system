// Общие функции для всех страниц: запросы к API, сообщения, меню.

const token = () => localStorage.getItem("token");

// Экранирование: всё, что пришло с сервера, вставляется в HTML только через esc()
const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// 1490 -> «1 490 ₸», 0 -> «Бесплатно»
const money = (n) => (n === 0 ? "Бесплатно" : n.toLocaleString("ru-RU") + " ₸");

// Обёртка над fetch: добавляет JWT, превращает ошибки API в исключения с понятным текстом
async function api(path, { json, ...options } = {}) {
  const headers = {};
  if (token()) headers.Authorization = "Bearer " + token();
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(json);
  }
  const res = await fetch("/api" + path, { ...options, headers });

  if (res.status === 401 && path !== "/auth/login") {
    localStorage.removeItem("token");
    location.href = "/login";
    throw new Error("Требуется вход");
  }
  if (res.status === 204) return null;

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

function logout() {
  localStorage.removeItem("token");
  location.href = "/";
}

async function renderNav() {
  const box = document.getElementById("nav-links");
  if (!token()) {
    box.innerHTML = '<a href="/login">Войти</a>';
    return;
  }
  const me = await api("/auth/me");
  box.innerHTML = `<a href="#" onclick="logout()">Выйти (${esc(me.username)})</a>`;
}
renderNav();