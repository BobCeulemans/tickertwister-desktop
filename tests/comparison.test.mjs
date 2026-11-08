import {translator} from '../web/i18n.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {periods,commonPeriods,metrics,interpret} from '../web/comparison.mjs';
const q=(key,end,extra={})=>({periodKey:key,periodType:'quarter',end,revenue:100,income:10,equity:200,assets:400,debt:28,liabilities:120,cfo:15,capex:5,netBorrowings:1,eps:1,...extra});
const quarters=[q('2025-Q4','2025-12-31'),q('2026-Q1','2026-03-31'),q('2026-Q2','2026-06-30'),q('2026-Q3','2026-09-30')];
test('different fiscal ends never masquerade as same reporting period',()=>assert.equal(commonPeriods([{years:[{end:'2025-12-31'}]},{years:[{end:'2026-06-30'}]}]).length,0));
test('TTM sums flows and retains closing balances; missing values are not zeros',()=>{const p=periods({years:[],quarters}).get('TTM:2026-Q3');assert.equal(p.income,40);assert.equal(p.assets,400);assert.equal(p.fcf,40);assert.equal(p.fcfe,44);assert.equal(p.rd,null);assert.equal(metrics.find(m=>m.key==='roa').value(p),.1);});
test('incomplete and duplicate quarters do not form TTM',()=>{assert.equal([...periods({quarters:quarters.slice(1)}).keys()].filter(k=>k.startsWith('TTM')).length,0);assert.equal([...periods({quarters:[...quarters.slice(1),quarters[1]]}).keys()].filter(k=>k.startsWith('TTM')).length,0);});
test('matching calendar quarter allows real fiscal week-end dates to remain visible',()=>{const reports=[{quarters},{quarters:quarters.map(q=>({...q,end:q.end==='2026-09-30'?'2026-09-26':q.end}))}];const p=commonPeriods(reports)[0];assert.equal(p.key,'TTM:2026-Q3');assert.equal(p.rows[1].end,'2026-09-26');});
test('book liabilities and interest-bearing debt definitions remain separate',()=>{const y=quarters[0];const value=k=>metrics.find(m=>m.key===k).value(y);assert.equal(value('debtEquity'),.14);assert.equal(value('liabilitiesEquity'),.6);assert.equal(value('adjustedDebt'),null);assert.equal(metrics.find(m=>m.key==='adjustedDebt').value({...y,treasuryStock:-100}),.4);});
test('quarter metrics are not annualised; nonpositive denominator not misleading',()=>{const m=metrics.find(m=>m.key==='roa');assert.equal(m.value(quarters[0]),.025);assert.equal(m.value({...quarters[0],assets:0}),null);});
test('year-on-year compares same quarter rather than previous quarter',()=>{const p=periods({quarters:[q('2025-Q3','2025-09-30',{eps:2}),...quarters]});assert.equal(p.get('Q:2026-Q3').epsYoY,-.5);assert.equal(p.get('Q:2026-Q2').epsYoY,null);});
test('interpretation identifies its rule-based basis and missing figures',()=>{const r={symbol:'TEST',currency:'USD',quarters};const p=commonPeriods([r,r])[0];const text=interpret([r,r],p,translator('en'),String,v=>v===null?'—':String(v*100)+'%').join(' ');assert.match(text,/rule-based/);assert.match(text,/metrics unavailable/);assert.match(text,/not a language model/);});
import {maximumHistory} from '../web/comparison.mjs';
const annual=(end,value)=>({end,revenue:value,income:value/10,assets:200,equity:100,debt:20,cfo:20,capex:5,eps:value/100,retained:value});
test('maximum history selects equal-length approximate fiscal windows and uses annual means',()=>{
 const reports=[{years:[2022,2023,2024,2025].map((v,i)=>annual(v+'-09-30',100+i*10))},{years:[2023,2024,2025,2026].map((v,i)=>annual(v+'-06-30',100+i*10))},{years:[2022,2023,2024,2025].map((v,i)=>annual(v+'-12-31',100+i*10))}];
 const p=maximumHistory(reports);assert.equal(p.observations,3);assert.equal(p.rows[0].revenue,120);assert.equal(p.rows[0].income,12);assert.equal(p.rows[0].assets,200);assert.equal(metrics.find(m=>m.key==='roa').value(p.rows[0]),.06);assert.equal(p.rows[0].periodStart,'2023-09-30');assert.equal(p.rows[1].end,'2025-06-30');assert.equal(p.rows[0].rd,undefined);
});
test('long-term windows cannot bridge missing fiscal years or average missing values',()=>{
 const years=[annual('2023-12-31',100),annual('2025-12-31',120)];assert.equal(maximumHistory([{years},{years}]),null);
 const complete=[annual('2024-12-31',100),{...annual('2025-12-31',120),income:null}];assert.equal(maximumHistory([{years:complete},{years:complete}]).rows[0].income,null);
});

test('one company has selectable annual and TTM periods',()=>{const one={years:[{end:'2025-12-31'}],quarters};assert.ok(commonPeriods([one]).some(p=>p.key==='TTM:2026-Q3'));assert.ok(commonPeriods([one]).some(p=>p.key==='FY:2025-12-31'));});
