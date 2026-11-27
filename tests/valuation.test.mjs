import test from 'node:test';
import assert from 'node:assert/strict';
import {calculateValuation, defaultValuation, minimumDiscountRate, valuationMarket, valuationSources, historicalOwnerEarningsGrowth,
  waccEstimate, revenueHistory, currentTreasury, treasuryReference, historicalGrowthBand, valuationGrowthBand, reverseGrowth, valuationSensitivity, valuationScenarios} from '../web/valuation.mjs';

const report = {
  currency:'USD', fetchedAt:'2026-11-14T12:00:00Z', quote:{price:50,currency:'USD'}, valuationShares:10e6,
  years:[{end:'2025-12-31', income:100e6, capex:50e6, da:20e6, workingCapitalCashEffect:0}],
  valuationData:{netDebt:200e6}
};
const inputs = {...defaultValuation(report), rate:'10', growth:'0', terminal:'0', dividend:'2'};
const near = (a,b,tolerance=1e-10) => assert.ok(Math.abs(a-b)<Math.max(1,Math.abs(b))*tolerance,`${a} != ${b}`);

test('constant earnings and net cash reconcile enterprise, equity and share value', () => {
  const v=calculateValuation(report,inputs);
  near(v.enterpriseValue,1e9); near(v.equityValue,800e6); near(v.perShare,80); near(v.margin,.375);
  near(calculateValuation(report,{...inputs,netDebt:'-200'}).perShare,120);
  assert.equal(v.rows.length,10);
});
test('Lotus worked example exposes all five steps including terminal value at year ten', () => {
  const v=calculateValuation({...report,currency:'EUR'}, {...inputs, ownerEarnings:'200', growth:'9', terminal:'2.5',
    rate:'6', shares:'812838', netDebt:'115.4'});
  near(v.rows[0].flow,218e6); near(v.rows.at(-1).flow,473472734.92,1e-9);
  near(v.projectionPV,2339310846.24,1e-9);
  near(v.terminalValue,473472734.92*1.025/.035,1e-9);
  near(v.terminalPV,v.terminalValue/1.06**10);
  near(v.enterpriseValue,v.projectionPV+v.terminalPV); near(v.equityValue,v.enterpriseValue-115.4e6);
  near(v.perShare,v.equityValue/812838); assert.ok(Math.abs(v.perShare-12261.49)<.01);
});
test('Gordon uses D1 once and allows a mature company in decline', () => {
  const options={...inputs,rate:'8',terminal:'2'};
  const v=calculateValuation(report,options,'gordon');
  near(v.dividendNext,2.04); near(v.perShare,34); assert.equal(v.enterpriseValue,null);
  near(calculateValuation(report,{...options,dividend:'4'},'gordon').perShare,68);
  near(calculateValuation(report,{...options,terminal:'-2'},'gordon').perShare,19.6);
  assert.ok(calculateValuation(report,{...inputs,terminal:'-2'}).terminalPV>0);
});
test('invalid assumptions and missing data cannot become plausible zeroes', () => {
  for(const change of [{rate:'2',terminal:'2'},{netDebt:''},{shares:'0'},{shares:'1.8'},{ownerEarnings:'-1'},
    {growth:'201'},{ownerEarnings:'  '},{terminal:'-100'}]){
    assert.ok(calculateValuation(report,{...inputs,...change}).error);
  }
  for(const dividend of ['', '0']) assert.ok(calculateValuation(report,{...inputs,dividend},'gordon').error);
  assert.equal(valuationSensitivity(report,{...inputs,growth:''}),null);
  const scenario=valuationScenarios({...inputs,growth:'',ownerEarnings:''})[1];
  assert.equal(scenario.growth,''); assert.equal(scenario.ownerEarnings,'');
});
test('Treasury threshold, stale dates and future dates', () => {
  for(const [yieldValue,expected] of [[6.1,'6.1'],[6,'6'],[5.99,'6'],[4.88,'6'],[3,'6'],[0,'6'],[-.1,'6']]){
    const r={...report,treasury:{yield:yieldValue,date:'2026-11-07'}};
    assert.ok(currentTreasury(r)); assert.equal(defaultValuation(r).rate,expected);
  }
  assert.equal(defaultValuation({...report,treasury:{yield:5.1,date:'2026-10-01'}}).rate,'6');
  assert.equal(defaultValuation(report).rate,'6');
  assert.equal(currentTreasury({...report,treasury:{yield:5.1,date:'2026-11-15'}}),false);
});
test('Owner Earnings sources preserve working capital signs and the maintenance proxy', () => {
  const r={...report,years:[
    {end:'2024-12-31',income:10e6,da:8e6,capex:3e6,workingCapitalCashEffect:2e6},
    {end:'2025-12-31',income:36e6,da:6e6,capex:100e6,workingCapitalCashEffect:-2e6}]};
  const history=historicalOwnerEarningsGrowth(r),v=valuationSources(r),defaults=defaultValuation(r);
  near(history,2**(365.25/365)-1); near(v.ownerEarnings,34e6); near(v.maintenanceCapex,6e6);
  assert.equal(defaults.growth,'10'); assert.equal(defaults.ownerEarnings,'34'); assert.equal(defaults.terminal,'2');
  delete r.years[1].workingCapitalCashEffect;
  assert.equal(defaultValuation(r).ownerEarnings,'36'); assert.deepEqual(valuationSources(r).assumedZero,['Working capital cash effect']);
});
test('earlier Yahoo snapshots recover dated working capital, debt and outstanding shares', () => {
  const r={years:[{end:'2025-12-31',income:20e6,da:4e6,capex:9e6,debt:5e6,cash:7e6,shares:999}],
    originalTables:[
      {title:'Kasstromen',dates:['2024-12-31','2025-12-31'],rows:[['ChangeInWorkingCapital',[0,-3e6]]]},
      {title:'Balans',dates:['2025-12-31'],rows:[['ShareIssued',[999]],['TreasurySharesNumber',[10]]]}]};
  const v=defaultValuation(r);
  assert.equal(v.ownerEarnings,'17'); assert.equal(v.netDebt,'-2'); assert.equal(v.shares,'989');
  assert.equal(defaultValuation({...r,originalTables:[]}).shares,'');
});
test('reverse DCF recovers a known growth, sensitivity centre matches main value', () => {
  const v=calculateValuation(report,{...inputs,growth:'5'});
  near(reverseGrowth(report,inputs,v.perShare),.05);
  near(valuationSensitivity(report,inputs).rows[2].cells[2].perShare,calculateValuation(report,inputs).perShare);
  assert.equal(reverseGrowth(report,inputs,-1),null);
});

