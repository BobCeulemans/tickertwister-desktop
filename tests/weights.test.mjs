import test from 'node:test';import assert from 'node:assert/strict';
import {personalScore,validWeights} from '../web/weights.mjs';
const report={schema:'yahoo39-v1',score:{criteria:[{key:'returnOnEquityHistory',weight:9,points:9,available:true},{key:'grossProfitMarginHistory',weight:4,points:0,available:true},{key:'netBorrowingsHistory',weight:0,points:0,available:true},{key:'netProfitMarginHistory',weight:6,points:null,available:false}]}};
test('default personal weighting matches original weighted score',()=>{assert.equal(personalScore(report).value,900/13);assert.equal(personalScore(report).custom,false);});
test('weights change importance without changing the original report',()=>{const old=JSON.stringify(report);const s=personalScore(report,{returnOnEquityHistory:2});assert.equal(s.value,1800/22);assert.equal(JSON.stringify(report),old);assert.equal(s.custom,true);});
test('missing and unscored criteria cannot acquire fabricated points',()=>{const s=personalScore(report,{netBorrowingsHistory:100,netProfitMarginHistory:100});assert.equal(s.value,900/13);});
test('all scored criteria disabled produces no score, not zero or infinity',()=>assert.equal(personalScore(report,{returnOnEquityHistory:0,grossProfitMarginHistory:0}).value,null));
test('bad weight files are rejected',()=>{for(const w of [null,[],{unknown:1},{returnOnEquityHistory:-1},{returnOnEquityHistory:'2'},{returnOnEquityHistory:Infinity},{returnOnEquityHistory:101}])assert.equal(validWeights(w),false);});
