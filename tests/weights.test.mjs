import test from 'node:test';import assert from 'node:assert/strict';
import {personalScore,validWeights} from '../web/weights.mjs';
const report={schema:'yahoo39-v1',score:{criteria:[{key:'returnOnEquityHistory',weight:9,points:9,available:true},{key:'grossProfitMarginHistory',weight:4,points:0,available:true},{key:'netBorrowingsHistory',weight:0,points:0,available:true},{key:'netProfitMarginHistory',weight:6,points:null,available:false}]}};
test('default personal weighting matches original weighted score',()=>{assert.equal(personalScore(report).value,900/13);assert.equal(personalScore(report).custom,false);});
test('weights change importance without changing the original report',()=>{const old=JSON.stringify(report);const s=personalScore(report,{returnOnEquityHistory:2});assert.equal(s.value,1800/22);assert.equal(JSON.stringify(report),old);assert.equal(s.custom,true);});
test('missing and unscored criteria cannot acquire fabricated points',()=>{const s=personalScore(report,{netBorrowingsHistory:100,netProfitMarginHistory:100});assert.equal(s.value,900/13);});
test('all scored criteria disabled produces no score, not zero or infinity',()=>assert.equal(personalScore(report,{returnOnEquityHistory:0,grossProfitMarginHistory:0}).value,null));
test('bad weight files are rejected',()=>{for(const w of [null,[],{unknown:1},{returnOnEquityHistory:-1},{returnOnEquityHistory:'2'},{returnOnEquityHistory:Infinity},{returnOnEquityHistory:101}])assert.equal(validWeights(w),false);});

test('personal exceptions award full effective points without changing source points or coverage',()=>{
 const source=structuredClone(report);
 source.score.criteria[1].points=1.5;
 const original=structuredClone(source);
 const key='grossProfitMarginHistory',weights={[key]:2};
 const result=personalScore(source,weights,[key,'netProfitMarginHistory','netBorrowingsHistory']);
 const row=result.criteria.find(c=>c.key===key);
 assert.equal(result.value,100);
 assert.equal(row.points,1.5);
 assert.equal(row.personalPoints,8);
 assert.equal(row.overridden,true);
 assert.ok(result.criteria.filter(c=>c.overridden).length===1);
 assert.equal(personalScore(source,weights).criteria[1].personalPoints,3);
 assert.deepEqual(source,original);
 assert.throws(()=>personalScore(source,{},[key,key]));
 assert.throws(()=>personalScore(source,{},['unknown']));
});
