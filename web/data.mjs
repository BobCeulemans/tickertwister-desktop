// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {nativeCall} from './native.mjs';
import {isYahooTicker} from './tickerBatch.mjs';
const pending=new Map();
export async function loadAnalysis(input){
 const symbol=String(input||'').trim().toUpperCase();
 if(!isYahooTicker(symbol))throw new Error('INVALID_TICKER');
 if(pending.has(symbol))return pending.get(symbol);
 const request=nativeCall('analyse',{symbol}).then(r=>{if(r.error)throw new Error(r.error);return r;});
 pending.set(symbol,request);try{return await request;}finally{pending.delete(symbol);}
}
