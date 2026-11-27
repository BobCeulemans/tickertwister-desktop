// SPDX-License-Identifier: AGPL-3.0-only
import assert from 'node:assert/strict';
import test from 'node:test';
import {collectTickerList,parseTickerList,isYahooTicker} from '../web/tickerBatch.mjs';

test('paste and UTF-8 text input accept Yahoo syntax and preserve unique order',()=>{
 assert.deepEqual(parseTickerList('\uFEFFlotb.br\r\n^tnx,brk-b;EURUSD=X  lotb.BR'),['LOTB.BR','^TNX','BRK-B','EURUSD=X']);
 assert.ok(['^TNX','BRK-B','EURUSD=X'].every(isYahooTicker));
 assert.ok(!isYahooTicker(' BAD ')&&!isYahooTicker('https://invalid'));
});

test('a list processes one company at a time and continues after invalid or unavailable data',async()=>{
 let concurrent=0;
 const seen=[],completed=[],failed=[];
 await collectTickerList(['A','!BAD','B','C'],{signal:new AbortController().signal,onStart:s=>seen.push(s),
  load:async s=>{assert.equal(++concurrent,1);await Promise.resolve();concurrent--;if(s==='B')throw Error('NO_ANNUAL_DATA');return {symbol:s};},
  onResult:(s,r)=>completed.push(r.symbol),onFailure:(s,e)=>failed.push([s,e])});
 assert.deepEqual(seen,['A','!BAD','B','C']);assert.deepEqual(completed,['A','C']);
 assert.deepEqual(failed,[['!BAD','INVALID_TICKER'],['B','NO_ANNUAL_DATA']]);
});

test('stopping a list retains the in-flight result and skips further requests',async()=>{
 const session=new AbortController(),seen=[],results=[];
 await collectTickerList(['A','B'],{signal:session.signal,onStart:s=>seen.push(s),load:async s=>{session.abort();return s;},onResult:s=>results.push(s),onFailure:assert.fail});
 assert.deepEqual(seen,['A']);assert.deepEqual(results,['A']);
});
