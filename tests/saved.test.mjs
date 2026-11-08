import test from 'node:test';import assert from 'node:assert/strict';
import {normalizeFacts} from '../web/finance.mjs';import {makeSaved,parseSaved} from '../web/saved.mjs';
const annual={val:100,start:'2025-01-01',end:'2025-12-31',filed:'2026-02-01',form:'10-K',accn:'0000000000-26-000001'};
const r={...normalizeFacts({entityName:'Test',cik:1,facts:{'us-gaap':{Revenues:{units:{USD:[annual]}}}}},'TEST'),quote:null};
const options={method:'dcf',rate:'10',growth:'5',terminal:'2.5',price:'',cashFlow:''};
test('saved reports preserve assumptions, dates and missing fields',()=>{const s=parseSaved(JSON.stringify(makeSaved(r,options)));assert.equal(s.report.symbol,'TEST');assert.equal(s.options.rate,'10');assert.equal(s.report.years[0].income,null);assert.ok(s.report.savedAt);});
test('unknown formats and corrupted fields are rejected',()=>{assert.throws(()=>parseSaved('{}'),/INVALID_SAVED/);const s=makeSaved(r,options);assert.throws(()=>parseSaved({...s,version:2}));assert.throws(()=>parseSaved({...s,report:{...r,cik:'<script>'}}));assert.throws(()=>parseSaved({...s,report:{...r,years:[{...r.years[0],income:'text'}]}}));});
test('quality score is recomputed rather than trusting a saved score',()=>{const s=makeSaved({...r,score:{value:100}},options);assert.notEqual(parseSaved(s).report.score.value,100);});
import ORIGINAL_METHODS from '../web/original-methods.mjs';
test('Yahoo reports preserve 39 criteria and currencies and recompute original weighted contributions',()=>{
 const criteria=ORIGINAL_METHODS.map((key,i)=>({key,label:key,heading:key,formula:'test',threshold:'test',available:i!==0,weight:2,points:i===0?null:1}));
 const report={...r,schema:'yahoo39-v1',currency:'EUR',years:r.years.map(y=>({...y,fcfe:null})),originalHistories:[],score:{criteria,value:100}};
 const saved=makeSaved(report,options), restored=parseSaved(JSON.stringify(saved));
 assert.equal(restored.report.score.value,50);assert.equal(restored.report.score.total,39);assert.equal(restored.report.score.available,38);assert.equal(restored.report.currency,'EUR');
 const broken=structuredClone(saved);broken.report.score.criteria.pop();assert.throws(()=>parseSaved(broken),/INVALID_SAVED/);
});
test('multiple model assumptions survive saving and malformed fields are rejected',()=>{
 const multipleInputs={rate:'12',growth:'8',multiple:'17',cashFlow:'1200'};
 const saved=makeSaved(r,{...options,multipleInputs});assert.deepEqual(parseSaved(JSON.stringify(saved)).options.multipleInputs,multipleInputs);
 assert.throws(()=>parseSaved({...saved,options:{...saved.options,multipleInputs:{...multipleInputs,rate:null}}}),/INVALID_SAVED/);
});
test('optional comparison periods survive saving and reject date/key mismatches',()=>{
 const quarters=[{end:'2026-09-26',periodKey:'2026-Q3',periodType:'quarter',income:10,revenue:100,rd:null}];
 const saved=makeSaved({...r,quarters},options);assert.deepEqual(parseSaved(saved).report.quarters,quarters);
 assert.throws(()=>parseSaved({...saved,report:{...saved.report,quarters:[{...quarters[0],periodKey:'2026-Q1'}]}}),/INVALID_SAVED/);
 assert.throws(()=>parseSaved({...saved,report:{...saved.report,quarters:[{...quarters[0],income:'10'}]}}),/INVALID_SAVED/);
});
test('personal weights roundtrip and malformed configurations are rejected',()=>{
 const saved=makeSaved(r,{...options,scoreWeights:{returnOnEquityHistory:2,grossProfitMarginHistory:0}});
 assert.deepEqual(parseSaved(JSON.stringify(saved)).options.scoreWeights,saved.options.scoreWeights);
 assert.throws(()=>parseSaved({...saved,options:{...options,scoreWeights:{returnOnEquityHistory:-2}}}),/INVALID_SAVED/);
 assert.throws(()=>parseSaved({...saved,options:{...options,scoreWeights:{typo:3}}}),/INVALID_SAVED/);
});
test('FX snapshot survives export and malformed conversion metadata is rejected',()=>{
 const fx={from:'USD',to:'JPY',rate:150,at:'2026-11-06T00:00:00Z'},quoteBasis={verified:true,ordinaryPerQuote:1,source:'https://www.sony.com/'};
 const saved=makeSaved({...r,fx,quoteBasis},options);assert.deepEqual(parseSaved(JSON.stringify(saved)).report.fx,fx);
 for(const invalid of [{...fx,rate:0},{...fx,at:'invalid'},{...fx,to:'invalid'}])assert.throws(()=>parseSaved({...saved,report:{...saved.report,fx:invalid}}),/INVALID_SAVED/);
 assert.throws(()=>parseSaved({...saved,report:{...saved.report,quoteBasis:{...quoteBasis,ordinaryPerQuote:0}}}),/INVALID_SAVED/);
});
