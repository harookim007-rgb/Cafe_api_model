const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

const won = (n) => n.toLocaleString("ko-KR") + "원";
const pct = (v) => (v == null ? "-" : Math.round(v * 100) + "%");

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: opts.body instanceof FormData ? {} : { "Content-Type": "application/json" },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg = data.detail || `요청 실패 (${res.status})`;
    if (Array.isArray(msg)) msg = "입력값을 다시 확인해 주세요";
    throw new Error(msg);
  }
  return data;
}

let toastTimer;
function toast(msg, isError = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.toggle("error", isError);
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 2600);
}

function sentimentBadge(r) {
  if (!r.sentiment) return '<span class="badge none">분석 안 됨</span>';
  const cls = r.sentiment === "긍정" ? "pos" : "neg";
  return `<span class="badge ${cls}">${r.sentiment} ${Math.round(r.sentiment_score * 100)}</span>`;
}

function reviewItem(r, { removable = false } = {}) {
  return `
    <li>
      <div class="review-meta"><b>${esc(r.menu_name)}</b> · ${esc(r.author)} · ${esc(r.created_at.slice(5, 16))}</div>
      <p class="review-content">${esc(r.content)}</p>
      <div class="review-side">
        <span class="stars-text">${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}</span>
        ${sentimentBadge(r)}
        ${removable ? `<button class="btn danger small" data-del-review="${r.id}">삭제</button>` : ""}
      </div>
    </li>`;
}

/* ---------- 서버 상태 ---------- */
let ready = {};

async function loadStatus() {
  try {
    const res = await fetch("/ready");
    ready = (await res.json()).checks || {};
  } catch {
    ready = {};
  }
  $$("#server-status li").forEach((li) => {
    const ok = ready[li.dataset.key];
    li.classList.toggle("on", ok === true);
    li.classList.toggle("off", ok === false);
  });
  $("#vision-offline").hidden = ready.triton !== false;
  $("#chat-offline").hidden = ready.vllm !== false;
}

/* ---------- 대시보드 ---------- */
async function loadHome() {
  const [s, reviews] = await Promise.all([api("/api/stats"), api("/api/reviews?limit=5")]);
  $("#stat-menus").textContent = s.menus;
  $("#stat-reviews").textContent = s.reviews;
  $("#stat-rating").textContent = s.avg_rating ?? "-";
  $("#stat-positive").textContent = pct(s.positive_ratio);
  $("#home-reviews").innerHTML = reviews.length
    ? reviews.map((r) => reviewItem(r)).join("")
    : '<li class="empty">아직 리뷰가 없어요.</li>';
}

$("#sentiment-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = $("#sentiment-text").value.trim();
  if (!text) return;
  try {
    const r = await api("/api/ai/sentiment", { method: "POST", body: JSON.stringify({ text }) });
    const box = $("#sentiment-result");
    box.hidden = false;
    box.innerHTML = `
      ${sentimentBadge({ sentiment: r.label, sentiment_score: r.score })}
      <div class="meter"><div class="meter-bar"><span style="width:${r.score * 100}%"></span></div>긍정 확률 ${pct(r.score)}</div>
      <span class="ms">${r.ms}ms</span>`;
  } catch (err) {
    toast(err.message, true);
  }
});

/* ---------- 메뉴 ---------- */
let menuCategory = "";
let menus = [];

async function loadMenus() {
  const q = menuCategory ? `?category=${encodeURIComponent(menuCategory)}` : "";
  menus = await api("/api/menus" + q);
  const rows = $("#menu-rows");
  if (!menus.length) {
    rows.innerHTML = '<tr><td colspan="7" class="empty">등록된 메뉴가 없어요.</td></tr>';
    return;
  }
  rows.innerHTML = menus
    .map((m) => {
      const meter =
        m.avg_sentiment == null
          ? '<span class="meter">리뷰 없음</span>'
          : `<div class="meter"><div class="meter-bar"><span style="width:${m.avg_sentiment * 100}%"></span></div>${pct(m.avg_sentiment)}</div>`;
      return `
      <tr class="${m.is_soldout ? "soldout" : ""}" data-id="${m.id}">
        <td><b>${esc(m.name)}</b></td>
        <td><span class="cat">${esc(m.category)}</span></td>
        <td class="num"><input class="price-input" type="number" min="100" step="100" value="${m.price}" aria-label="${esc(m.name)} 가격"></td>
        <td class="num">${m.review_count}${m.avg_rating ? ` · ★${m.avg_rating}` : ""}</td>
        <td>${meter}</td>
        <td><label class="switch" title="품절"><input type="checkbox" ${m.is_soldout ? "checked" : ""} aria-label="${esc(m.name)} 품절"><span></span></label></td>
        <td><button class="btn danger small" data-del-menu>삭제</button></td>
      </tr>`;
    })
    .join("");
}

