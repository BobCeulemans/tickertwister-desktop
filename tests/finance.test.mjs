import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeFacts,qualityScore,div,cagr} from '../web/finance.mjs';
const annual=(val,end='2025-12-31',filed='2026-02-01')=>({val,start:end.slice(0,4)+'-01-01',end,filed,form:'10-K',accn:'0000000000-26-000001'});
function facts(){return {entityName:'Test',cik:1,facts:{'us-gaap':{Revenues:{units:{USD:[annual(100),annual(90,'2024-12-31')]}},NetIncomeLoss:{units:{USD:[annual(10),annual(8,'2024-12-31')]}},Assets:{units:{USD:[{...annual(80),start:undefined}]}},StockholdersEquity:{units:{USD:[{...annual(40),start:undefined}]}}}}};}
test('zero and negative denominators do not generate misleading ratios',()=>{assert.equal(div(1,0),null);assert.equal(div(1,-1),null);assert.equal(div(null,2),null);assert.equal(div(0,2),0);});
test('score excludes missing values and distinguishes missing from zero',()=>{const missing=qualityScore([{end:'2025-12-31'}]);assert.equal(missing.value,null);assert.equal(missing.available,0);const zero=qualityScore([{end:'2025-12-31',fcf:0}]);assert.equal(zero.available,1);assert.equal(zero.value,0);assert.equal(zero.weight,9);});
test('annual normalization ignores quarters and chooses latest restatement',()=>{const f=facts();f.facts['us-gaap'].Revenues.units.USD.push({...annual(500),start:'2025-10-01',form:'10-Q'},annual(110,'2025-12-31','2026-03-01'));const r=normalizeFacts(f,'TEST');assert.equal(r.years.at(-1).revenue,110);assert.equal(r.years.at(-1).roe,.25);assert.equal(r.years.at(-1).debt,null);assert.equal(r.provenance.find(p=>p.field==='revenue'&&p.end==='2025-12-31').filed,'2026-03-01');});
test('annual data is not substituted from other currencies or IFRS',()=>{const f=facts();for(const x of Object.values(f.facts['us-gaap'])){x.units.EUR=x.units.USD;delete x.units.USD;}assert.throws(()=>normalizeFacts(f,'TEST'),/NO_ANNUAL_USD/);assert.throws(()=>normalizeFacts({facts:{'ifrs-full':{}}},'TEST'),/UNSUPPORTED_GAAP/);});
test('CAGR uses elapsed years and positive endpoints',()=>{assert.equal(cagr([{end:'2024-01-01',fcf:-1},{end:'2025-01-01',fcf:100}],'fcf'),null);assert.ok(Math.abs(cagr([{end:'2021-01-01',fcf:100},{end:'2025-01-01',fcf:146.41}],'fcf')-.1)<1e-9);});
import {businessExcerpt} from '../web/models.mjs';
test('printable business descriptions fit the report excerpt',()=>{
 assert.ok(businessExcerpt('A long description. '.repeat(100)).length<=620);
});
