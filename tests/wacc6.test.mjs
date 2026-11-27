// SPDX-License-Identifier: AGPL-3.0-only
import test from 'node:test';
import assert from 'node:assert/strict';
import {waccEstimate,defaultValuation,calculateValuation,valuationScenarios,valuationSensitivity,reverseGrowth} from '../web/valuation.mjs';
import {restoreValuation,updateValuationScenarios,refreshedValuationOptions} from '../web/saved.mjs';
import {taxReference} from '../web/statutoryTax.mjs';

const date='2026-11-26';
const riskFreeRates={EUR:{date,yield:3.25,currency:'EUR',sourceID:'bund'},USD:{date,yield:4.9,currency:'USD',sourceID:'tnx'}};
const base={currency:'EUR',fetchedAt:'2026-11-27',riskFreeRates,beta:.684,country:'Belgium',valuationShares:50e6,
  quote:{currency:'EUR',price:20,marketCap:1000},years:[{end:'2025-12-31',income:100e6,debt:100,interest:44,tax:70,pretax:100}]};
const near=(a,b)=>assert.ok(Number.isFinite(a)&&Math.abs(a-b)<1e-11,`${a} ≠ ${b}`);
const qr=[['2025-12-31','2025-Q4'],['2026-03-31','2026-Q1'],['2026-06-30','2026-Q2'],['2026-09-30','2026-Q3']]
  .map(([end,periodKey])=>({end,periodKey,debt:100,interest:2,tax:3,pretax:12}));

test('banks and insurers discount by their reporting-currency cost of equity only, including below the ordinary floor',()=>{
 for(const industry of ['Banks - Regional','Insurance - Diversified']){
  const report={...base,beta:.184,sector:'Financial Services',industry};
  const w=waccEstimate(report);
  near(w.rate,.0417); assert.equal(w.equityOnly,true); assert.equal(w.debtCost,undefined);
  const inputs={...defaultValuation(report),growth:'2'};
  assert.equal(inputs.rate,'4.17'); assert.equal(inputs.netDebt,'');
  const value=calculateValuation(report,{...inputs,rate:'18.55',netDebt:'99999'});
  near(value.rate,.0417); assert.equal(value.enterpriseValue,null); near(value.total,value.equityValue);
  for(const scenario of valuationScenarios(inputs,report)) assert.equal(scenario.rate,'4.17');
  assert.deepEqual(valuationSensitivity(report,inputs).rates,[4.17]);
  const restored=restoreValuation(report,{valuationInputs:{...inputs,rate:'17'},valuationScenarios:valuationScenarios(inputs,report)});
  assert.equal(restored.inputs.rate,'4.17'); assert.ok(restored.scenarios.every(s=>s.rate==='4.17'));
  assert.ok(calculateValuation({...report,riskFreeRates:{}},inputs).error);
 }
});

test('Visa payments is valued with WACC, not a bank; TTM shares the debt balance date and avoids mismatched FY',()=>{
 const report={...base,industry:'Credit Services',sector:'Financial Services',quarters:qr};
 const w=waccEstimate(report);
 assert.equal(w.equityOnly,false); assert.equal(w.balanceDate,qr[3].end); assert.equal(w.fiscalDate,w.balanceDate);
 assert.equal(w.interest,8); assert.equal(w.incomeTax,12); assert.equal(w.pretax,48); near(w.debtCost,.08); near(w.tax,.25);
 const incomplete=waccEstimate({...report,quarters:qr.slice(1)});
 assert.equal(incomplete.interest,null); assert.equal(incomplete.flowBasis,null);
 near(incomplete.debtCost,.0475); near(incomplete.tax,.25);
 const fiscal=waccEstimate({...report,quarters:[]}); assert.equal(fiscal.flowBasis,'FY=TTM'); near(fiscal.debtCost,.1325);
});

test('outliers, loss, unknown jurisdiction, missing interest and debt-free edge cases',()=>{
 const run=(fields,extra={})=>waccEstimate({...base,...extra,waccAccounts:{balanceDate:date,flowDate:date,flowBasis:'TTM',debt:100,tax:2,pretax:10,interest:1,...fields}});
 near(run({tax:-5}).tax,0); near(run({tax:100}).tax,.35);
 near(run({pretax:-1}).tax,.25); near(run({pretax:0},{country:'Netherlands'}).tax,.258);
 near(run({tax:null},{country:'United States'}).tax,.21);
 assert.equal(run({tax:null},{country:'Unknown'}).taxBenchmark.source,null);
 near(taxReference('Switzerland').rate,.19607821);
 near(run({interest:1}).debtCost,.0325); near(run({interest:0}).debtCost,.0325);
 near(run({interest:90}).debtCost,.1325); near(run({interest:null}).debtCost,.0475);
 near(run({debt:0,interest:90}).debtCost,0); near(run({debt:0,interest:90}).rate,.0667);
 assert.equal(run({flowDate:'2026-03-31'}).interest,null);
});

