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

/* 여러 마켓 합산 */
console.log("\n── 마켓 합산 ──");
{
  const mk = (src, name, qty, rev, fee, cogs, ad) =>
    ({ src, name, qty, rev, fee, cogs, ad, profit: rev - fee - cogs - ad });

  const ss = [mk("스마트스토어", "유기농 아몬드 1kg", 10, 229000, 15000, 210000, 5000),
              mk("스마트스토어", "캠핑용 폴딩 의자",   5, 229500, 14000, 140000, 4000)];
  const cp = [mk("쿠팡", "[로켓배송] 유기농 아몬드 1kg", 4, 91600, 9000, 84000, 2000),
              mk("쿠팡", "스텐 텀블러 500",             3,  45000, 4500,  30000, 1000)];

  const m = X.mergeItems([ss, cp]);
  const almond = m.find(o => o.name.indexOf("아몬드") >= 0);

  ok(m.length === 3, "표기만 다른 같은 상품은 한 줄로 합쳐진다", `→ ${m.length}줄`);
  ok(almond.qty === 14 && almond.rev === 320600,
     "수량과 매출이 두 마켓에서 더해진다", `→ ${almond.qty}개 / ${almond.rev.toLocaleString()}원`);
  ok(almond.fee === 24000 && almond.cogs === 294000 && almond.ad === 7000,
     "수수료·원가·광고비도 각각 더해진다");
  ok(almond.profit === 320600 - 24000 - 294000 - 7000, "순이익이 합산과 일치");
  ok(Math.abs(almond.margin - almond.profit / almond.rev) < 1e-12, "마진율은 합산 후 다시 계산");
  ok(almond.sources.length === 2 && almond.sources.includes("쿠팡"),
     "어느 마켓에서 왔는지 남는다", `→ [${almond.sources.join(", ")}]`);
  ok(almond.name === "[로켓배송] 유기농 아몬드 1kg", "표시 이름은 정보가 많은 쪽을 쓴다");

  const solo = m.find(o => o.name.indexOf("텀블러") >= 0);
  ok(solo.sources.length === 1, "한 마켓에만 있는 상품은 그대로 한 줄");

  /* 광고비는 파일별로 배분한 뒤 합쳐야 한다 */
  const adTotal = m.reduce((s, o) => s + o.ad, 0);
  ok(adTotal === 12000, "광고비 총액이 합산 과정에서 보존된다", `→ ${adTotal.toLocaleString()}원`);

  /* 택배비와 할인도 합산 결과에 남아야 한다. 순이익만 맞고 내역이 사라지면
     화면에서 택배비 칸이 통째로 안 보인다. */
  const withShip = X.mergeItems([[Object.assign(mk("스마트스토어","X",1,1000,0,0,0),
                                                { ship: 500, disc: 300 })]]);
  ok(withShip[0].ship === 500 && withShip[0].disc === 300,
     "합산해도 택배비와 할인 내역이 남는다",
     `택배비 ${withShip[0].ship} / 할인 ${withShip[0].disc}`);

  /* 이름이 많이 다르면 묶지 않고 물어본다 */
  const p = X.proposeMerges([
    [{ name: "캠핑용 폴딩 의자" }],
    [{ name: "캠핑 폴딩체어" }, { name: "전혀 다른 상품" }]]);
  ok(p.length === 0 || p[0].a === "캠핑용 폴딩 의자",
     "이름이 다른 쌍만 후보로 올라온다", `→ ${p.length}쌍`);
  ok(!X.proposeMerges([[{ name: "무선 이어폰" }], [{ name: "무선이어폰" }]]).length,
     "표기 차이는 이미 합쳐지므로 후보로 안 올린다");

  /* 원가는 표기가 달라도 한 번만 넣으면 된다 */
  const grid = FX.grids.smartstore;
  const hh = X.findHeader(grid);
  const hd = grid[hh].map(v => String(v ?? "").trim());
  const rws = grid.slice(hh + 1).filter(r => r.some(v => String(v ?? "").trim() !== ""));
  const mp = X.autoMap(hd);
  const { feeMul } = X.detectFeeSigns(rws, mp);
  const oneName = X.aggregate(rws, mp, feeMul, {}, 0)[0].name;
  const spaced = {}; spaced["[특가] " + oneName.replace(/ /g, "")] = 12345;
  const withCost = X.aggregate(rws, mp, feeMul, spaced, 0).find(o => o.name === oneName);
  ok(withCost.unit === 12345, "표기가 달라도 원가를 찾아 쓴다", `→ ${withCost.unit}`);
}

