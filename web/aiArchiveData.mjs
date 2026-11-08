import {languageCodes} from './i18n.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
import {parseResponse} from './aic.mjs';
export function archiveKey(input){const {language,asOf,...rest}=input;const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;return JSON.stringify(canonical(rest));}
export function readRecord(raw){
 if(!raw||typeof raw.id!=='string'||!languageCodes.includes(raw.language)||!raw.input?.companies?.length||!raw.input.companies.every(c=>typeof c.symbol==='string'))throw Error('INVALID_ARCHIVE');
 return {...raw,persisted:true,result:parseResponse(raw.response)};
}
export const relevantRecords=(records,symbols)=>records.filter(r=>r.input.companies.some(c=>symbols.includes(c.symbol)));

export const printRecords=(records,symbols,ids)=>relevantRecords(records,symbols).filter(r=>ids.includes(r.id));
