/* 정산 엑스레이 — 순수 계산 로직.
   DOM을 건드리지 않는다. 브라우저에서는 인라인되고, node에서는 그대로 테스트된다. */
(function (root) {
"use strict";

var ALIAS = {
  name:  ["상품명","등록상품명","노출상품명","판매상품명","품명","상품","옵션명","제품명"],
  qty:   ["수량","판매수량","주문수량","구매수량","확정수량"],
  rev:   ["결제금액","판매금액","상품금액","매출액","총판매금액","실판매금액","주문금액"],
  fee:   ["수수료","판매수수료","결제수수료","주문관리수수료","매출연동수수료","서비스이용료",
          "쿠폰분담금","할인분담금","차감액","공제금액"],
  settle:["정산금액","정산대상금액","정산예정금액","실지급액","지급액"],
  date:  ["정산완료일","정산일","정산기준일","결제일","주문일","날짜"]
};
var SUMMARY_WORDS = ["합계","소계","총계","계","total"];

function norm(s){ return String(s == null ? "" : s).replace(/\s|\(.*?\)|\[.*?\]|_/g, "").toLowerCase(); }

/* 숫자 파싱 — 콤마, 원화기호, 괄호음수, 회계 △ 표기를 모두 받는다 */
function num(v){
  if (typeof v === "number") return isFinite(v) ? v : 0;
  var s = String(v == null ? "" : v).trim();
  if (!s) return 0;
  var neg = false;
  if (/^\(.*\)$/.test(s)) { neg = true; s = s.slice(1, -1); }
  if (/^[△▲-]/.test(s))  { neg = true; s = s.replace(/^[△▲-]/, ""); }
  s = s.replace(/[,\s₩원]/g, "");
  var n = parseFloat(s);
  if (!isFinite(n)) return 0;
  return neg ? -n : n;
}

/* 상단 제목행을 건너뛰고 진짜 헤더 줄을 찾는다 */
function findHeader(rows){
  var best = 0, bestScore = -1, limit = Math.min(rows.length, 25);
  for (var i = 0; i < limit; i++){
    var cells = rows[i].map(norm).filter(Boolean);
    if (cells.length < 3) continue;
    var score = cells.length;
    for (var c = 0; c < cells.length; c++){
      for (var role in ALIAS){
        if (ALIAS[role].some(function(a){ return cells[c].indexOf(norm(a)) >= 0; })) { score += 6; break; }
      }
    }
    if (score > bestScore){ bestScore = score; best = i; }
  }
  return best;
}

function scoreHeader(h, alias){
  var H = norm(h), A = norm(alias);
  if (!H || !A) return 0;
  if (H === A) return 100 + A.length;
  if (H.indexOf(A) >= 0) return 50 + A.length;
  return 0;
}

/* 컬럼 → 역할. 수수료만 여러 컬럼을 동시에 가진다. */
function autoMap(headers){
  var map = {}, taken = {};
  ["name","qty","settle","rev","date"].forEach(function(role){
    var bi = -1, bs = 0;
    headers.forEach(function(h, i){
      if (taken[i]) return;
      ALIAS[role].forEach(function(a){ var s = scoreHeader(h, a); if (s > bs){ bs = s; bi = i; } });
    });
    if (bi >= 0){ map[role] = bi; taken[bi] = true; }
  });
  map.fee = [];
  headers.forEach(function(h, i){
    if (taken[i]) return;
    if (ALIAS.fee.some(function(a){ return scoreHeader(h, a) > 0; })) map.fee.push(i);
  });
  return map;
}

/* 마켓마다 수수료를 +로도 -로도 적는다. 매출 부호와 비교해 규약을 알아낸다. */
function detectFeeSigns(rows, map){
  var feeMul = {}, flipped = 0, ri = map.rev;
  (map.fee || []).forEach(function(ci){
    var same = 0, opp = 0;
    for (var i = 0; i < rows.length; i++){
      var rv = num(rows[i][ri]), fv = num(rows[i][ci]);
      if (!rv || !fv) continue;
      if (Math.sign(rv) === Math.sign(fv)) same++; else opp++;
    }
    var mul = (opp > same) ? -1 : 1;
    feeMul[ci] = mul;
    if (mul === -1) flipped++;
  });
  return { feeMul: feeMul, flipped: flipped };
}

/* 상품별 집계. 반품은 음수 행이므로 매출·수수료·원가에서 자연히 빠진다. */
function aggregate(rows, map, feeMul, costs, ad){
  costs = costs || {}; ad = ad || 0;
  var ni = map.name, qi = map.qty, ri = map.rev, by = {}, order = [];
  for (var i = 0; i < rows.length; i++){
    var r = rows[i];
    var nm = String(r[ni] == null ? "" : r[ni]).trim();
    if (!nm || SUMMARY_WORDS.indexOf(nm.toLowerCase()) >= 0) continue;
    var fee = 0;
    (map.fee || []).forEach(function(ci){ fee += num(r[ci]) * (feeMul[ci] == null ? 1 : feeMul[ci]); });
    if (!by[nm]){ by[nm] = { name: nm, qty: 0, rev: 0, fee: 0 }; order.push(nm); }
    by[nm].qty += (qi == null ? 0 : num(r[qi]));
    by[nm].rev += num(r[ri]);
    by[nm].fee += fee;
  }
  var items = order.map(function(k){ return by[k]; });
  var posRev = items.reduce(function(s, o){ return s + Math.max(0, o.rev); }, 0);
  items.forEach(function(o){
    o.unit   = Number(costs[o.name] || 0);
    o.cogs   = o.unit * o.qty;
    o.ad     = posRev > 0 ? ad * (Math.max(0, o.rev) / posRev) : 0;
    o.profit = o.rev - o.fee - o.cogs - o.ad;
    o.margin = o.rev !== 0 ? o.profit / o.rev : 0;
  });
  return items;
}

/* ── 원가 일괄 입력 ─────────────────────────────────────────────
   품목이 50개면 칸을 50번 채워야 했다. 거기서 대부분 포기한다.
   엑셀에서 상품명과 원가 두 칸을 긁어 붙여넣게 한다. */

/* 붙여넣은 텍스트를 {name, cost} 목록으로. 탭·쉼표·마지막 숫자 순으로 시도한다. */
function parseCostPaste(text){
  var out = [];
  String(text == null ? "" : text).split(/\r?\n/).forEach(function(line){
    if (!line.trim()) return;
    var name = null, cost = null, m;
    if (line.indexOf("\t") >= 0){
      var t = line.split("\t").filter(function(x){ return x.trim() !== ""; });
      if (t.length >= 2){ name = t[0]; cost = t[t.length - 1]; }
    }
    if (name == null && (m = line.match(/^(.*?),\s*([^,]+)$/))){
      name = m[1]; cost = m[2];
    }
    if (name == null && (m = line.match(/^(.*?)[\s]+([0-9][0-9,.\u20a9()\u25b3-]*)$/))){
      name = m[1]; cost = m[2];
    }
    if (name == null) return;
    name = name.trim();
    if (!name) return;
    out.push({ name: name, cost: num(cost) });
  });
  return out;
}

function bigrams(s){
  var g = [];
  for (var i = 0; i + 1 < s.length; i++) g.push(s.slice(i, i + 2));
  return g;
}

/* 두 이름의 닮은 정도 0~1. 한글은 형태 변화가 적어 바이그램이 잘 듣는다. */
function similar(a, b){
  a = norm(a); b = norm(b);
  if (!a || !b) return 0;
  if (a === b) return 1;
  var A = bigrams(a), B = bigrams(b);
  if (!A.length || !B.length) return a === b ? 1 : 0;
  var bag = {}, hit = 0;
  A.forEach(function(g){ bag[g] = (bag[g] || 0) + 1; });
  B.forEach(function(g){ if (bag[g] > 0){ bag[g]--; hit++; } });
  var dice = 2 * hit / (A.length + B.length);

  /* 원가표에는 "스텐 보온병 500ml"을 "보온병"이라고만 적어두는 일이 흔하다.
     길이 차가 크면 바이그램 점수가 주저앉으므로, 한쪽이 다른 쪽에 통째로
     들어 있으면 덮는 비율만큼 올려준다. 두 글자짜리는 아무데나 걸리므로 뺀다. */
  var shortS = a.length <= b.length ? a : b, longS = a.length <= b.length ? b : a;
  if (shortS.length >= 3 && longS.indexOf(shortS) >= 0){
    dice = Math.max(dice, 0.55 + 0.45 * (shortS.length / longS.length));
  }
  return dice;
}

/* 붙여넣은 목록을 실제 상품명에 맞춘다.

   이름이 똑같은 것만 바로 반영하고, 비슷하기만 한 것은 물어본다.
   원가가 틀리면 손익이 통째로 틀리므로 짐작으로 넣지 않는다. */
function matchCosts(pasted, names, opts){
  opts = opts || {};
  var floor = opts.floor == null ? 0.55 : opts.floor;   // 이 아래는 후보로도 안 본다
  var gap   = opts.gap   == null ? 0.08 : opts.gap;     // 2등과 이만큼 벌어져야 후보
  var costs = {}, ask = [], miss = [], taken = {};

  pasted.forEach(function(row){
    var exact = null;
    for (var i = 0; i < names.length; i++){
      if (norm(names[i]) === norm(row.name)){ exact = names[i]; break; }
    }
    if (exact != null){ costs[exact] = row.cost; taken[exact] = 1; return; }

    var best = null, bestScore = 0, second = 0;
    names.forEach(function(n){
      if (taken[n]) return;
      var sc = similar(row.name, n);
      if (sc > bestScore){ second = bestScore; bestScore = sc; best = n; }
      else if (sc > second) second = sc;
    });

    if (best != null && bestScore >= floor && bestScore - second >= gap){
      ask.push({ from: row.name, to: best, cost: row.cost, score: bestScore });
    } else {
      miss.push(row.name);
    }
  });

  return { costs: costs, ask: ask, miss: miss };
}

var API = { ALIAS: ALIAS, norm: norm, num: num, findHeader: findHeader,
            autoMap: autoMap, detectFeeSigns: detectFeeSigns, aggregate: aggregate,
            parseCostPaste: parseCostPaste, similar: similar, matchCosts: matchCosts };
if (typeof module !== "undefined" && module.exports) module.exports = API;
root.XRAY = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
