// SPDX-License-Identifier: AGPL-3.0-only
import test from 'node:test';
import assert from 'node:assert/strict';
import {sectorModel} from '../web/valuationSector.mjs';
import {calculateValuation, defaultValuation, historicalOwnerEarnings, historicalGrowthBand, valuationGrowthBand, valuationSources, valuationScenarios, previousEarningsDefaults} from '../web/valuation.mjs';
import {restoreValuation} from '../web/saved.mjs';

const report={currency:'USD',quoteCurrency:'USD',fetchedAt:'2026-11-25',beta:1,treasury:{date:'2026-11-24',yield:4.5,sourceID:'treasury',currency:'USD'},valuationShares:10,valuationData:{netDebt:200}};
const annual=(end,income,extra={})=>({end,income,da:10,capex:14,revenue:income*4,workingCapitalCashEffect:0,...extra});
const close=(actual,expected)=>assert.ok(Math.abs(actual-expected)<1e-8,`${actual} != ${expected}`);

test('financial-sector activity selects direct equity only for banking and underwriting',()=>{
 for(const [sector,industry,model] of [['Financial Services','Banks - Regional','bank'],['Financials','Insurance - Diversified','insurance'],['Financial Services','Insurance Brokers','financial'],['Financial Services','Credit Services','financial'],['Technology','Transaction & Payment Processing Services','financial'],['Consumer Defensive','Confectioners','other'],['','','other']]){
  assert.equal(sectorModel({sector,industry}),model);
 }
 const row=annual('2025-12-31',23000,{da:900,capex:1300,workingCapitalCashEffect:-18000});
 const r={...report,sector:'Financial Services',industry:'Credit Services',years:[row]};
 assert.equal(valuationSources(r).ownerEarnings,22600);
 assert.equal(valuationSources(r).workingCapitalCashEffect,-18000);
 const missing=historicalOwnerEarnings({...r,years:[{...row,capex:null,workingCapitalCashEffect:null}]})[0];
 assert.deepEqual(missing.assumedZero,['Capital expenditure']);
 assert.equal(missing.ownerEarnings,23900);
 const bank={...r,industry:'Banks - Regional'};
 assert.equal(valuationSources(bank).ownerEarnings,23000);
 assert.deepEqual(historicalOwnerEarnings({...bank,years:[{...row,da:null,capex:null}]})[0].assumedZero,[]);
 const inputs={...defaultValuation(bank),growth:'3',rate:'9.5'};
 const v=calculateValuation(bank,inputs);
 assert.equal(v.error,undefined);
 close(v.equityValue,v.projectionPV+v.terminalPV); assert.equal(v.enterpriseValue,null); assert.equal(v.netDebt,null);
 assert.equal(v.perShare,calculateValuation(bank,{...inputs,netDebt:'300000'}).perShare);
});

test('normalisation uses latest three consecutive fiscal years only when deviation exceeds 30%',()=>{
 const source=(years)=>valuationSources({...report,years:years.map(([end,income])=>annual(end,income))});
 const low=source([['2023-12-31',100],['2024-12-31',100],['2025-12-31',40]]);
 assert.equal(low.ownerEarnings,40); assert.equal(low.average,80); assert.equal(low.starting,80); assert.ok(low.normalized);
 const equality=source([['2023-12-31',85],['2024-12-31',85],['2025-12-31',130]]);
 assert.equal(equality.starting,130); assert.equal(equality.normalized,false);
 assert.equal(source([['2022-12-31',100],['2024-12-31',100],['2025-12-31',40]]).starting,40);
 assert.equal(source([['2023-12-31',100],['2024-12-31',null],['2025-12-31',40]]).average,null);
});

test('growth averages independent available signals and falls back to earnings on two-sided disagreement',()=>{
 const r={...report,years:[annual('2020-12-31',100),annual('2024-12-31',100*1.1**4,{revenue:400*1.13**4,workingCapitalCashEffect:100*1.041**4-100*1.1**4})]};
 const blended=historicalGrowthBand(r);
 close(blended.suggested,(.1+.13+.041)/3); assert.equal(blended.diverges,false);
 const bank=historicalGrowthBand({...r,sector:'Banks'});
 close(bank.suggested,.13); // Financial companies start from historical revenue growth.
 const poorCash=structuredClone(r); poorCash.years[1].workingCapitalCashEffect=-95;
 const fallback=historicalGrowthBand(poorCash);
 assert.ok(fallback.historical<0); assert.equal(fallback.diverges,true); close(fallback.suggested,.1);
 const missing=structuredClone(r); missing.years.forEach(row=>row.income=null);
 const band=valuationGrowthBand(missing,{...defaultValuation(missing),ownerEarnings:'1'});
 assert.equal(band.historical,null); close(band.suggested,.13); assert.equal(band.strict,'10'); assert.equal(band.moderate,'12'); assert.ok(band.moderateValue>band.strictValue);
});

test('Preview 5 old automatic earnings and scenarios update in-memory but independent user edits survive',()=>{
 const r={...report,sector:'Financial Services',industry:'Credit Services',years:[
  annual('2023-12-31',200e6,{workingCapitalCashEffect:-5e6}),annual('2024-12-31',215e6,{workingCapitalCashEffect:-40e6}),annual('2025-12-31',235e6,{workingCapitalCashEffect:-180e6})]};
 const fresh=defaultValuation(r);
 const previous={...fresh,...previousEarningsDefaults(r)}; delete previous.earningsMethod;
 assert.notEqual(previous.growth,fresh.growth); assert.notEqual(previous.ownerEarnings,fresh.ownerEarnings);
 const scenarios=valuationScenarios(previous,r); scenarios[2].growth='7.25';
 const options={valuationInputs:previous,valuationScenarios:scenarios}, untouched=structuredClone(options);
 const next=restoreValuation(r,options);
 assert.equal(next.inputs.growth,fresh.growth); assert.equal(next.inputs.ownerEarnings,fresh.ownerEarnings);
 assert.equal(next.scenarios[1].ownerEarnings,fresh.ownerEarnings); assert.equal(next.scenarios[2].growth,'7.25');
 assert.equal(restoreValuation(r,{valuationInputs:{...previous,ownerEarnings:'230.5',growth:'5'}}).inputs.ownerEarnings,'230.5');
 assert.deepEqual(options,untouched); assert.deepEqual(restoreValuation(r,{valuationInputs:next.inputs,valuationScenarios:next.scenarios}).inputs,next.inputs);
});