test('DCF caps growth independently at 10% and 12% with an unchanged negative floor', () => {
  // Four calendar years including a leap day make this exactly four 365.25-day years.
  for (const [cagr,strict,moderate] of [[16,'10','12'],[11,'10','11'],[9,'9','9'],[0,'0','0'],[-7,'-7','-7'],[-24,'-20','-20']]) {
    const year = {income:100e6,da:10e6,capex:20e6,workingCapitalCashEffect:0};
    const r = {...report, years:[{...year,end:'2020-12-31'}, {...year,end:'2024-12-31',income:year.income*(1+cagr/100)**4}]};
    const defaults=defaultValuation(r);
    const band=valuationGrowthBand(r,{...defaults,growth:'28'});
    near(band.historical,cagr/100);
    assert.equal(band.strict,strict); assert.equal(band.moderate,moderate); assert.equal(defaults.growth,strict);
    near(band.strictValue,calculateValuation(r,{...defaults,growth:strict}).perShare);
    near(band.moderateValue,calculateValuation(r,{...defaults,growth:moderate}).perShare);
    assert.deepEqual(valuationGrowthBand(r,defaults),band);
  }
});
test('missing history and invalid valuation inputs do not produce default band prices', () => {
  const missing=valuationGrowthBand(report,inputs);
  assert.equal(missing.suggested,null); assert.equal(missing.historical,null); assert.equal(missing.period,null);
  assert.equal(missing.strict,''); assert.equal(missing.moderate,'');
  assert.equal(missing.strictValue,null); assert.equal(missing.moderateValue,null);
  const r={...report,years:[{...report.years[0],end:'2024-12-31'},report.years[0]]};
  assert.equal(historicalGrowthBand(r).strict,'0');
  assert.equal(valuationGrowthBand(r,{...inputs,netDebt:''}).strictValue,null);
});
test('Treasury links are derived from the source and observation month, including legacy FRED snapshots',()=>{
 const date='2026-11-20',unexpected='https://example.test';
 assert.equal(treasuryReference({date,sourceID:'treasury',url:unexpected}).url,
  'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=202611');
 for(const sourceID of ['fred',undefined])assert.equal(treasuryReference({date,sourceID,url:unexpected}).url,'https://fred.stlouisfed.org/series/DGS10');
 assert.equal(treasuryReference({date,sourceID:'unknown',url:unexpected}),null);
});

test('historical growth labels use the fiscal endpoints of the actual earnings sample',()=>{
 const complete={income:100,da:10,capex:10,workingCapitalCashEffect:0};
 const r={...report,years:[
  {end:'2021-12-31'}, {...complete,end:'2022-12-31'}, {end:'2023-12-31'},
  {...complete,end:'2025-12-31',income:150}, {end:'2026-12-31'}]};
 const band=historicalGrowthBand(r);
 assert.equal(band.period,'2022–2025');
 near(band.historical,1.5**(365.25/1096)-1);
 assert.equal(valuationGrowthBand(r,inputs).period,band.period);
});

