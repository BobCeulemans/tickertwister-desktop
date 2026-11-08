import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeFacts,valuation,qualityScore,div,cagr} from '../web/finance.mjs';
const report={years:[{end:'2025-12-31',fcf:100,shares:10,dps:2}],quote:null};
const annual=(val,end='2025-12-31',filed='2026-02-01')=>({val,start:end.slice(0,4)+'-01-01',end,filed,form:'10-K',accn:'0000000000-26-000001'});
function facts(){return {entityName:'Test',cik:1,facts:{'us-gaap':{Revenues:{units:{USD:[annual(100),annual(90,'2024-12-31')]}},NetIncomeLoss:{units:{USD:[annual(10),annual(8,'2024-12-31')]}},Assets:{units:{USD:[{...annual(80),start:undefined}]}},StockholdersEquity:{units:{USD:[{...annual(40),start:undefined}]}}}}};}
test('constant equity cash flow perpetuity matches closed-form DCF',()=>{const v=valuation(report,{rate:.1,growth:0,terminal:0});assert.ok(Math.abs(v.total-1000)<1e-8);assert.ok(Math.abs(v.perShare-100)<1e-8);assert.equal(v.rows.length,10);});
test('Gordon uses next-year dividend and required return minus growth',()=>{const v=valuation(report,{method:'gordon',rate:.1,terminal:.02});assert.equal(v.perShare,25.5);assert.equal(v.total,255);});
test('invalid terminal assumptions rejected; negative cash flow not valued',()=>{assert.throws(()=>valuation(report,{rate:.02,terminal:.03}),/INVALID_ASSUMPTIONS/);assert.throws(()=>valuation(report,{rate:NaN}),/INVALID_ASSUMPTIONS/);assert.equal(valuation({...report,years:[{...report.years[0],fcf:-1}]}).error,'NO_CASHFLOW');});
test('missing dividends, shares and market prices remain missing',()=>{assert.equal(valuation({...report,years:[{...report.years[0],dps:null}]},{method:'gordon'}).error,'NO_DIVIDEND');assert.equal(valuation({...report,years:[{...report.years[0],shares:null}]}).error,'NO_CASHFLOW');assert.equal(valuation(report).margin,null);});
test('price override and margin of safety use equity value consistently',()=>{assert.ok(Math.abs(valuation(report,{rate:.1,growth:0,terminal:0,price:80}).margin-.2)<1e-10);});
test('zero and negative denominators do not generate misleading ratios',()=>{assert.equal(div(1,0),null);assert.equal(div(1,-1),null);assert.equal(div(null,2),null);assert.equal(div(0,2),0);});
test('score excludes missing values and distinguishes missing from zero',()=>{const missing=qualityScore([{end:'2025-12-31'}]);assert.equal(missing.value,null);assert.equal(missing.available,0);const zero=qualityScore([{end:'2025-12-31',fcf:0}]);assert.equal(zero.available,1);assert.equal(zero.value,0);assert.equal(zero.weight,9);});
test('annual normalization ignores quarters and chooses latest restatement',()=>{const f=facts();f.facts['us-gaap'].Revenues.units.USD.push({...annual(500),start:'2025-10-01',form:'10-Q'},annual(110,'2025-12-31','2026-03-01'));const r=normalizeFacts(f,'TEST');assert.equal(r.years.at(-1).revenue,110);assert.equal(r.years.at(-1).roe,.25);assert.equal(r.years.at(-1).debt,null);assert.equal(r.provenance.find(p=>p.field==='revenue'&&p.end==='2025-12-31').filed,'2026-03-01');});
test('annual data is not substituted from other currencies or IFRS',()=>{const f=facts();for(const x of Object.values(f.facts['us-gaap'])){x.units.EUR=x.units.USD;delete x.units.USD;}assert.throws(()=>normalizeFacts(f,'TEST'),/NO_ANNUAL_USD/);assert.throws(()=>normalizeFacts({facts:{'ifrs-full':{}}},'TEST'),/UNSUPPORTED_GAAP/);});
test('CAGR uses elapsed years and positive endpoints',()=>{assert.equal(cagr([{end:'2024-01-01',fcf:-1},{end:'2025-01-01',fcf:100}],'fcf'),null);assert.ok(Math.abs(cagr([{end:'2021-01-01',fcf:100},{end:'2025-01-01',fcf:146.41}],'fcf')-.1)<1e-9);});
test('Yahoo DCF uses actual FCFE and quote currency must match',()=>{const r={schema:'yahoo39-v1',currency:'EUR',years:[{fcf:100,fcfe:80,shares:10}],valuationShares:20,quote:{price:10,currency:'USD'}};const v=valuation(r,{rate:.1,growth:0,terminal:0});assert.ok(Math.abs(v.perShare-40)<1e-8);assert.equal(v.margin,null);});
test('Gordon rejects dividend currency mismatch',()=>{assert.equal(valuation({schema:'yahoo39-v1',currency:'EUR',years:[{}],dividendPerShare:2,dividendCurrency:'USD'},{method:'gordon'}).error,'CURRENCY_MISMATCH');});
import {multipleValuation,multipleDefaults,scenarioDefaults,businessExcerpt} from '../web/models.mjs';
test('FCFE multiple model matches original ten-year formula and responds to assumptions',()=>{
 const r={currency:'EUR',valuationShares:10,quote:{price:90,currency:'EUR'},years:[{fcfe:100}],originalValuation:{fcfe:100,rate:.12,growth:.05,multiple:15}};
 const defaults=multipleDefaults(r),v=multipleValuation(r,defaults);
 const expected=Array.from({length:10},(_,i)=>100*1.05**(i+1)/1.12**(i+1)).reduce((a,b)=>a+b,0)+100*1.05**10/1.12**10*15;
 assert.ok(Math.abs(v.perShare-expected/10)<1e-9);assert.equal(v.margin,1-90/v.perShare);
 assert.ok(multipleValuation(r,{...defaults,rate:'20'}).perShare<v.perShare);
 assert.equal(multipleValuation({...r,quote:{price:90,currency:'USD'}},defaults).margin,null);
 for(const key of ['rate','growth','multiple','cashFlow'])assert.equal(multipleValuation(r,{...defaults,[key]:''}).error,'INVALID_ASSUMPTIONS');
});
test('scenario defaults use historical growth without inventing missing FCFE',()=>{
 const r={schema:'yahoo39-v1',years:[{end:'2021-01-01',fcfe:100},{end:'2025-01-01',fcfe:146.41}]};
 assert.equal(scenarioDefaults(r).growth,'10.00');assert.equal(scenarioDefaults(r).rate,'12');assert.equal(scenarioDefaults({...r,years:[{end:'2025-01-01',fcfe:null}]}).cashFlow,'');
 assert.ok(businessExcerpt('A long description. '.repeat(100)).length<=620);
});
import {cashFlowBasis} from '../web/models.mjs';
test('missing borrowing yields an explicitly identified FCF scenario, without changing source data',()=>{
 const r={schema:'yahoo39-v1',currency:'EUR',valuationShares:10,years:[{end:'2025-12-31',fcfe:null,fcf:60e6,netBorrowings:null}]};
 assert.equal(cashFlowBasis(r).kind,'fcf-proxy');assert.equal(multipleDefaults(r).cashFlow,'60');
 assert.ok(multipleValuation(r,multipleDefaults(r)).perShare>0);
 assert.equal(r.years[0].fcfe,null);assert.equal(r.years[0].netBorrowings,null);
 assert.equal(cashFlowBasis({...r,years:[{fcfe:-10,fcf:60}]}).value,-10);
 assert.equal(cashFlowBasis({...r,years:[{fcfe:null,fcf:null}]}).kind,'missing');
});