/* 택배비와 할인 */
console.log("\n── 택배비 ──");
{
  const grid = [
    ["주문번호","상품명","수량","결제금액","판매수수료","판매자부담할인액"],
    ["A1","아몬드",  1,  20000, 1000, 2000],
    ["A1","집게",    1,  30000, 1500, 3000],   // 같은 주문에 상품 둘
    ["A2","아몬드",  2,  40000, 2000, 4000],
    ["A3","아몬드", -1, -20000,-1000,-2000],   // 반품
  ];
  const hd = grid[0], rws = grid.slice(1);
  const mp = X.autoMap(hd);

  ok(mp.order != null && hd[mp.order] === "주문번호", "주문번호 컬럼 인식");
  ok(mp.disc  != null && hd[mp.disc]  === "판매자부담할인액", "판매자 부담 할인액 컬럼 인식");
  ok(!mp.fee.includes(mp.disc), "할인 컬럼이 수수료에 섞이지 않음");
  ok(!mp.fee.includes(mp.order), "주문번호가 수수료에 섞이지 않음");

  ok(X.countOrders(rws, mp) === 2, "주문 수는 행 수가 아니라 주문번호 기준",
     `행 4개 → 주문 ${X.countOrders(rws, mp)}건`);

  const { feeMul } = X.detectFeeSigns(rws, mp);
  const it = X.aggregate(rws, mp, feeMul, {}, 0, { ship: 3000 });
  const al = it.find(o => o.name === "아몬드"), jg = it.find(o => o.name === "집게");

  ok(near(al.ship + jg.ship, 6000, 0.01), "택배비 총액 = 단가 × 주문 수",
     `${Math.round(al.ship + jg.ship)} / 6000`);
  ok(near(jg.ship, 1800, 0.01), "한 주문 안에서는 매출 비중으로 나눔",
     `집게 ${Math.round(jg.ship)} (30000/50000 × 3000)`);
  ok(near(al.ship, 4200, 0.01), "반품 행에는 택배비가 붙지 않음",
     `아몬드 ${Math.round(al.ship)} = 1200 + 3000`);

  const noShip = X.aggregate(rws, mp, feeMul, {}, 0, {});
  ok(noShip.every(o => o.ship === 0), "단가를 안 넣으면 택배비는 0");

  const noOrder = Object.assign({}, mp, { order: null });
  const it2 = X.aggregate(rws, noOrder, feeMul, {}, 0, { ship: 3000 });
  ok(it2.every(o => o.ship === 0), "주문번호가 없으면 택배비를 계산하지 않음");

  console.log("\n── 할인 ──");
  ok(near(al.disc, 4000, 0.01), "할인은 상품별로 합산, 반품분은 상계",
     `아몬드 ${Math.round(al.disc)} = 2000 + 4000 − 2000`);
  ok(near(al.profit, al.rev - al.fee - al.ship, 0.01),
     "기본값은 할인을 빼지 않음 (매출이 보통 할인 후 금액이라)");

  const on = X.aggregate(rws, mp, feeMul, {}, 0, { ship: 3000, useDisc: true });
  const alOn = on.find(o => o.name === "아몬드");
  ok(near(alOn.profit, al.profit - 4000, 0.01), "켜면 판매자 부담 할인만큼 더 뺌",
     `${Math.round(al.profit)} → ${Math.round(alOn.profit)}`);

  const neg = rws.map(r => r.slice());
  neg.forEach(r => { r[5] = -r[5]; });                 // 할인을 반대 부호로 적은 파일
  const it3 = X.aggregate(neg, mp, X.detectFeeSigns(neg, mp).feeMul, {}, 0,
                          { ship: 3000, useDisc: true });
  ok(near(it3.find(o => o.name === "아몬드").profit, alOn.profit, 0.01),
     "할인을 음수로 적은 파일도 같은 결과");
}

/* 손익분기 */
console.log("\n── 손익분기 ──");
{
  const mk = o => Object.assign({ qty:0, rev:0, fee:0, cogs:0, ad:0, ship:0, discApplied:0 }, o);
  const fin = o => (o.profit = o.rev - o.fee - o.cogs - o.ad - o.ship - o.discApplied, o);

  const loss = fin(mk({ qty:19, rev:435100, fee:30235, cogs:399000, ad:32032 }));
  const b = X.breakeven(loss);

  ok(b.price > 435100 / 19, "필요 판매가는 지금 판매가보다 높다",
     `${Math.round(b.price)} > ${Math.round(435100/19)}`);
  const X2 = b.price * loss.qty, r = loss.fee / loss.rev;
  ok(near(X2 - X2*r - loss.cogs - loss.ad - loss.ship, 0, 1),
     "그 가격에 팔면 순이익이 정확히 0", `검산 ${Math.round(X2 - X2*r - loss.cogs - loss.ad)}`);
  ok(b.cost < loss.cogs / loss.qty, "버틸 수 있는 원가는 지금 원가보다 낮다",
     `${Math.round(b.cost)} < ${Math.round(loss.cogs/19)}`);
  ok(near(loss.rev - loss.fee - loss.ad - loss.ship - b.cost * loss.qty, 0, 1),
     "그 원가면 순이익이 정확히 0");
  ok(near(b.gap, 26167, 1), "메워야 할 금액은 적자액 그대로", `${Math.round(b.gap)}`);

  const win = fin(mk({ qty:34, rev:1560600, fee:106716, cogs:952000, ad:114891 }));
  ok(X.breakeven(win).price === null, "흑자 상품에는 손익분기를 내지 않는다");

  ok(X.breakeven(fin(mk({ qty:0, rev:0, fee:0, cogs:1000 }))).price === null,
     "수량이 0이면 계산하지 않는다");

  /* 택배비·할인이 붙어 있으면 그것까지 메워야 한다 */
  const heavy = fin(mk({ qty:10, rev:100000, fee:10000, cogs:95000, ad:0,
                         ship:5000, discApplied:3000 }));
  const hb = X.breakeven(heavy);
  const HX = hb.price * 10, hr = heavy.fee / heavy.rev;
  ok(near(HX - HX*hr - heavy.cogs - heavy.ship - heavy.discApplied, 0, 1),
     "택배비와 할인까지 넣고 본전을 맞춘다", `개당 ${Math.round(hb.price)}원`);

  /* 수수료율이 100%를 넘으면 가격을 올려도 답이 없다 */
  const mad = fin(mk({ qty:1, rev:1000, fee:1200, cogs:500 }));
  ok(X.breakeven(mad).price === null, "수수료가 매출보다 크면 필요 판매가를 못 낸다");
}

console.log(`\n${fails ? "실패" : "통과"}: ${checks - fails}/${checks}`);
process.exit(fails ? 1 : 0);
