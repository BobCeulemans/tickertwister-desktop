import {translator} from '../web/i18n.mjs';
import test from 'node:test';import assert from 'node:assert/strict';
import {decimalInput,notePages,statuses} from '../web/presentation.mjs';
import {parseDesk,emptyNotes} from '../web/research.mjs';
import {normalizeFacts} from '../web/finance.mjs';import {makeSaved} from '../web/saved.mjs';
test('percent inputs remove floating-point artefacts while retaining blanks',()=>{assert.equal(decimalInput(5.700000000000001),'5.70');assert.equal(decimalInput(''),'');assert.equal(decimalInput(-.125),'-0.13');});
test('long research notes paginate without losing words or overflowing line budget',()=>{const text=Array.from({length:2200},(_,i)=>'word'+i).join(' ');const pages=notePages(text);assert.ok(pages.length>1);assert.ok(pages.every(p=>p.split('\n').length<=32));assert.deepEqual(pages.join('\n').split(/\s+/),text.split(/\s+/));});
test('legacy pass status migrates and all four new statuses roundtrip',()=>{
 const annual={val:100,start:'2025-01-01',end:'2025-12-31',filed:'2026-02-01',form:'10-K',accn:'0000000000-26-000001'};
 const report={...normalizeFacts({entityName:'Test',cik:1,facts:{'us-gaap':{Revenues:{units:{USD:[annual]}}}}},'TEST'),quote:null};
 const saved=makeSaved(report,{method:'dcf',rate:'12',growth:'5',terminal:'2',price:'',cashFlow:''});
 for(const status of ['pass',...statuses.map(s=>s[0])]){const d=parseDesk({format:'tickertwister-research',version:1,entries:[{saved,notes:{...emptyNotes(),status}}]});assert.equal(d.entries[0].notes.status,status==='pass'?'hard':status);}
});

test('compact amounts retain sign, two decimals and local scale; market value excludes user assumptions',async()=>{
 const {shortAmount,marketValue}=await import('../web/presentation.mjs');const n=v=>v.toFixed(2),nl=translator('nl'),en=translator('en');
 assert.equal(shortAmount(17587300000,n,nl),'17.59 mrd');assert.equal(shortAmount(-17587300000,n,en),'-17.59 bln');assert.equal(shortAmount(null,n,nl),'—');
 assert.equal(marketValue({quote:{price:100},valuationShares:200,price:5}),20000);assert.equal(marketValue({quote:{price:100}}),null);
});
import {tableScale,reminderLabel} from '../web/presentation.mjs';
test('table uses a shared scale suitable for typical company figures',()=>{
 const t=translator('en');
 assert.deepEqual(tableScale([null,0,38e6,60e6,900e6],t),[1e6,'million']);
 assert.deepEqual(tableScale([30e9,90e9,200e9],t),[1e9,'billion']);
 assert.deepEqual(tableScale([38000,60000],t),[1e3,'thousand']);
 assert.equal(reminderLabel('2026-11-07T14:35'),'07/11/2026 · 14:35');
 assert.equal(reminderLabel('2026-11-07'),'07/11/2026');
});

test('archive timestamps use the Mac timezone, including summer time',async()=>{
 const {archiveDateTime}=await import('../web/presentation.mjs');
 globalThis.__ttTimeZone='Europe/Brussels';
 try{assert.match(archiveDateTime('2026-11-08T12:30:00Z','nl'),/13:30/);assert.match(archiveDateTime('2026-07-08T12:30:00Z','nl'),/14:30/);}finally{delete globalThis.__ttTimeZone;}
});
