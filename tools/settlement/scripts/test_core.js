/* 핵심 계산 검증 — 도구의 결과를 독립적으로 만든 정답과 대조한다. */
const fs = require("fs");
const path = require("path");
const X = require(path.join(__dirname, "..", "src", "core.js"));

const FX = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "sample", "_fixtures.json"), "utf-8"));
let fails = 0, checks = 0;

function ok(cond, label, extra){
  checks++;
  if (!cond){ fails++; console.log(`  ✗ ${label}` + (extra ? `  ${extra}` : "")); }
  else console.log(`  ✓ ${label}` + (extra ? `  ${extra}` : ""));
}
const near = (a, b, tol = 1) => Math.abs(a - b) <= tol;

for (const market of ["smartstore", "coupang"]){
  console.log(`\n── ${market} ──`);
  const grid = FX.grids[market];

  const h = X.findHeader(grid);
  const headers = grid[h].map(v => String(v ?? "").trim());
  const rows = grid.slice(h + 1).filter(r => r.some(v => String(v ?? "").trim() !== ""));
  ok(headers.includes("상품명") || headers.includes("등록상품명"),
     `헤더 행 탐지 (${h + 1}번째 줄)`, `[${headers.slice(0, 4).join(", ")}...]`);

  const map = X.autoMap(headers);
  ok(map.name != null, "상품명 컬럼 인식", `→ "${headers[map.name]}"`);
  ok(map.qty  != null, "수량 컬럼 인식",   `→ "${headers[map.qty]}"`);
  ok(map.rev  != null, "매출 컬럼 인식",   `→ "${headers[map.rev]}"`);
  ok(map.fee.length > 0, `수수료 컬럼 ${map.fee.length}개 인식`,
     `→ [${map.fee.map(i => headers[i]).join(", ")}]`);
  ok(!map.fee.includes(map.rev) && !map.fee.includes(map.settle),
     "수수료에 매출/정산금액이 섞이지 않음");

  const { feeMul, flipped } = X.detectFeeSigns(rows, map);
  const expectFlip = market === "coupang" ? 1 : 0;
  ok(flipped === expectFlip, `수수료 부호 규약 판별 (보정 ${flipped}개, 기대 ${expectFlip}개)`);

  const items = X.aggregate(rows, map, feeMul, FX.costs, 0);
  const truth = FX.truth[market];
  ok(items.length === Object.keys(truth).length,
     `상품 수 일치 (${items.length}개)`);

  // 합계행이 상품으로 잡히지 않았는지
  ok(!items.some(o => ["합계","소계","총계"].includes(o.name)), "합계행 제외됨");

  let bad = [];
  for (const o of items){
    const t = truth[o.name];
    if (!t){ bad.push(`${o.name}: 정답에 없음`); continue; }
    if (!near(o.qty, t.qty, 0))   bad.push(`${o.name} 수량 ${o.qty}≠${t.qty}`);
    if (!near(o.rev, t.rev))      bad.push(`${o.name} 매출 ${o.rev}≠${t.rev}`);
    if (!near(o.fee, t.fee))      bad.push(`${o.name} 수수료 ${o.fee}≠${t.fee}`);
    if (!near(o.cogs, t.cogs))    bad.push(`${o.name} 원가 ${o.cogs}≠${t.cogs}`);
    if (!near(o.profit, t.profit))bad.push(`${o.name} 순이익 ${o.profit.toFixed(0)}≠${t.profit}`);
  }
  ok(bad.length === 0, "상품별 수량·매출·수수료·원가·순이익 전부 일치",
     bad.length ? `\n      ${bad.slice(0, 5).join("\n      ")}` : "");

  const T = items.reduce((a, o) => ({ rev: a.rev + o.rev, fee: a.fee + o.fee,
    cogs: a.cogs + o.cogs, profit: a.profit + o.profit }), {rev:0,fee:0,cogs:0,profit:0});
  const TT = Object.values(truth).reduce((a, t) => ({ rev: a.rev + t.rev, fee: a.fee + t.fee,
    cogs: a.cogs + t.cogs, profit: a.profit + t.profit }), {rev:0,fee:0,cogs:0,profit:0});
  ok(near(T.rev, TT.rev) && near(T.fee, TT.fee) && near(T.profit, TT.profit),
     "총계 일치",
     `매출 ${Math.round(T.rev).toLocaleString()} / 수수료 ${Math.round(T.fee).toLocaleString()} / 순이익 ${Math.round(T.profit).toLocaleString()}`);
}

/* 광고비 배분 — 총액이 보존되는지 */
console.log("\n── 광고비 배분 ──");
{
  const grid = FX.grids.coupang;
  const h = X.findHeader(grid), headers = grid[h].map(String);
  const rows = grid.slice(h + 1);
  const map = X.autoMap(headers);
  const { feeMul } = X.detectFeeSigns(rows, map);
  const AD = 500000;
  const items = X.aggregate(rows, map, feeMul, FX.costs, AD);
  const spread = items.reduce((s, o) => s + o.ad, 0);
  ok(near(spread, AD, 1), `배분 총액 보존 (${Math.round(spread).toLocaleString()} / ${AD.toLocaleString()})`);
  const top = [...items].sort((a,b) => b.rev - a.rev)[0];
  const bot = [...items].sort((a,b) => a.rev - b.rev)[0];
  ok(top.ad > bot.ad, "매출 큰 상품에 광고비가 더 배분됨");
}

/* 숫자 파싱 엣지 케이스 */
console.log("\n── 숫자 파싱 ──");
[["39,900",39900],["(1,234)",-1234],["△500",-500],["-577",-577],["₩12,000",12000],
 ["",0],["  ",0],["abc",0],[1234,1234],[null,0]].forEach(([inp, exp]) => {
  ok(X.num(inp) === exp, `num(${JSON.stringify(inp)}) = ${exp}`, `→ ${X.num(inp)}`);
});

console.log(`\n${fails ? "실패" : "통과"}: ${checks - fails}/${checks}`);
process.exit(fails ? 1 : 0);
