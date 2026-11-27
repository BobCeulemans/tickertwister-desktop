import test from 'node:test';import assert from 'node:assert/strict';
import {diagnostics,parseDesk,emptyNotes} from '../web/research.mjs';
import {defaultValuation,calculateValuation,valuationScenarios,reverseGrowth,valuationSensitivity} from '../web/valuation.mjs';
import {makeSaved} from '../web/saved.mjs';import {normalizeFacts} from '../web/finance.mjs';
const r={currency:'EUR',valuationShares:100,quote:{price:25,currency:'EUR'},years:[{end:'2024-12-31',income:10,cfo:12,assets:100,shares:100,netMargin:.15},{end:'2025-12-31',income:12,cfo:8,fcf:5,assets:100,equity:5,dividends:4,buybacks:2,shares:105,netMargin:.10,currentAssets:10,currentLiabilities:20,operating:15,interest:6}]};
const inputs={...defaultValuation(r),rate:'12',growth:'8',ownerEarnings:'.001',netDebt:'0',terminal:'2'};
test('reverse valuation also recovers negative growth',()=>{
 for(const growth of [-30,0,8,50]){
  const price=calculateValuation(r,{...inputs,growth:String(growth)}).perShare;
  assert.ok(Math.abs(reverseGrowth(r,inputs,price)*100-growth)<1e-7);
 }
});
test('sensitivity and stress scenarios treat higher rates and lower earnings consistently',()=>{
 const grid=valuationSensitivity(r,inputs), scenarios=valuationScenarios(inputs);
 assert.ok(grid.rows[2].cells[0].perShare>grid.rows[2].cells[4].perShare);
 const [bear,base,bull]=scenarios.map(s=>calculateValuation(r,s).perShare);
 assert.ok(bear<base&&base<bull);
});
test('quality checks distinguish missing from zero and use average assets',()=>{const c=diagnostics(r),get=k=>c.find(x=>x.key===k);assert.equal(c.length,8);assert.equal(get('accruals').value,.04);assert.equal(get('conversion').status,'review');assert.equal(get('payout').value,1.2);assert.equal(get('payout').status,'review');assert.equal(get('shares').status,'review');const missing=diagnostics({years:[{}]});assert.ok(missing.every(c=>c.status==='missing'));const zero=diagnostics({years:[{cfo:0,income:10}]});assert.equal(zero.find(c=>c.key==='conversion').status,'review');});
const annual={val:100,start:'2025-01-01',end:'2025-12-31',filed:'2026-02-01',form:'10-K',accn:'0000000000-26-000001'};
const legacy={...normalizeFacts({entityName:'Test',cik:1,facts:{'us-gaap':{Revenues:{units:{USD:[annual]}}}}},'TEST'),quote:null};
const options={method:'dcf',valuationInputs:inputs,valuationScenarios:valuationScenarios(inputs)};
test('research dossier roundtrip retains notes, scenarios and recomputed scores',()=>{const notes={...emptyNotes(),thesis:'Private thesis',disconfirm:'Falling retention',reviewDate:'2026-12-01'},entry={saved:makeSaved(legacy,options),notes};const desk={format:'tickertwister-research',version:1,entries:[entry]};const d=parseDesk(JSON.stringify(desk));assert.equal(d.entries[0].notes.thesis,notes.thesis);assert.deepEqual(d.entries[0].saved.options.valuationScenarios,options.valuationScenarios);assert.throws(()=>parseDesk({...desk,entries:[entry,entry]}),/INVALID_DESK/);assert.throws(()=>parseDesk({...desk,entries:[{...entry,notes:{...notes,status:'purchase'}}]}),/INVALID_DESK/);assert.throws(()=>parseDesk({...desk,version:99}),/INVALID_DESK/);});
test('extreme scenario inputs never produce infinite model values',()=>{assert.ok(calculateValuation(r,{...inputs,growth:'100',ownerEarnings:'1e300'}).error);});
test('local reminder preserves optional hours and minutes through dossier storage',()=>{
 for(const date of ['2026-12-01','2026-12-01T14:35']){
  const d=parseDesk({format:'tickertwister-research',version:1,entries:[{saved:makeSaved(legacy,options),notes:{...emptyNotes(),reviewDate:date}}]});
  assert.equal(d.entries[0].notes.reviewDate,date);
 }
});