test('equity and borrowing benchmarks respect currency even for banks and cross listings',()=>{
 const dual={...base,quote:{currency:'USD',price:20,marketCap:1000},fx:{from:'USD',to:'EUR',at:date,rate:.9}};
 assert.equal(waccEstimate(dual).rate,null); near(waccEstimate(dual).riskFree,.049);
 near(waccEstimate(dual,'','cashFlow').riskFree,.0325); near(waccEstimate(dual,'','cashFlow').equity,900);
 const bank={...dual,industry:'Banks - Diversified'};
 near(waccEstimate(bank).equityCost,.0832); near(waccEstimate(bank,'','cashFlow').equityCost,.0667);
 assert.equal(defaultValuation(bank).rate,'6.67');
 const old={...bank,riskFreeRates:undefined,treasury:{sourceID:'treasury',yield:5,date}};
 assert.equal(defaultValuation(old).rate,''); // no EUR benchmark in this file
});

test('personal equity return prices DCF, Gordon, growth sensitivity and reverse DCF at the entered rate',()=>{
 const report={...base,industry:'Insurance - Diversified'};
 const inputs={...defaultValuation(report),personalEquityRate:true,rate:'8.125',growth:'3',dividend:'1.5'};
 const price=calculateValuation(report,inputs);
 near(price.rate,.08125);
 near(calculateValuation(report,inputs,'gordon').perShare,1.5*1.02/(.08125-.02));
 near(reverseGrowth(report,inputs,price.perShare),.03);
 const grid=valuationSensitivity(report,inputs);
 assert.deepEqual(grid.rates,[8.125]);
 near(grid.rows[2].cells[0].perShare,price.perShare);
 assert.equal(calculateValuation(report,{...inputs,rate:''}).error,'Enter a personal cost of equity.');
 assert.ok(calculateValuation(report,{...inputs,rate:'2'}).error);
 near(calculateValuation({...report,riskFreeRates:{}},inputs).perShare,price.perShare);
 near(calculateValuation(report,{...inputs,personalEquityRate:false}).rate,.0667);
});

test('personal equity return survives saving and refresh even if it equals original CAPM, and resets all scenario rates',()=>{
 const report={...base,sector:'Banks'},nextReport={...report,beta:1};
 const defaults=defaultValuation(report),manual={...defaults,personalEquityRate:true,growth:'3'};
 const scenarios=valuationScenarios(manual,report);
 scenarios[0].growth='-1';
 const options={method:'dcf',valuationInputs:manual,valuationScenarios:scenarios};
 const loaded=restoreValuation(report,JSON.parse(JSON.stringify(options)));
 assert.equal(loaded.inputs.personalEquityRate,true);
 const refresh=refreshedValuationOptions({report,options},nextReport);
 assert.equal(refresh.valuationInputs.rate,'6.67');
 assert.ok(refresh.valuationScenarios.every(row=>row.rate==='6.67'&&row.personalEquityRate));
 const reset=defaultValuation(nextReport);
 const following=updateValuationScenarios(refresh.valuationScenarios,refresh.valuationInputs,reset,nextReport);
 assert.ok(following.every(row=>row.rate==='8.25'&&!row.personalEquityRate));
 assert.equal(following[0].growth,'-1');
});

test('only a separately edited bank scenario keeps its own rate after changing the main assumption',()=>{
 const bank={...base,industry:'Banks - Regional'};
 const main={...defaultValuation(bank),growth:'3'};
 const original=valuationScenarios(main,bank);
 original[0]={...original[0],personalEquityRate:true,independentEquityRate:true,rate:'9.75'};
 const changed={...main,personalEquityRate:true,rate:'8'};
 const scenarios=updateValuationScenarios(original,main,changed,bank);
 const options={method:'dcf',valuationInputs:changed,valuationScenarios:scenarios};
 const loaded=restoreValuation(bank,JSON.parse(JSON.stringify(options)));
 assert.deepEqual(loaded.scenarios.map(s=>s.rate),['9.75','8','8']);
 near(calculateValuation(bank,loaded.scenarios[0]).rate,.0975);
 const refreshed=refreshedValuationOptions({report:bank,options},{...bank,beta:2});
 assert.deepEqual(refreshed.valuationScenarios.map(s=>s.rate),['9.75','8','8']);
 assert.ok(valuationScenarios(changed,bank).every(s=>s.rate==='8'&&!s.independentEquityRate));
});