test('reported Yahoo growth is neither capped nor floored in FCFE defaults',()=>{
 const r={currency:'USD',valuationShares:10,years:[{fcfe:100}],originalValuation:{growth:.15}};
 for(const [growth,expected] of [[.271,'27.10'],[-.074,'-7.40'],[1.2,'120.00'],[0,'0.00']]){
  const inputs=multipleDefaults({...r,revenueGrowth:growth});assert.equal(inputs.growth,expected);
  assert.ok(multipleValuation(r,inputs).perShare>0);
 }
 assert.equal(multipleDefaults({...r,originalValuation:{error:'missing'}}).growth,'0.00');
 assert.equal(multipleDefaults(r).growth,'15.00'); // Older snapshots keep their available assumption.
});
test('DCF starting CAGR keeps large positive and negative growth; financial limits remain enforced',()=>{
 for(const [end,expected] of [[285.61,'30.00'],[40.96,'-20.00']]){
  const r={schema:'yahoo39-v1',years:[{end:'2021-01-01',fcfe:100},{end:'2025-01-01',fcfe:end}]};
  assert.equal(scenarioDefaults(r).growth,expected);
 }
 assert.equal(scenarioDefaults({years:[],revenueGrowth:.28}).growth,'28.00');
 assert.ok(valuation(report,{growth:1.2}).perShare>0);
 assert.throws(()=>valuation(report,{growth:-1}),/INVALID_ASSUMPTIONS/);
 assert.throws(()=>valuation(report,{growth:1e50}),/INVALID_ASSUMPTIONS/);
 const r={currency:'USD',valuationShares:10,years:[{fcfe:100}]},inputs=multipleDefaults(r);
 assert.equal(multipleValuation(r,{...inputs,growth:'-100'}).error,'INVALID_ASSUMPTIONS');
 assert.equal(multipleValuation(r,{...inputs,growth:'1e50'}).error,'INVALID_ASSUMPTIONS');
});
