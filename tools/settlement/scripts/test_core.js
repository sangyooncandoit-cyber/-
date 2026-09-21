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

/* 원가 일괄 입력 */
console.log("\n── 원가 붙여넣기 파싱 ──");
[["유기농 아몬드 1kg\t21,000", "유기농 아몬드 1kg", 21000, "엑셀 탭 구분"],
 ["무선 이어폰, 15400",        "무선 이어폰",       15400, "쉼표 구분"],
 ["실리콘 주방 집게 2p  4500", "실리콘 주방 집게 2p", 4500, "공백 + 끝자리 숫자"],
 ["A\t₩12,000",               "A",                 12000, "원화 기호"],
 ["B\t(1,234)",               "B",                 -1234, "괄호 음수"]].forEach(([line, nm, cost, label]) => {
  const r = X.parseCostPaste(line);
  ok(r.length === 1 && r[0].name === nm && r[0].cost === cost, label,
     `→ ${JSON.stringify(r[0] || null)}`);
});
ok(X.parseCostPaste("상품명만있고숫자없음").length === 0, "숫자 없는 줄은 버린다");
ok(X.parseCostPaste("\n\n  \n").length === 0, "빈 줄은 버린다");

console.log("\n── 원가 이름 맞추기 ──");
{
  const names = ["유기농 아몬드 1kg", "캠핑용 폴딩 의자", "무선 이어폰",
                 "실리콘 주방 집게 2p", "스텐 보온병 500ml"];
  const r = X.matchCosts(X.parseCostPaste(
    ["유기농 아몬드 1kg\t21000",
     "[무료배송] 캠핑용 폴딩 의자\t28000",
     "무선이어폰\t15400",
     "보온병\t7000",
     "집게\t4500",
     "없는상품 XYZ\t9000"].join("\n")), names);

  ok(r.costs["유기농 아몬드 1kg"] === 21000, "이름이 같으면 바로 반영");
  ok(r.costs["캠핑용 폴딩 의자"] === 28000, "대괄호 수식어는 무시하고 같은 이름으로 본다");
  ok(r.costs["무선 이어폰"] === 15400, "띄어쓰기 차이는 같은 이름으로 본다");
  ok(Object.keys(r.costs).length === 3, "짐작으로 반영한 것이 없다",
     `→ ${Object.keys(r.costs).length}개만 반영`);

  const ask = r.ask.find(a => a.from === "보온병");
  ok(ask && ask.to === "스텐 보온병 500ml", "줄여 적은 이름은 후보로 올려 되묻는다",
     `→ ${ask ? ask.score.toFixed(2) : "없음"}`);
  ok(!r.ask.some(a => a.to === "스텐 보온병 500ml" && a.from === "집게"),
     "두 글자짜리는 아무데나 갖다 붙이지 않는다");
  ok(r.miss.includes("없는상품 XYZ") && r.miss.includes("집게"),
     "못 찾은 것은 못 찾았다고 돌려준다", `→ [${r.miss.join(", ")}]`);

  const twice = X.matchCosts(X.parseCostPaste("무선이어폰\t15400\n무선 이어폰\t99999"), names);
  ok(twice.costs["무선 이어폰"] === 99999, "같은 상품이 두 번 오면 나중 값이 이긴다");
}

console.log(`\n${fails ? "실패" : "통과"}: ${checks - fails}/${checks}`);
process.exit(fails ? 1 : 0);
