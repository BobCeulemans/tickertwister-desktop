import test from 'node:test';import assert from 'node:assert/strict';
import {financialInput,apiRequest,parseResponse,outputSchema} from '../web/aic.mjs';
const r={symbol:'TEST',name:'Test',currency:'USD',notes:'PRIVATE NOTE',apiKey:'SECRET',summary:'PRIVATE SUMMARY'};
const row={end:'2025-12-31',income:10,equity:100,debt:14,assets:200,revenue:100};
const p={key:'FY:2025-12-31',rows:[row,{...row,equity:-1}]};
test('AI input is allowlisted and excludes notes, keys, summaries and user valuations',()=>{const s=JSON.stringify(financialInput([r,r],p,'nl'));for(const secret of ['PRIVATE','SECRET','apiKey','summary','quotePrice','modelPerShare','aiAssumptions'])assert.ok(!s.includes(secret));});
test('AI preserves ratio fractions, missingness and dates',()=>{const d=financialInput([r,r],p,'en');assert.equal(d.companies[0].metrics.debtEquity,.14);assert.equal(d.companies[1].metrics.debtEquity,null);assert.equal(d.companies[0].metrics.cfo,null);assert.equal(d.companies[0].end,'2025-12-31');});
test('AI rejects invalid company count and row mismatch',()=>{assert.throws(()=>financialInput([r],p,'nl'));assert.throws(()=>financialInput([r,r],{rows:[]},'nl'));});
test('request is bounded, stateless, tool-free and structured',()=>{const q=apiRequest(financialInput([r,r],p,'nl'));assert.equal(q.max_output_tokens,8192);assert.equal(q.store,false);assert.equal(q.tools,undefined);assert.equal(q.text.format.strict,true);assert.equal(q.reasoning.effort,'medium');});
const sections=Object.fromEntries(Object.keys(outputSchema.properties).map(k=>[k,'Test observation']));
const response={status:'completed',model:'test-model',usage:{input_tokens:123,output_tokens:456},output:[{type:'message',content:[{type:'output_text',text:JSON.stringify(sections)}]}]};
test('response parser retains usage and structure',()=>{const r=parseResponse(response);assert.deepEqual(r.sections,sections);assert.equal(r.usage.input_tokens,123);});
test('incomplete, refused, oversized and malformed output never become a conclusion',()=>{assert.throws(()=>parseResponse({...response,status:'incomplete'}));assert.throws(()=>parseResponse({...response,output:[{content:[{type:'refusal'}]}]}));for(const obj of [{...sections,conclusion:'x'.repeat(1301)},{conclusion:'bad'}])assert.throws(()=>parseResponse({...response,output:[{content:[{type:'output_text',text:JSON.stringify(obj)}]}]}));});
import {translationRequest} from '../web/aic.mjs';
import {archiveKey,readRecord,relevantRecords} from '../web/aiArchiveData.mjs';
test('archive identity ignores language and request day, but distinguishes financial revisions',()=>{const input=financialInput([r,r],p,'nl');assert.equal(archiveKey(input),archiveKey({...input,language:'en',asOf:'2099-01-01'}));assert.notEqual(archiveKey(input),archiveKey({...input,period:'Q:2025-Q4'}));assert.notEqual(archiveKey(input),archiveKey({...input,companies:input.companies.map(c=>({...c,metrics:{income:999}}))}));});
test('archive roundtrip restores paid text and links every compared company',()=>{const raw={id:'test',input:financialInput([r,{...r,symbol:'OTHER'}],p,'nl'),language:'nl',createdAt:'2026-11-05T12:00:00Z',response};const restored=readRecord(JSON.parse(JSON.stringify(raw)));assert.deepEqual(restored.result.sections,sections);assert.equal(relevantRecords([restored],['OTHER']).length,1);assert.equal(relevantRecords([restored],['NONE']).length,0);assert.throws(()=>readRecord({...raw,language:'invalid'}));});
test('translation preserves original text and sends no fresh notes or valuation advice',()=>{const original={input:financialInput([r,r],p,'nl'),result:{sections}};const req=translationRequest(original,'en');assert.deepEqual(JSON.parse(req.input).sections,sections);assert.equal(JSON.parse(req.input).language,'en');assert.match(req.instructions,/Do not add new analysis/);assert.equal(req.max_output_tokens,8192);assert.equal(original.input.language,'nl');});
test('interpretation prompt distinguishes quality from price and avoids table repetition',()=>{const req=apiRequest(financialInput([r,r],p,'nl'));assert.match(req.instructions,/at most six numerical anchors/);assert.match(req.instructions,/EACH company/);assert.match(req.instructions,/No user valuations or share prices are supplied/);});
test('archive identity survives native JSON key reordering',()=>{const input=financialInput([r,r],p,'nl');const reorder=v=>Array.isArray(v)?v.map(reorder):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).reverse().map(([k,v])=>[k,reorder(v)])):v;assert.equal(archiveKey(input),archiveKey(reorder(input)));});

test('single-company input uses one matched row',()=>{const input=financialInput([r],{key:p.key,rows:[row]},'nl');assert.equal(input.companies.length,1);});

import {printRecords} from '../web/aiArchiveData.mjs';
test('printing selects either, both or neither overlapping company comparisons',()=>{const records=[{id:'old',input:{companies:[{symbol:'AAPL'},{symbol:'MSFT'}]}},{id:'new',input:{companies:[{symbol:'AAPL'},{symbol:'KO'}]}}];assert.deepEqual(printRecords(records,['AAPL'],['new']).map(r=>r.id),['new']);assert.equal(printRecords(records,['AAPL'],['old','new']).length,2);assert.equal(printRecords(records,['AAPL'],[]).length,0);assert.equal(printRecords(records,['MSFT'],['new']).length,0);});

