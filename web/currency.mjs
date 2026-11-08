// SPDX-License-Identifier: AGPL-3.0-only
// Values remain in statement currency; FX translates only the comparison price.
const positive=v=>Number.isFinite(v)&&v>0;
export function fxRate(report){const f=report?.fx;return f&&f.from===report.quote?.currency&&f.to===report.currency&&positive(f.rate)&&Number.isFinite(Date.parse(f.at))&&Number.isFinite(Date.parse(report.fetchedAt))&&Math.abs(Date.parse(report.fetchedAt)-Date.parse(f.at))<=7*86400000?f.rate:null;}
export function comparablePrice(report){const q=report?.quote;if(!positive(q?.price))return null;if(q.currency===(report.currency||'USD'))return q.price;const rate=fxRate(report),basis=report.quoteBasis;return rate&&basis?.verified===true&&positive(basis.ordinaryPerQuote)?q.price*rate/basis.ordinaryPerQuote:null;}
export function quotedModelValue(report,value){const rate=fxRate(report),basis=report.quoteBasis;return positive(value)&&rate&&basis?.verified===true&&positive(basis.ordinaryPerQuote)?value*basis.ordinaryPerQuote/rate:null;}
export function dividendInStatementCurrency(report,value){if(!report.dividendCurrency||report.dividendCurrency===report.currency)return value;const rate=fxRate(report),basis=report.quoteBasis;return report.dividendCurrency===report.quote?.currency&&positive(value)&&rate&&basis?.verified===true&&positive(basis.ordinaryPerQuote)?value*rate/basis.ordinaryPerQuote:null;}