$("#menu-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    name: $("#menu-name").value.trim(),
    price: Number($("#menu-price").value),
    category: $("#menu-category").value,
  };
  try {
    await api("/api/menus", { method: "POST", body: JSON.stringify(body) });
    toast(`${body.name} 추가됨`);
    $("#menu-name").value = "";
    loadMenus();
  } catch (err) {
    toast(err.message, true);
  }
});

$("#menu-filter").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  $$("#menu-filter .chip").forEach((c) => c.classList.toggle("active", c === chip));
  menuCategory = chip.dataset.cat;
  loadMenus();
});

$("#menu-rows").addEventListener("change", async (e) => {
  const tr = e.target.closest("tr");
  const id = tr?.dataset.id;
  if (!id) return;
  const patch = e.target.type === "checkbox" ? { is_soldout: e.target.checked } : { price: Number(e.target.value) };
  try {
    const m = await api(`/api/menus/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
    toast(e.target.type === "checkbox" ? `${m.name} ${m.is_soldout ? "품절 처리" : "판매 재개"}` : `${m.name} ${won(m.price)}로 변경`);
    tr.classList.toggle("soldout", m.is_soldout);
  } catch (err) {
    toast(err.message, true);
    loadMenus();
  }
});

// 삭제는 두 번 눌러야 실행 (실수 방지)
$("#menu-rows").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-del-menu]");
  if (!btn) return;
  if (!btn.dataset.armed) {
    btn.dataset.armed = "1";
    btn.textContent = "한 번 더";
    setTimeout(() => {
      delete btn.dataset.armed;
      btn.textContent = "삭제";
    }, 2500);
    return;
  }
  const id = btn.closest("tr").dataset.id;
  try {
    const m = await api(`/api/menus/${id}`, { method: "DELETE" });
    toast(`${m.name} 삭제됨`);
    loadMenus();
  } catch (err) {
    toast(err.message, true);
  }
});

/* ---------- 리뷰 ---------- */
let rating = 5;
let reviewFilter = "";

function renderStars() {
  $("#review-stars").innerHTML = [1, 2, 3, 4, 5]
    .map((n) => `<button type="button" role="radio" aria-checked="${n === rating}" aria-label="${n}점" data-n="${n}" class="${n <= rating ? "on" : ""}">★</button>`)
    .join("");
}

$("#review-stars").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  rating = Number(b.dataset.n);
  renderStars();
});

async function loadReviews() {
  const all = await api("/api/menus");
  const select = $("#review-menu");
  const prev = select.value;
  select.innerHTML = all.map((m) => `<option value="${m.id}">${esc(m.name)}</option>`).join("");
  if (prev) select.value = prev;

  const q = reviewFilter ? `&sentiment=${encodeURIComponent(reviewFilter)}` : "";
  const list = await api(`/api/reviews?limit=50${q}`);
  $("#review-list").innerHTML = list.length
    ? list.map((r) => reviewItem(r, { removable: true })).join("")
    : '<li class="empty">조건에 맞는 리뷰가 없어요.</li>';
}

$("#review-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    menu_id: Number($("#review-menu").value),
    author: $("#review-author").value.trim(),
    content: $("#review-content").value.trim(),
    rating,
  };
  try {
    const r = await api("/api/reviews", { method: "POST", body: JSON.stringify(body) });
    toast(r.sentiment ? `등록됨 · ${r.sentiment} 리뷰로 분류했어요` : "등록됨");
    $("#review-content").value = "";
    loadReviews();
  } catch (err) {
    toast(err.message, true);
  }
});

$("#review-filter").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (!chip) return;
  $$("#review-filter .chip").forEach((c) => c.classList.toggle("active", c === chip));
  reviewFilter = chip.dataset.s;
  loadReviews();
});

$("#review-list").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-del-review]");
  if (!btn) return;
  try {
    await api(`/api/reviews/${btn.dataset.delReview}`, { method: "DELETE" });
    loadReviews();
  } catch (err) {
    toast(err.message, true);
  }
});

/* ---------- 이미지 ---------- */
let imageFile = null;

function setImage(file) {
  if (!file) return;
  if (!/^image\/(jpeg|png|webp)$/.test(file.type)) {
    toast("jpg, png, webp 이미지만 올릴 수 있어요", true);
    return;
  }
  imageFile = file;
  const img = $("#image-preview");
  img.src = URL.createObjectURL(file);
  img.hidden = false;
  $("#dropzone-text").hidden = true;
  $("#btn-classify").disabled = false;
  $("#btn-describe").disabled = false;
}

$("#image-input").addEventListener("change", (e) => setImage(e.target.files[0]));
const dz = $("#dropzone");
dz.addEventListener("dragover", (e) => {
  e.preventDefault();
  dz.classList.add("drag");
});
dz.addEventListener("dragleave", () => dz.classList.remove("drag"));
dz.addEventListener("drop", (e) => {
  e.preventDefault();
  dz.classList.remove("drag");
  setImage(e.dataTransfer.files[0]);
});

async function runVision(path, button) {
  if (!imageFile) return;
  const fd = new FormData();
  fd.append("file", imageFile);
  const out = $("#vision-result");
  button.disabled = true;
  out.className = "empty";
  out.textContent = "분석 중...";
  try {
    const r = await api(path, { method: "POST", body: fd });
    out.className = "";
    if (r.labels) {
      out.innerHTML =
        r.labels
          .map((l) => `<div class="result-row"><div class="top"><span>${esc(l.label)}</span><span>${pct(l.score)}</span></div><div class="bar"><span style="width:${l.score * 100}%"></span></div></div>`)
          .join("") + `<p class="ms">${r.ms}ms</p>`;
    } else {
      out.innerHTML = `<div class="result-row"><div class="top"><b>${esc(r.label)}</b><span>${pct(r.score)}</span></div></div><div class="describe">${esc(r.description)}</div>`;
    }
  } catch (err) {
    out.className = "empty";
    out.textContent = err.message;
  } finally {
    button.disabled = false;
  }
}

$("#btn-classify").addEventListener("click", (e) => runVision("/api/ai/classify", e.currentTarget));
$("#btn-describe").addEventListener("click", (e) => runVision("/api/ai/describe", e.currentTarget));

/* ---------- 챗봇 ---------- */
let history = [];

function renderChat(pending = false) {
  const log = $("#chat-log");
  log.innerHTML =
    history.map((m) => `<div class="bubble ${m.role}">${esc(m.content)}</div>`).join("") +
    (pending ? '<div class="bubble assistant pending">답변을 만드는 중...</div>' : "");
  log.scrollTop = log.scrollHeight;
}

$("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#chat-text");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  history.push({ role: "user", content: text });
  renderChat(true);
  try {
    const messages = [{ role: "system", content: $("#chat-system").value }, ...history.slice(-20)];
    const r = await api("/api/ai/chat", { method: "POST", body: JSON.stringify({ messages }) });
    history.push({ role: "assistant", content: r.content });
  } catch (err) {
    history.pop();
    input.value = text;
    toast(err.message, true);
  }
  renderChat();
});

$("#chat-clear").addEventListener("click", () => {
  history = [];
  renderChat();
});

/* ---------- 라우팅 ---------- */
const loaders = { home: loadHome, menus: loadMenus, reviews: loadReviews, vision: () => {}, chat: () => {} };

function route() {
  const view = (location.hash || "#home").slice(1);
  const name = loaders[view] ? view : "home";
  $$(".view").forEach((v) => (v.hidden = v.id !== `view-${name}`));
  $$(".nav a").forEach((a) => a.classList.toggle("active", a.dataset.view === name));
  Promise.resolve(loaders[name]()).catch((err) => toast(err.message, true));
}

window.addEventListener("hashchange", route);
renderStars();
route();
loadStatus();
setInterval(loadStatus, 30000);