import fs from 'node:fs';
import {personalScore} from '../web/weights.mjs';
import {commonPeriods} from '../web/comparison.mjs';
import METHODS from '../web/original-methods.mjs';
const fixture={schema:'yahoo39-v1',symbol:'TEST',name:'Test',currency:'USD',years:[{end:'2025-12-31',income:10,revenue:100}],score:{value:50,coverage:1,available:39,total:39,criteria:METHODS.map(key=>({key,label:key,available:true,weight:2,points:1,factor:.5,formula:'Synthetic test rule'}))}};
test('quality input uses personal weighting, excludes scenario and carries all 39 contributions',()=>{const company={...fixture,aiWeights:{returnOnEquityHistory:5},aiAssumptions:{rate:'SECRET_SCENARIO'},quote:{price:99999999}};const data=financialInput([company],commonPeriods([company])[0],'nl');assert.equal(data.companies[0].quality.activeScore,personalScore(company,company.aiWeights).value);assert.equal(data.companies[0].quality.weighting,'personal');assert.equal(data.companies[0].quality.criteria.length,39);assert.ok(!JSON.stringify(data).includes('SECRET_SCENARIO'));assert.ok(!JSON.stringify(data).includes('99999999'));assert.equal(data.companies[0].valuation,undefined);});
test('default weighting sends original score; all zero weighted criteria give null',()=>{const d=financialInput([fixture],commonPeriods([fixture])[0],'en');assert.equal(d.companies[0].quality.activeScore,fixture.score.value);const zero={...fixture,aiWeights:Object.fromEntries(fixture.score.criteria.map(c=>[c.key,0]))};assert.equal(financialInput([zero],commonPeriods([zero])[0],'nl').companies[0].quality.activeScore,null);});
test('four full reports fit the declared bounded input',()=>{const reports=[fixture,fixture,fixture,fixture];const d=financialInput(reports,commonPeriods(reports)[0],'en');assert.ok(new TextEncoder().encode(JSON.stringify(d)).length<=64000);});

test('annual cash dividends reach AI without substituting earnings payout or user valuation',()=>{
 const company={...fixture,years:[{...fixture.years[0],dividends:12,fcf:9}]};
 const d=financialInput([company],commonPeriods([company])[0],'nl');
 assert.equal(d.companies[0].annualHistory[0].dividends,12);assert.equal(d.companies[0].annualHistory[0].fcf,9);
 assert.match(apiRequest(d).instructions,/dividend cash outflow/);
});

import {cashChecks,aiSettings} from '../web/aic.mjs';
test('annual distribution controls reproduce Meta and Apple cash surplus or shortfall',()=>{
 const meta=cashChecks({end:'2025-12-31',fcf:46.109e9,buybacks:26.248e9,dividends:5.324e9},'USD');
 assert.equal(meta.afterDistributions,14.537e9);assert.ok(meta.distributionCoverage>1);
 const apple=cashChecks({end:'2025-12-31',fcf:98.767e9,buybacks:90.711e9,dividends:15.421e9},'USD');
 assert.equal(apple.afterDistributions,-7.365e9);assert.ok(apple.distributionCoverage<1);assert.ok(apple.dividendCoverage>1);
});
test('cash coverage preserves missing values, zero outflows, negative and zero FCF',()=>{
 assert.equal(cashChecks({fcf:10,dividends:2},'USD').afterDistributions,null);
 assert.equal(cashChecks({fcf:0,dividends:2,buybacks:3},'USD').distributionCoverage,0);
 assert.equal(cashChecks({fcf:-10,dividends:2,buybacks:3},'USD').distributionCoverage,-2);
 assert.equal(cashChecks({fcf:10,dividends:0,buybacks:0},'USD').distributionCoverage,null);
 assert.equal(cashChecks({fcf:10,dividends:0,buybacks:0},'USD').afterDistributions,10);
});
test('all three explicit model selections reach requests with supported reasoning and bounded tokens',()=>{
 for(const model of ['gpt-6-luna','gpt-6.1-sol','gpt-6-astra']) {
  const req=apiRequest({language:'nl'},{model,effort:'high',limit:16384});
  assert.equal(req.model,model);assert.equal(req.reasoning.effort,'high');assert.equal(req.max_output_tokens,16384);
 }
 assert.deepEqual(aiSettings({model:'untrusted',effort:'none',limit:999999}),{model:'gpt-6-luna',effort:'medium',limit:8192});
});

import {selectedAIReports} from '../web/research.mjs';
test('GOOG dossier score and weights cannot be replaced by an open AAPL analysis',()=>{
 const goog={...r,symbol:'GOOG',schema:'yahoo39-v1',score:{value:90,criteria:[{key:'returnOnEquityHistory',available:true,weight:9,points:9,factor:1},{key:'priceToBookValue',available:true,weight:1,points:0,factor:0}],available:35,total:39}};
 const apple={...r,symbol:'AAPL',score:{value:63,criteria:[],available:36,total:39}};
 const entries=[{saved:{report:goog,options:{scoreWeights:{returnOnEquityHistory:2}}}}];
 const selected=selectedAIReports(entries,apple,{scoreWeights:{returnOnEquityHistory:9}});
 assert.equal(selected[0].symbol,'GOOG');assert.equal(selected[0].score.value,90);assert.deepEqual(selected[0].aiWeights,{returnOnEquityHistory:2});
 const data=financialInput(selected,{key:p.key,rows:[row]},'nl');
 assert.equal(data.companies[0].quality.baselineScore,90);assert.equal(data.companies[0].quality.activeScore,1800/19);
 assert.equal(selectedAIReports(entries,goog,{scoreWeights:{returnOnEquityHistory:3}})[0].aiWeights.returnOnEquityHistory,3);
});
