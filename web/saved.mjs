// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {validWeights} from './weights.mjs';
import ORIGINAL_METHODS from './original-methods.mjs';
import {qualityScore,finite} from './finance.mjs';
export function makeSaved(report,options){return {format:'tickertwister-desktop',version:1,savedAt:new Date().toISOString(),report,options};}
export function parseSaved(input){
 const s=typeof input==='string'?JSON.parse(input):input;
 if(s?.format!=='tickertwister-desktop'||s.version!==1||!s.report||!s.options)throw new Error('INVALID_SAVED');
 const r=s.report;const yahoo=r.schema==='yahoo39-v1';
 if(typeof r.symbol!=='string'||!/^[A-Z0-9^][A-Z0-9.^=\-]{0,19}$/.test(r.symbol)||typeof r.name!=='string'||r.name.length>500||(yahoo?!/^[A-Za-z]{3,12}$/.test(r.currency):r.currency!=='USD')||(!yahoo&&!/^\d{10}$/.test(r.cik))||!Array.isArray(r.years)||!r.years.length||r.years.length>4||!Array.isArray(r.provenance))throw new Error('INVALID_SAVED');
 const numericKeys=['revenue','income','gross','cost','operating','interest','assets','equity','liabilities','currentAssets','currentLiabilities','cash','investments','receivables','inventory','payables','longDebt','currentDebt','shortDebt','retained','cfo','capex','debtIssued','debtRepaid','buybacks','dividends','eps','dps','shares','debt','fcf','roe','roa','grossMargin','netMargin','currentRatio','quickRatio','debtEquity','liabilitiesEquity','interestCoverage','fcfMargin','cashConversion','assetTurnover','capexIncome','dividendCoverage','dio','dso','dpo','ccc'];
 for(const y of r.years){if(!/^\d{4}-\d{2}-\d{2}$/.test(y.end))throw new Error('INVALID_SAVED');for(const key of numericKeys){if(y[key]!==null&&!finite(y[key]))throw new Error('INVALID_SAVED');}}
 if(r.revenueGrowth!==undefined&&r.revenueGrowth!==null&&!finite(r.revenueGrowth))throw Error('INVALID_SAVED');
 // Optional v3.1 comparison data; old saved analyses remain readable.
 if(r.quarters!==undefined){
  if(!Array.isArray(r.quarters)||r.quarters.length>8)throw Error('INVALID_SAVED');
  const seen=new Set();for(const q of r.quarters){
   if(!/^\d{4}-\d{2}-\d{2}$/.test(q.end)||!/^\d{4}-Q[1-4]$/.test(q.periodKey)||q.periodType!=='quarter'||seen.has(q.periodKey))throw Error('INVALID_SAVED');seen.add(q.periodKey);
   if(Math.abs(Date.parse(q.end+'T00:00:00Z')-Date.UTC(Number(q.periodKey.slice(0,4)),Number(q.periodKey.slice(-1))*3,0))>7*86400000)throw Error('INVALID_SAVED');
   for(const [k,v] of Object.entries(q))if(!['end','periodKey','periodType'].includes(k)&&v!==null&&!finite(v))throw Error('INVALID_SAVED');
  }
 }
 for(const k of ['website','sector','industry'])if(r[k]!==undefined&&(typeof r[k]!=='string'||r[k].length>2000))throw Error('INVALID_SAVED');
 if(r.provenance.length>300||r.provenance.some(p=>['field','tag','end','filed','accession'].some(k=>typeof p[k]!=='string'||p[k].length>300)))throw new Error('INVALID_SAVED');
 if(r.quote!==null&&(!finite(r.quote?.price)||r.quote.price<=0||typeof r.quote.currency!=='string'))throw new Error('INVALID_SAVED');
 // Optional 5.0.3 currency metadata travels with snapshots; reject corrupt conversion inputs.
 if(r.fx!==undefined&&(!r.fx||!finite(r.fx.rate)||r.fx.rate<=0||!/^[A-Z]{3}$/.test(r.fx.from)||!/^[A-Z]{3}$/.test(r.fx.to)||typeof r.fx.at!=='string'||!Number.isFinite(Date.parse(r.fx.at))))throw Error('INVALID_SAVED');
 if(r.quoteBasis!==undefined&&(!r.quoteBasis||r.quoteBasis.verified!==true||!finite(r.quoteBasis.ordinaryPerQuote)||r.quoteBasis.ordinaryPerQuote<=0||typeof r.quoteBasis.source!=='string'||!r.quoteBasis.source.startsWith('https://')))throw Error('INVALID_SAVED');
 if(!['dcf','gordon'].includes(s.options.method)||['rate','growth','terminal','price','cashFlow'].some(k=>typeof s.options[k]!=='string'||s.options[k].length>32))throw new Error('INVALID_SAVED');
 if(s.options.multipleInputs!==undefined&&(!s.options.multipleInputs||['rate','growth','multiple','cashFlow'].some(k=>typeof s.options.multipleInputs[k]!=='string'||s.options.multipleInputs[k].length>32)))throw new Error('INVALID_SAVED');
 if(s.options.labScenarios!==undefined&&(!Array.isArray(s.options.labScenarios)||s.options.labScenarios.length!==3||s.options.labScenarios.some(v=>!v||['rate','growth','multiple','cashFlow'].some(k=>typeof v[k]!=='string'||v[k].length>32))))throw new Error('INVALID_SAVED');
 if(s.options.scoreWeights!==undefined&&!validWeights(s.options.scoreWeights))throw Error('INVALID_SAVED');
 if(typeof s.savedAt!=='string'||!Number.isFinite(Date.parse(s.savedAt)))throw new Error('INVALID_SAVED');
 let score=qualityScore(r.years);
 if(yahoo){
  const criteria=r.score?.criteria;
  if(!Array.isArray(criteria)||criteria.length!==39||criteria.some((c,i)=>c.key!==ORIGINAL_METHODS[i]||typeof c.available!=='boolean'||!finite(c.weight)||c.weight<0||(c.available&&(!finite(c.points)||c.points<0||c.points>c.weight))||['label','heading','formula','threshold'].some(k=>typeof c[k]!=='string')))throw new Error('INVALID_SAVED');
  if(!Array.isArray(r.originalHistories)||r.originalHistories.some(h=>typeof h.name!=='string'||typeof h.label!=='string'||typeof h.heading!=='string'||!Array.isArray(h.pairs)||h.pairs.some(p=>typeof p[0]!=='string'||(p[1]!==null&&!finite(p[1])))))throw new Error('INVALID_SAVED');
  if(r.years.some(y=>y.fcfe!==null&&!finite(y.fcfe)))throw new Error('INVALID_SAVED');
  const available=criteria.filter(c=>c.available),points=available.reduce((sum,c)=>sum+c.points,0),weight=available.reduce((sum,c)=>sum+c.weight,0);
  score={criteria:criteria.map(c=>({...c,factor:c.available?(c.weight?c.points/c.weight:0):null})),value:weight?100*points/weight:null,points,weight,available:available.length,total:39,coverage:available.length/39};
 }
 return {...s,report:{...r,score,savedAt:s.savedAt,cached:false}};
}
