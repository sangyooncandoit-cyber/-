/* 결과 화면 동작.
   담당자가 "찾았다"에서 끝나지 않고 바로 조치할 수 있게 만드는 것이 목적이다.
   처리 상태는 브라우저에 저장해 창을 닫았다 열어도 남는다. */
"use strict";

const TECH_KO = {
  HOMOGLYPH: "닮은꼴 글자 위장",
  JAMO: "자모 분해",
  TRANSPARENT: "투명 텍스트",
  OFFSCREEN: "화면 밖 은닉",
  ETC: "추가 제안",
};
const $ = (s) => document.querySelector(s);
const el = (t, c) => { const e = document.createElement(t); if (c) e.className = c; return e; };

let DATA = null;
let FILTER = "all";
let STATE = {};           // {findingKey: "done"}

const keyOf = (f) => `${f.url}|${f.location}|${f.technique}`;

function loadState(entry) {
  try { STATE = JSON.parse(localStorage.getItem("adguard:" + entry) || "{}"); }
  catch { STATE = {}; }
}
function saveState(entry) {
  try { localStorage.setItem("adguard:" + entry, JSON.stringify(STATE)); }
  catch { /* 저장이 막혀 있어도 화면은 돌아가야 한다 */ }
}

/* ── 탐지 시작 ─────────────────────────────────────── */
$("#form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = $("#url").value.trim();
  if (!url) return;
  $("#err").hidden = true;
  $("#go").disabled = true;
  $("#progress").style.display = "block";
  $("#summary").style.display = "none";
  $("#results").style.display = "none";

  try {
    const r = await fetch("/api/scan", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!r.ok) throw new Error(await r.text());
    poll();
  } catch (ex) {
    fail(ex.message || "탐지를 시작하지 못했습니다.");
  }
});

function fail(msg) {
  $("#err").textContent = msg;
  $("#err").hidden = false;
  $("#go").disabled = false;
  $("#progress").style.display = "none";
}

async function poll() {
  try {
    const s = await (await fetch("/api/status")).json();
    $("#p-pages").textContent = s.pages;
    $("#p-found").textContent = s.found;
    $("#p-time").textContent = Math.round(s.elapsed);
    $("#p-now").textContent = s.current ? "지금 보는 중 — " + s.current : "";
    if (s.error) return fail(s.error);
    if (s.running) return setTimeout(poll, 500);

    const data = await (await fetch("/api/result")).json();
    $("#progress").style.display = "none";
    $("#go").disabled = false;
    render(data, s);
  } catch (ex) {
    fail("상태를 읽지 못했습니다. " + (ex.message || ""));
  }
}

/* ── 그리기 ────────────────────────────────────────── */
function render(data, stat) {
  DATA = data;
  loadState(data.meta.entry_url);

  const fs = data.findings;
  const by = {};
  fs.forEach((f) => { by[f.technique] = (by[f.technique] || 0) + 1; });

  const tiles = $("#tiles");
  tiles.innerHTML = "";
  const add = (n, l, red) => {
    const t = el("div", "tile" + (red ? " red" : ""));
    const a = el("div", "n"); a.textContent = n;
    const b = el("div", "l"); b.textContent = l;
    t.append(a, b); tiles.appendChild(t);
  };
  add(fs.length, "검출 합계", fs.length > 0);
  Object.keys(TECH_KO).forEach((k) => { if (by[k]) add(by[k], TECH_KO[k]); });
  add(stat.pages, "살펴본 페이지");
  add(Math.round(data.meta.elapsed_sec) + "초", "걸린 시간");

  $("#s-note").textContent =
    `${data.meta.entry_url} 기준 · ${data.meta.finished_at.slice(0, 19).replace("T", " ")} 완료`;
  $("#ver").textContent = "도구 버전 " + data.meta.tool_version;
  $("#summary").style.display = "block";
  $("#results").style.display = "block";
  paint();
}

function paint() {
  const list = $("#list");
  list.innerHTML = "";
  const groups = new Map();
  for (const f of DATA.findings) {
    if (FILTER === "todo" && STATE[keyOf(f)] === "done") continue;
    if (FILTER !== "all" && FILTER !== "todo" && f.technique !== FILTER) continue;
    if (!groups.has(f.url)) groups.set(f.url, []);
    groups.get(f.url).push(f);
  }
  if (!groups.size) {
    const e = el("div", "card empty");
    e.textContent = DATA.findings.length
      ? "조건에 맞는 항목이 없습니다."
      : "불법광고로 의심되는 항목을 찾지 못했습니다.";
    list.appendChild(e);
    return;
  }
  for (const [url, items] of groups) list.appendChild(pageBlock(url, items));
}

