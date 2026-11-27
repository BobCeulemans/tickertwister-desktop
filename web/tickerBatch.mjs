// SPDX-License-Identifier: AGPL-3.0-only
export const isYahooTicker = value => /^[A-Z0-9^][A-Z0-9.^=\-]{0,19}$/.test(value);

export function parseTickerList(text) {
 return [...new Set(String(text).toUpperCase().split(/[\s,;]+/u).filter(Boolean))];
}

export async function collectTickerList(symbols,{load,onStart,onResult,onFailure,signal}) {
 for(const symbol of symbols) {
  if(signal.aborted)break;
  onStart(symbol);
  try {
   if(!isYahooTicker(symbol))throw Error('INVALID_TICKER');
   onResult(symbol,await load(symbol));
  }catch(error){onFailure(symbol,error.message||'DATA_UNAVAILABLE');}
 }
}
