// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {decimalInput} from './presentation.mjs';
import {finite,cagr} from './finance.mjs';
import {multipleValuation} from './models.mjs';
import {parseSaved} from './saved.mjs';
export const emptyDesk=()=>({format:'tickertwister-research',version:1,entries:[]});
export const emptyNotes=()=>({status:'research',reviewDate:'',thesis:'',risks:'',disconfirm:'',nextStep:''});
export function parseDesk(input){
 const d=typeof input==='string'?JSON.parse(input):input;
 if(d?.format!=='tickertwister-research'||d.version!==1||!Array.isArray(d.entries)||d.entries.length>30)throw Error('INVALID_DESK');
 const seen=new Set();
 const entries=d.entries.map(e=>{
  const saved=parseSaved(e.saved),symbol=saved.report.symbol;
  if(seen.has(symbol))throw Error('INVALID_DESK');seen.add(symbol);
  const notes=e.notes;
  if(!notes||!['research','watch','pass','hard','candidate'].includes(notes.status)||!['reviewDate','thesis','risks','disconfirm','nextStep'].every(k=>typeof notes[k]==='string'&&notes[k].length<12001)||notes.reviewDate&&!/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?$/.test(notes.reviewDate))throw Error('INVALID_DESK');
  return {saved,notes:{...notes,status:notes.status==='pass'?'hard':notes.status}};
 });
 return {...emptyDesk(),entries};
}
export function sensitivity(report,inputs){
 if(multipleValuation(report,inputs).error)return null;
 const rates=[-4,-2,0,2,4].map(d=>Number(inputs.rate)+d),growths=[-6,-3,0,3,6].map(d=>Number(inputs.growth)+d);
 return {rates,growths,rows:growths.map(g=>rates.map(r=>multipleValuation(report,{...inputs,rate:String(r),growth:String(g)})))};
}
export function impliedGrowth(report,inputs,target){
 if(!finite(target)||target<=0)return {error:'NO_PRICE'};
 if(multipleValuation(report,inputs).error)return {error:'NO_MODEL'};
 let lo=-99,hi=100;
 const price=g=>multipleValuation(report,{...inputs,growth:String(g)}).perShare;
 if(!finite(price(lo))||!finite(price(hi))||target<price(lo)||target>price(hi))return {error:'OUTSIDE_RANGE'};
 for(let n=0;n<90;n++){const mid=(lo+hi)/2;if(price(mid)<target)lo=mid;else hi=mid;}
 return {growth:(lo+hi)/200,perShare:price((lo+hi)/2)};
}
export function scenariosFrom(inputs){
 const adjust=(growth,rate,multiple,cash)=>({growth:decimalInput(Math.max(-99.9,Number(inputs.growth)+growth)),rate:decimalInput(Math.min(100,Math.max(0,Number(inputs.rate)+rate))),multiple:String(Math.min(100,Math.max(.01,Number(inputs.multiple)*multiple))),cashFlow:inputs.cashFlow===''?'':String(Number((Number(inputs.cashFlow)*cash).toFixed(4)))});
 return [adjust(-5,2,.75,.85),{...inputs},adjust(5,-2,1.25,1.1)];
}
export function diagnostics(report){
 const y=report.years.at(-1),p=report.years.at(-2),checks=[];
 const ratio=(a,b)=>finite(a)&&finite(b)&&b>0?a/b:null;
 const add=(key,value,warn,nl,en,ruleNl,ruleEn,unit='ratio')=>checks.push({key,value,status:value===null?'missing':warn(value)?'review':'clear',nl,en,ruleNl,ruleEn,unit});
 add('conversion',ratio(y.cfo,y.income),v=>v<1,'Wordt winst ook kasstroom?','Does profit turn into cash?','CFO / net income; onder 1 vraagt uitleg. Negatieve of nulwinst: niet beoordeeld.','CFO / net income; below 1 needs explanation. Non-positive income: not assessed.');
 const avg=p&&finite(p.assets)&&finite(y.assets)?(p.assets+y.assets)/2:null;
 add('accruals',ratio(finite(y.income)&&finite(y.cfo)?y.income-y.cfo:null,avg),v=>v>.1,'Winst boven operationele kasstroom','Profit above operating cash flow','(Net income − CFO) / gemiddeld totaal activa. Boven 10%: onderzoek werkkapitaal en niet-kasposten; geen fraudetest.','(Net income − CFO) / average assets. Above 10%: investigate working capital and non-cash items; not a fraud test.','percent');
 add('payout',ratio(finite(y.dividends)&&finite(y.buybacks)?y.dividends+y.buybacks:null,y.fcf),v=>v>1,'Worden uitkeringen gedekt?','Are distributions covered?','(Dividenden + inkoop eigen aandelen) / FCF. Boven 1: uitkeringen overstijgen de vrije kasstroom.','(Dividends + share buybacks) / FCF. Above 1: distributions exceed free cash flow.');
 add('equity',ratio(y.equity,y.assets),v=>v<=0||v<.1,'Hoe dik is de kapitaalbuffer?','How thick is the equity cushion?','Eigen vermogen / totaal activa. Onder 10%: onderzoek schuld en de invloed op ROE. Sectorafhankelijk.','Equity / total assets. Below 10%: investigate leverage and its effect on ROE. Sector-dependent.','percent');
 add('shares',p&&finite(y.shares)&&finite(p.shares)&&p.shares>0?y.shares/p.shares-1:null,v=>v>.02,'Verwatering of aandeleninkoop','Dilution or share reduction','Verandering gerapporteerde aandelen sinds vorig boekjaar. Boven +2%: onderzoek emissies, aandelenbeloning en splits.','Change in reported shares since the prior fiscal year. Above +2%: investigate issuance, stock compensation and splits.','percent');
 add('liquidity',ratio(y.currentAssets,y.currentLiabilities),v=>v<1,'Kortlopende verplichtingen','Short-term obligations','Current assets / current liabilities. Onder 1: onderzoek werkkapitaal; sommige bedrijfsmodellen werken hiermee.','Current assets / current liabilities. Below 1: investigate working capital; some business models operate this way.');
 add('interest',ratio(y.operating,y.interest),v=>v<3,'Rentelasten dragen','Servicing interest','Operating income / interest expense. Onder 3: onderzoek financiering. Ontbrekende of nulrente is niet beoordeeld.','Operating income / interest expense. Below 3: investigate financing. Missing or zero interest is not assessed.');
 add('margin',p&&finite(y.netMargin)&&finite(p.netMargin)?y.netMargin-p.netMargin:null,v=>v<-.03,'Marge onder druk?','Margin under pressure?','Verschil nettomarge met vorig boekjaar. Daling groter dan 3 procentpunt: onderzoek mix, kosten en eenmalige posten.','Net margin change from prior fiscal year. A decline over 3 percentage points: investigate mix, costs and one-offs.','pp');
 return checks;
}
export function comparison(report){const y=report.years.at(-1);return {score:report.score.value,coverage:report.score.coverage,roe:y.roe,margin:y.netMargin,liquidity:y.currentRatio,debt:y.debtEquity,conversion:y.cashConversion,growth:cagr(report.years,'revenue')};}

export function selectedAIReports(entries,currentReport,options={}){
 return entries.map(e=>({...e.saved.report,aiWeights:(currentReport?.symbol===e.saved.report.symbol?options.scoreWeights:e.saved.options.scoreWeights)||{}}));
}
