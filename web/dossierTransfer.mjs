// SPDX-License-Identifier: AGPL-3.0-only
import {emptyDesk,parseDesk} from './research.mjs';
import {readRecord,relevantRecords} from './aiArchiveData.mjs';

const format='tickertwister-transfer';
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const symbol=/^[A-Z0-9^][A-Z0-9.^=-]{0,19}$/;

function portableRecord(record){
 const r=readRecord(record);
 if(!uuid.test(r.id)||typeof r.createdAt!=='string'||!Number.isFinite(Date.parse(r.createdAt))||r.input.companies.length>4||
   (r.response.model!=null&&typeof r.response.model!=='string')||(r.settings!=null&&
    (typeof r.settings!=='object'||(r.settings.effort!=null&&typeof r.settings.effort!=='string')||
     (r.settings.limit!=null&&!Number.isSafeInteger(r.settings.limit))))||
   !r.input.companies.every(c=>symbol.test(c.symbol))||typeof r.input.period!=='string'||
   (r.translationOf!=null&&!uuid.test(r.translationOf)))throw Error('INVALID_TRANSFER');
 return {id:r.id,input:r.input,language:r.language,response:r.response,createdAt:r.createdAt,
  translationOf:r.translationOf??null,settings:r.settings??null};
}
export function makeTransfer(desk,records,symbols,includeFullArchive=false){
 const entries=desk.entries.filter(entry=>symbols.includes(entry.saved.report.symbol));
 const full=includeFullArchive&&entries.length===desk.entries.length;
 const archive=full?records:relevantRecords(records,entries.map(e=>e.saved.report.symbol));
 return parseTransfer({format,version:1,full,dossier:{...emptyDesk(),entries},archive:archive.map(portableRecord)});
}
export function parseTransfer(input){
 const file=typeof input==='string'?JSON.parse(input):input;
 if(file?.format!==format||file.version!==1||typeof file.full!=='boolean'||!Array.isArray(file.archive))throw Error('INVALID_TRANSFER');
 const dossier=parseDesk(file.dossier),archive=file.archive.map(portableRecord);
 if(!dossier.entries.length&&!archive.length)throw Error('EMPTY_TRANSFER');
 const tickers=new Set(dossier.entries.map(e=>e.saved.report.symbol));
 const ids=new Set();
 for(const record of archive){
  const key=record.id.toLowerCase();
  if(ids.has(key)||(!file.full&&!record.input.companies.some(c=>tickers.has(c.symbol))))throw Error('INVALID_TRANSFER');
  ids.add(key);
 }
 return {format,version:1,full:file.full,dossier,archive};
}
// Foundation may reorder JSON keys when committing the transaction.
export function sameDossier(a,b){
 const order=value=>Array.isArray(value)?value.map(order):value&&typeof value==='object'?
  Object.fromEntries(Object.keys(value).sort().map(k=>[k,order(value[k])])):value;
 return JSON.stringify(order(a))===JSON.stringify(order(b));
}
export function planImport(local,file,replace=false){
 const imported=new Map(file.dossier.entries.map(e=>[e.saved.report.symbol,e]));
 const existing=new Set(local.entries.map(e=>e.saved.report.symbol));
 const added=file.dossier.entries.filter(e=>!existing.has(e.saved.report.symbol));
 const matching=file.dossier.entries.filter(e=>existing.has(e.saved.report.symbol)).map(e=>e.saved.report.symbol);
 if(local.entries.length+added.length>30)throw Error('DOSSIER_FULL');
 const retained=local.entries.map(e=>replace?(imported.get(e.saved.report.symbol)??e):e);
 return {desk:parseDesk({...local,entries:[...retained,...added]}),added:added.length,matching};
}
