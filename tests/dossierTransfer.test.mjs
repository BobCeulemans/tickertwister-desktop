// SPDX-License-Identifier: AGPL-3.0-only
import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeFacts} from '../web/finance.mjs';
import {defaultValuation} from '../web/valuation.mjs';
import {emptyDesk,emptyNotes} from '../web/research.mjs';
import {makeSaved} from '../web/saved.mjs';
import {outputSchema} from '../web/aic.mjs';
import {makeTransfer,parseTransfer,planImport} from '../web/dossierTransfer.mjs';

const sample={val:100,start:'2025-01-01',end:'2025-12-31',filed:'2026-02-01',form:'10-K',accn:'0000000000-26-000001'};
function entry(symbol,thesis){
 const report={...normalizeFacts({entityName:symbol,cik:1,facts:{'us-gaap':{Revenues:{units:{USD:[sample]}}}}},symbol),quote:null};
 const options={method:'dcf',valuationInputs:defaultValuation(report),scratchpad:'Working note'};
 return {saved:makeSaved(report,options),notes:{...emptyNotes(),thesis}};
}
function record(id,symbols){
 const sections=Object.fromEntries(Object.keys(outputSchema.properties).map(k=>[k,'Observation']));
 return {id,language:'nl',input:{period:'LONG:4',companies:symbols.map(symbol=>({symbol}))},createdAt:'2026-11-27T09:10:00Z',response:{status:'completed',model:'model',output:[{content:[{type:'output_text',text:JSON.stringify(sections)}]}]}};
}
const desk={...emptyDesk(),entries:[entry('A','A thesis'),entry('B','B thesis')]};
const a=record('eb67f0bd-e809-4802-9bc0-bf5e91d61016',['A','C']), b=record('2476a59e-6cb3-4d57-bea7-c1ee92e57c10',['B']), orphan=record('3336a59e-6cb3-4d57-bea7-c1ee92e57c10',['D']);
test('selective dossier includes thesis, assumptions, notes and all comparisons involving its ticker',()=>{
 const f=makeTransfer(desk,[a,b,orphan],['A']);assert.equal(f.dossier.entries.length,1);
 assert.equal(f.dossier.entries[0].saved.options.scratchpad,'Working note');assert.equal(f.dossier.entries[0].notes.thesis,'A thesis');
 assert.deepEqual(f.archive.map(r=>r.id),[a.id]);assert.equal(f.archive[0].input.companies[1].symbol,'C');
 assert.deepEqual(parseTransfer(JSON.stringify(f)),f);
});
test('full dossier includes independently archived AI; archives without companies can migrate',()=>{
 const f=makeTransfer(desk,[a,b,orphan],['A','B'],true);assert.equal(f.archive.length,3);
 assert.equal(makeTransfer(emptyDesk(),[orphan],[],true).archive.length,1);
 assert.throws(()=>makeTransfer(emptyDesk(),[],[],true));
});
test('merge keeps local notes by default, explicitly replaces conflicts, and is idempotent',()=>{
 const f=makeTransfer(desk,[a,b],['A','B'],true);
 const local={...emptyDesk(),entries:[entry('A','Already on destination')]};
 const p=planImport(local,f);assert.deepEqual(p.matching,['A']);assert.equal(p.added,1);assert.equal(p.desk.entries[0].notes.thesis,'Already on destination');
 assert.equal(planImport(local,f,true).desk.entries[0].notes.thesis,'A thesis');
 assert.equal(planImport(p.desk,f).added,0);
});
test('unrelated records in a subset, invalid UUID and duplicates are rejected before import',()=>{
 const f=makeTransfer(desk,[a,b],['A']);
 assert.throws(()=>parseTransfer({...f,archive:[b]})); assert.throws(()=>parseTransfer({...f,archive:[{...a,id:'bad'}]}));
 assert.throws(()=>parseTransfer({...f,archive:[a,a]}));
});
