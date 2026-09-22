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
  order: ["주문번호","상품주문번호","묶음배송번호","배송비묶음번호","주문no"],
  disc:  ["판매자부담할인액","판매자부담할인","셀러부담할인","판매자할인액",
          "판매자부담쿠폰","즉시할인액","상품할인액"],
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
  ["order","name","qty","settle","rev","disc","date"].forEach(function(role){
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

/* 정산 파일에서 주문이 몇 건인지. 한 주문에 상품이 여럿이면 행도 여러 개라,
   행 수로 세면 주문 수가 상품 수만큼 부풀려진다. */
function countOrders(rows, map){
  var oi = map.order, ri = map.rev, seen = {}, n = 0;
  if (oi == null) return 0;
  for (var i = 0; i < rows.length; i++){
    if (num(rows[i][ri]) <= 0) continue;           // 반품 행은 새 배송이 아니다
    var k = String(rows[i][oi] == null ? "" : rows[i][oi]).trim();
    if (!k || seen[k]) continue;
    seen[k] = 1; n++;
  }
  return n;
}

/* 상품별 집계. 반품은 음수 행이므로 매출·수수료·원가에서 자연히 빠진다.

   opts.ship    건당 실제 택배비. 주문번호 컬럼이 있어야 계산한다.
   opts.useDisc 매출 칸이 할인 전 금액일 때만 켠다. 할인 후 금액에서 또 빼면
                없는 적자가 생긴다. */
function aggregate(rows, map, feeMul, costs, ad, opts){
  costs = costs || {}; ad = ad || 0; opts = opts || {};
  var ship = Number(opts.ship) || 0, useDisc = !!opts.useDisc;
  var ni = map.name, qi = map.qty, ri = map.rev, oi = map.order, di = map.disc;
  var by = {}, order = [];

  /* 택배비는 주문 단위로 나간다. 한 주문 안에 상품이 여럿이면
     그 주문의 택배비를 상품들의 매출 비중으로 나눠 붙인다. */
  var ordRev = {};
  if (ship && oi != null){
    for (var j = 0; j < rows.length; j++){
      var k0 = String(rows[j][oi] == null ? "" : rows[j][oi]).trim();
      if (!k0) continue;
      ordRev[k0] = (ordRev[k0] || 0) + Math.max(0, num(rows[j][ri]));
    }
  }

  for (var i = 0; i < rows.length; i++){
    var r = rows[i];
    var nm = String(r[ni] == null ? "" : r[ni]).trim();
    if (!nm || SUMMARY_WORDS.indexOf(nm.toLowerCase()) >= 0) continue;
    var fee = 0;
    (map.fee || []).forEach(function(ci){ fee += num(r[ci]) * (feeMul[ci] == null ? 1 : feeMul[ci]); });
    if (!by[nm]){ by[nm] = { name: nm, qty: 0, rev: 0, fee: 0, disc: 0, ship: 0 }; order.push(nm); }
    by[nm].qty += (qi == null ? 0 : num(r[qi]));
    by[nm].rev += num(r[ri]);
    by[nm].fee += fee;
    if (di != null) by[nm].disc += num(r[di]);      // 부호는 마지막에 정리한다
    if (ship && oi != null){
      var k = String(r[oi] == null ? "" : r[oi]).trim();
      var tot = ordRev[k] || 0;
      if (k && tot > 0) by[nm].ship += ship * (Math.max(0, num(r[ri])) / tot);
    }
  }
  var items = order.map(function(k){ return by[k]; });
  var posRev = items.reduce(function(s, o){ return s + Math.max(0, o.rev); }, 0);

  /* 같은 상품을 마켓마다 다르게 적어둔다. 원가는 한 번만 넣고 쓰도록
     정확한 이름이 없으면 표기를 지운 이름으로 한 번 더 찾는다. */
  var costIdx = {};
  Object.keys(costs).forEach(function(k){ costIdx[norm(k)] = costs[k]; });

  items.forEach(function(o){
    o.unit   = Number((costs[o.name] != null ? costs[o.name] : costIdx[norm(o.name)]) || 0);
    o.cogs   = o.unit * o.qty;
    o.ad     = posRev > 0 ? ad * (Math.max(0, o.rev) / posRev) : 0;
    o.disc   = Math.abs(o.disc);                   // 마켓마다 +로도 -로도 적는다
    o.discApplied = useDisc ? o.disc : 0;
    o.profit = o.rev - o.fee - o.cogs - o.ad - o.ship - o.discApplied;
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

/* 이 파일이 어느 달 것인지. 날짜 칸에서 제일 많이 나오는 연월을 쓴다.
   한 파일에 두 달이 걸쳐 있어도 주된 달로 잡힌다. */
function periodOf(rows, map){
  var di = map.date, tally = {}, best = null, bn = 0;
  if (di == null) return null;
  for (var i = 0; i < rows.length; i++){
    var v = rows[i][di];
    var t = (v instanceof Date) ? (v.getFullYear() + "-" + ("0" + (v.getMonth() + 1)).slice(-2))
                                : String(v == null ? "" : v).trim();
    var m = t.match(/(20\d{2})\D?(0[1-9]|1[0-2])/);
    if (!m) continue;
    var k = m[1] + "-" + m[2];
    tally[k] = (tally[k] || 0) + 1;
    if (tally[k] > bn){ bn = tally[k]; best = k; }
  }
  return best;
}

/* 두 기간의 집계를 상품별로 맞붙인다.
   한 달치만 보면 "지금 적자"는 알지만 "적자로 넘어가는 중"은 못 잡는다. */
function compareItems(prev, curr){
  var byPrev = {}, out = [];
  (prev || []).forEach(function(o){ byPrev[norm(o.name)] = o; });
  var seen = {};

  (curr || []).forEach(function(o){
    var k = norm(o.name), p = byPrev[k] || null;
    seen[k] = 1;
    out.push({
      name: o.name,
      prev: p ? p.profit : null,
      curr: o.profit,
      delta: o.profit - (p ? p.profit : 0),
      isNew: !p,
      gone: false,
      crossed: !!p && p.profit >= 0 && o.profit < 0,   // 흑자에서 적자로 넘어갔다
      recovered: !!p && p.profit < 0 && o.profit >= 0
    });
  });

  (prev || []).forEach(function(o){
    var k = norm(o.name);
    if (seen[k]) return;
    out.push({ name: o.name, prev: o.profit, curr: null, delta: -o.profit,
               isNew: false, gone: true, crossed: false, recovered: false });
  });

  // 넘어간 것 먼저, 그다음 많이 나빠진 순
  return out.sort(function(a, b){
    if (a.crossed !== b.crossed) return a.crossed ? -1 : 1;
    return a.delta - b.delta;
  });
}

/* 적자 상품을 찾은 다음이 비어 있었다. 얼마면 본전인지까지 내놓는다.

   판매가를 올리면 수수료도 같이 오른다. 수수료는 매출에 비례하므로
   필요 매출 X 는 X - X*r - (원가+광고비+택배비) = 0 을 푼 값이다.
   여기서 r 은 이 상품의 실효 수수료율이다. */
function breakeven(o){
  var qty = Number(o.qty) || 0;
  var fixed = (o.cogs || 0) + (o.ad || 0) + (o.ship || 0) + (o.discApplied || 0);
  var out = { price: null, cost: null, gap: 0 };
  if (qty <= 0 || (o.profit || 0) >= 0) return out;

  var r = o.rev > 0 ? (o.fee || 0) / o.rev : 0;
  if (r < 0) r = 0;
  if (r < 1) out.price = (fixed / (1 - r)) / qty;      // 개당 필요 판매가

  var room = (o.rev || 0) - (o.fee || 0) - (o.ad || 0) - (o.ship || 0) - (o.discApplied || 0);
  if (room > 0) out.cost = room / qty;                 // 개당 버틸 수 있는 원가
  out.gap = -(o.profit || 0);
  return out;
}

/* ── 여러 마켓 합치기 ───────────────────────────────────────────
   파일마다 컬럼도 수수료 부호도 광고비도 다르므로 집계는 파일별로 따로 한다.
   합치는 것은 그 결과다. 표기만 다른 같은 이름은 알아서 묶고,
   비슷하기만 한 것은 묶지 않고 후보로만 내놓는다. */

/* 파일별 집계 결과들을 상품 단위로 합친다. alias 는 사용자가 직접 묶어준 것. */
function mergeItems(lists, alias){
  alias = alias || {};
  var by = {}, order = [];
  (lists || []).forEach(function(list){
    (list || []).forEach(function(o){
      var key = alias[o.name] || norm(o.name);
      if (!by[key]){
        by[key] = { name: o.name, qty: 0, rev: 0, fee: 0, cogs: 0, ad: 0,
                    ship: 0, disc: 0, discApplied: 0, profit: 0, _srcs: {} };
        order.push(key);
      }
      var t = by[key];
      if (String(o.name).length > String(t.name).length) t.name = o.name;  // 긴 쪽이 정보가 많다
      t.qty += o.qty; t.rev += o.rev; t.fee += o.fee;
      t.cogs += o.cogs; t.ad += o.ad; t.profit += o.profit;
      t.ship += (o.ship || 0); t.disc += (o.disc || 0);
      t.discApplied += (o.discApplied || 0);
      if (o.src != null) t._srcs[o.src] = 1;
    });
  });
  return order.map(function(k){
    var t = by[k];
    t.unit = t.qty ? t.cogs / t.qty : 0;
    t.margin = t.rev !== 0 ? t.profit / t.rev : 0;
    t.sources = Object.keys(t._srcs);
    delete t._srcs;
    return t;
  });
}

/* 서로 다른 파일에 있는, 같은 상품일 법한 이름 쌍을 찾는다.
   표기만 다른 것은 이미 합쳐지므로 제외하고 나머지만 내놓는다. */
function proposeMerges(lists, opts){
  opts = opts || {};
  var floor = opts.floor == null ? 0.62 : opts.floor;
  var gap   = opts.gap   == null ? 0.08 : opts.gap;
  var out = [], seen = {};

  for (var i = 0; i < (lists || []).length; i++){
    for (var j = i + 1; j < lists.length; j++){
      (lists[i] || []).forEach(function(a){
        var best = null, bestScore = 0, second = 0;
        (lists[j] || []).forEach(function(b){
          if (norm(a.name) === norm(b.name)) return;      // 이미 한 덩어리다
          var sc = similar(a.name, b.name);
          if (sc > bestScore){ second = bestScore; bestScore = sc; best = b; }
          else if (sc > second) second = sc;
        });
        if (!best || bestScore < floor || bestScore - second < gap) return;
        var key = [norm(a.name), norm(best.name)].sort().join("|");
        if (seen[key]) return;
        seen[key] = 1;
        out.push({ a: a.name, b: best.name, score: bestScore });
      });
    }
  }
  return out.sort(function(x, y){ return y.score - x.score; });
}

var API = { ALIAS: ALIAS, norm: norm, num: num, findHeader: findHeader,
            autoMap: autoMap, detectFeeSigns: detectFeeSigns, aggregate: aggregate,
            countOrders: countOrders, breakeven: breakeven,
            periodOf: periodOf, compareItems: compareItems,
            parseCostPaste: parseCostPaste, similar: similar, matchCosts: matchCosts,
            mergeItems: mergeItems, proposeMerges: proposeMerges };
if (typeof module !== "undefined" && module.exports) module.exports = API;
root.XRAY = API;
})(typeof globalThis !== "undefined" ? globalThis : this);
