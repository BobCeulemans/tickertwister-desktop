// SPDX-License-Identifier: AGPL-3.0-only
import test from 'node:test';
import assert from 'node:assert/strict';
import {sectorModel} from '../web/valuationSector.mjs';
import {defaultValuation, financialDiscountInput, historicalGrowthBand, previousEarningsDefaults, valuationGrowthBand, valuationScenarios, waccEstimate} from '../web/valuation.mjs';
import {refreshedValuationOptions, restoreValuation} from '../web/saved.mjs';

const year = (end, income, revenue) => ({end,income,revenue,da:20e6,capex:20e6,workingCapitalCashEffect:0});
const report = {symbol:'PYPL',name:'PayPal Holdings, Inc.',sector:'Financial Services',industry:'Credit Services',
 currency:'USD',fetchedAt:'2026-11-27',riskFreeRates:{USD:{currency:'USD',sourceID:'tnx',yield:4.848,date:'2026-11-25'}},
 quote:{currency:'USD',marketCap:48e9,price:58},country:'United States',beta:1.4,valuationShares:830e6,valuationData:{netDebt:3e9},
 waccAccounts:{debt:9e9,balanceDate:'2026-09-30',flowDate:'2026-09-30',flowBasis:'TTM',interest:540e6,pretax:9e9,tax:2e9},
 years:[year('2021-12-31',100e6,500e6),year('2025-12-31',100e6*1.2082**4,500e6*1.0643**4)]};

test('financial growth defaults follow observed revenue growth for payments, banking and underwriting',()=>{
 for(const [symbol,name,industry,expected] of [
  ['PYPL','PayPal Holdings, Inc.','Credit Services','financial'],['MA','Mastercard Incorporated','Credit Services','financial'],
  ['V','Visa Inc.','Credit Services','financial'],['AXP','American Express Company','Credit Services','bank'],
  ['BRK-A','Berkshire Hathaway Inc.','Insurance - Diversified','insurance'],['KBC.BR','KBC Group NV','Banks - Diversified','bank']]){
  const r={...report,symbol,name,industry}, defaults=defaultValuation(r), band=valuationGrowthBand(r,defaults);
  assert.equal(sectorModel(r),expected); assert.equal(band.method,'Revenue growth before caps');
  assert.equal(defaults.growth,'6.43'); assert.equal(band.strict,'6.43'); assert.equal(band.moderate,'6.43');
  assert.equal(band.strictValue,band.moderateValue); assert.ok(band.strictValue>0);
  if(expected==='financial') assert.equal(Number(defaults.rate),waccEstimate(r,'','cashFlow').rate*100);
  else assert.ok(Math.abs(Number(defaults.rate)-11.848)<1e-10);
 }
 assert.equal(sectorModel({...report,symbol:'AXP'}),'financial'); // ticker alone is insufficient
 assert.equal(sectorModel({...report,symbol:'AXP',name:'American Express Global Business Travel Group'}),'financial');
 assert.equal(sectorModel({...report,symbol:'AXP',cik:'0000004962'}),'bank');
});

test('financial growth prefers the full available revenue history and discloses fallback and caps',()=>{
 const evaluate=years=>historicalGrowthBand({...report,years});
 const r=structuredClone(report.years); r[0].income=null;
 assert.equal(evaluate(r).strict,'6.43');
 r[0].revenue=1; assert.equal(evaluate(r).strict,'10'); assert.equal(evaluate(r).moderate,'12');
 r[1].revenue=.1; assert.equal(evaluate(r).strict,'-20');
 const missing=structuredClone(report.years); missing[1].revenue=null;
 assert.equal(evaluate(missing).method,'Net income growth fallback');
 assert.equal(evaluate(missing).strict,'10'); assert.equal(evaluate(missing).moderate,'12');
 missing[0].income=-1; missing[0].da=150e6;
 assert.equal(evaluate(missing).method,'Owner earnings growth fallback');
 missing[0].da=0; assert.equal(evaluate(missing).suggested,null);
 const noWacc={...report,beta:null}; assert.equal(defaultValuation(noWacc).rate,'6');
 const belowMinimum={...report,beta:0}; assert.equal(defaultValuation(belowMinimum).rate,'6');
});

test('opening Preview 6 payments preserves authored assumptions and updates automatic main and scenario rates and growth',()=>{
 const old={...defaultValuation(report),...previousEarningsDefaults(report,'sector-blend-v1'),earningsMethod:'sector-blend-v1',rate:'6'};
 assert.equal(old.growth,'10');
 const scenarios=valuationScenarios(old,report); scenarios[0].rate='16.873'; scenarios[2].growth='17.75';
 const options={method:'dcf',valuationInputs:old,valuationScenarios:scenarios}, pristine=structuredClone(options);
 const next=restoreValuation(report,options), defaults=defaultValuation(report);
 assert.equal(next.inputs.growth,'6.43'); assert.equal(next.inputs.rate,defaults.rate);
 assert.equal(next.scenarios[1].rate,defaults.rate); assert.equal(next.scenarios[2].growth,'17.75');
 assert.equal(next.scenarios[0].growth,'1.43'); assert.equal(next.scenarios[0].rate,'16.873');
 assert.deepEqual(pristine,options);
 const edited=restoreValuation(report,{...options,valuationInputs:{...old,rate:'7.75',growth:'4'}});
 assert.equal(edited.inputs.rate,'7.75'); assert.equal(edited.inputs.growth,'4');
 const personal={...defaults,waccBeta:'1.25',rate:financialDiscountInput(report,'1.25')};
 const revised={...report,riskFreeRates:{USD:{...report.riskFreeRates.USD,yield:4.735}}};
 const refresh=input=>refreshedValuationOptions({report,options:{method:'dcf',valuationInputs:input}},revised).valuationInputs;
 assert.equal(refresh(personal).rate,financialDiscountInput(revised,'1.25'));
 assert.equal(refresh({...personal,rate:'7.9'}).rate,'7.9');
 const sixWacc={...old,waccBeta:'1.25',rate:String(Number(Number(personal.rate).toPrecision(12)))};
 assert.equal(refresh(sixWacc).rate,financialDiscountInput(revised,'1.25'));
});

test('an earlier American Express scenario keeps its explicit discount assumption when switching to a bank model',()=>{
 const axp={...report,symbol:'AXP',name:'American Express Company'};
 const old={...defaultValuation(report),...previousEarningsDefaults(axp,'sector-blend-v1'),earningsMethod:'sector-blend-v1',rate:'6'};
 const scenarios=valuationScenarios(old,axp,false);
 scenarios[0].rate='14.987';
 const options={method:'dcf',valuationInputs:old,valuationScenarios:scenarios};
 const restored=restoreValuation(axp,options);
 assert.equal(restored.inputs.rate,'11.848'); assert.equal(restored.inputs.netDebt,'');
 assert.equal(restored.scenarios[0].rate,'14.987');
 assert.equal(restored.scenarios[0].independentEquityRate,true); assert.equal(restored.scenarios[0].personalEquityRate,true);
 assert.equal(restored.scenarios[2].rate,restored.inputs.rate);
 const withNewBeta=refreshedValuationOptions({report:axp,options},{...axp,beta:.5});
 assert.equal(withNewBeta.valuationScenarios[0].rate,'14.987');
 assert.equal(withNewBeta.valuationScenarios[2].rate,'7.348');
});