function pageBlock(url, items) {
  const d = el("details", "page"); d.open = true;
  const s = el("summary");
  const u = el("span", "purl"); u.textContent = url.replace(/^https?:\/\//, "");
  u.title = url;
  const c = el("span", "count"); c.textContent = items.length + "건";
  const open = el("button", "ghost");
  open.type = "button"; open.textContent = "페이지 열기";
  open.style.cssText = "font-size:12px;padding:4px 10px;font-weight:500";
  open.onclick = (e) => { e.preventDefault(); window.open(url, "_blank", "noopener"); };
  s.append(u, c, open);
  d.appendChild(s);
  items.forEach((f) => d.appendChild(findBlock(f)));
  return d;
}

function findBlock(f) {
  const k = keyOf(f);
  const box = el("div", "find" + (STATE[k] === "done" ? " done" : ""));

  const head = el("div", "fhead");
  const t = el("span", "tech t-" + f.technique);
  t.textContent = TECH_KO[f.technique] || f.technique;
  const id = el("span", "fid"); id.textContent = f.id;
  head.append(t, id);
  box.appendChild(head);

  const ev = el("div", "ev");
  ev.textContent = f.evidence_text;
  if (f._normalized && f._normalized !== f.evidence_text) {
    const n = el("span", "norm");
    n.innerHTML = "원래 글자로 되돌리면 → <b></b>";
    n.querySelector("b").textContent = f._normalized;
    ev.appendChild(n);
  }
  box.appendChild(ev);

  const dl = el("dl", "meta");
  const put = (k2, v, cls) => {
    const dt = el("dt"); dt.textContent = k2;
    const dd = el("dd", cls); dd.textContent = v;
    dl.append(dt, dd);
  };
  if (f._reason) put("판단 근거", f._reason);
  if (f._signals && f._signals.length) put("걸린 표현", f._signals.join(", "));
  put("위치", f.location, "sel");
  box.appendChild(dl);

  const acts = el("div", "acts");
  const copy = el("button"); copy.type = "button"; copy.textContent = "위치 복사";
  copy.onclick = async () => {
    try { await navigator.clipboard.writeText(f.location); copy.textContent = "복사했습니다"; }
    catch { copy.textContent = "복사하지 못했습니다"; }
    setTimeout(() => (copy.textContent = "위치 복사"), 1600);
  };
  const done = el("button" , STATE[k] === "done" ? "on" : "");
  done.type = "button";
  done.textContent = STATE[k] === "done" ? "처리 완료" : "처리 완료로 표시";
  done.onclick = () => {
    if (STATE[k] === "done") delete STATE[k]; else STATE[k] = "done";
    saveState(DATA.meta.entry_url);
    paint();
  };
  acts.append(copy, done);
  box.appendChild(acts);
  return box;
}

/* ── 거르기 ────────────────────────────────────────── */
document.querySelectorAll(".chip").forEach((b) => {
  b.onclick = () => {
    FILTER = b.dataset.f;
    document.querySelectorAll(".chip").forEach((o) =>
      o.setAttribute("aria-pressed", String(o === b)));
    paint();
  };
});

/* ── 내려받기 ──────────────────────────────────────── */
$("#csv").onclick = () => {
  const rows = [["번호", "유형", "페이지", "위치", "검출 문구", "판단 근거", "처리 상태"]];
  DATA.findings.forEach((f) => rows.push([
    f.id, TECH_KO[f.technique] || f.technique, f.url, f.location,
    f.evidence_text, f._reason || "",
    STATE[keyOf(f)] === "done" ? "처리 완료" : "미처리",
  ]));
  const esc = (v) => '"' + String(v).replace(/"/g, '""') + '"';
  // 엑셀이 UTF-8 로 읽도록 BOM 을 붙인다
  const csv = "﻿" + rows.map((r) => r.map(esc).join(",")).join("\r\n");
  const a = el("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  a.download = "불법광고_조치목록.csv";
  a.click();
  URL.revokeObjectURL(a.href);
};
$("#print").onclick = () => window.print();