test('main models, scenarios and selectable sensitivity cells enforce the same Treasury minimum', () => {
  const r={...report,treasury:{yield:7.2,date:'2026-11-13'}};
  const min=minimumDiscountRate(r), valid={...inputs,rate:String(min)};
  for (const method of ['dcf','gordon']) {
    assert.match(calculateValuation(r,{...valid, rate:'7.19'},method).error,/model minimum/);
    assert.equal(calculateValuation(r,valid,method).error,undefined);
  }
  assert.equal(valuationScenarios(valid,r)[2].rate,'7.2');
  assert.deepEqual(valuationSensitivity(r,valid).rates,[7.2,8.2,9.2]);
  assert.equal(defaultValuation({...r,treasury:{yield:8,date:'2026-10-01'}}).rate,'6');
});
test('quote metrics retain the quote currency and unknown units stay unavailable', () => {
  const r={...report,currency:'JPY',quote:{currency:'USD',price:20,marketCap:50e6}};
  assert.deepEqual(valuationMarket(r),{currency:'USD',price:20,capitalisation:50e6});
  assert.equal(calculateValuation(r,inputs).margin,null);
  assert.equal(valuationMarket({...r,quote:{currency:'GBp',price:2000,marketCap:50e6}}).capitalisation,null);
  assert.deepEqual(valuationMarket({...report,quote:null}),{currency:null,price:null,capitalisation:null});
});

test('VEEV example uses model-only zero maintenance capex and preserves the unreported source', () => {
 const y={end:'2026-01-31',income:908906000, da:37972000, capex:null, workingCapitalCashEffect:-91938000};
 const r={...report, years:[y]};
 const v=valuationSources(r);
 assert.equal(v.ownerEarnings,854940000); assert.equal(v.maintenanceCapex,null); assert.equal(y.capex,null);
 assert.deepEqual(v.assumedZero,['Maintenance capex estimate']);
 assert.equal(defaultValuation(r).ownerEarnings,'854.94');
 const missing=valuationSources({...r,years:[{...y,da:null,workingCapitalCashEffect:null}]});
 assert.equal(missing.ownerEarnings,y.income); assert.equal(missing.depreciation,null);
 assert.equal(missing.workingCapitalCashEffect,null);
 assert.equal(valuationSources({...r,years:[{...y,income:null}]}).ownerEarnings,null);
});

test('new 2% terminal defaults and saved 2.5% assumptions are distinct; unavailable old earnings recover', async () => {
 const {restoreValuation}=await import('../web/saved.mjs');
 const r={...report,years:[{...report.years[0],capex:null}]};
 const old={...defaultValuation(r),terminal:'2.5',ownerEarnings:''}; delete old.waccBeta;
 const recovered=restoreValuation(r,{valuationInputs:old});
 assert.equal(recovered.inputs.ownerEarnings,'120'); assert.equal(recovered.inputs.terminal,'2.5'); assert.equal(old.ownerEarnings,'');
 assert.equal(defaultValuation(r).terminal,'2');
});

test('upside and margin compare like currencies, with different denominators',()=>{
 const v=calculateValuation(report,inputs);
 near(v.upside,.6); near(v.margin,.375);
 for(const quote of [{currency:'USD',price:0},{currency:'EUR',price:50}]){
  assert.equal(calculateValuation({...report,quote},inputs).upside,null);
 }
});

test('WACC reconciles capital weights, observed costs, fallback assumptions and reciprocal currencies',()=>{
 const annual={end:'2025-12-31',debt:200,interest:10,tax:30,pretax:100};
 const r={...report,country:'United States',beta:1.2,quote:{currency:'USD',price:50,marketCap:800},years:[annual],
  treasury:{sourceID:'treasury',date:'2026-11-12',yield:4},waccTreasury:{date:'2026-11-12',yield:4.5}};
 const w=waccEstimate(r);
 near(w.debtWeight,.2); near(w.riskFree,.045); near(w.equityCost,.105); near(w.debtCost,.05); near(w.tax,.30); near(w.rate,.091);
 assert.equal(w.useYahoo,true); assert.equal(w.taxAssumed,false);
 const missing=waccEstimate({...r,beta:null,years:[{...annual,pretax:-10,interest:null}],waccTreasury:{date:'2026-10-01',yield:9}},'1');
 near(missing.tax,.21); near(missing.debtCost,.055); near(missing.rate,.8*.09+.2*.055*.79);
 assert.equal(missing.taxAssumed,true); assert.equal(missing.debtCostAssumed,true); assert.equal(missing.useYahoo,false);
 near(waccEstimate({...r,years:[{...annual,interest:0}]}).debtCost,.045);
 near(waccEstimate({...r,years:[{...annual,debt:0,tax:null,interest:null}]}).rate,.105);
 assert.equal(waccEstimate({...r,beta:null}).rate,null); assert.equal(waccEstimate({...r,treasury:null,waccTreasury:null}).rate,null);
 const cross={...r,currency:'EUR'};
 assert.equal(waccEstimate(cross).rate,null);
 const fx={from:'USD',to:'EUR',rate:0.9,at:r.fetchedAt};
 near(waccEstimate({...cross,fx}).equity,720);
});

test('revenue CAGR uses the statement endpoints independent of missing owner earnings',()=>{
 const r={years:[{end:'2020-12-31',revenue:100},{end:'2024-12-31',revenue:200}]};
 near(revenueHistory(r).growth,2**.25-1); assert.equal(revenueHistory(r).period,'2020–2024');
 assert.equal(historicalOwnerEarningsGrowth(r),null);
});
