// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {directEquityModel,reportedSectorModel,sectorModel} from './valuationSector.mjs';
import {currentEarningsMethod,defaultValuation,equityDiscountInput,financialDiscountInput,minimumDiscountRate,valuationScenarios,valuationSources,previousEarningsDefaults} from './valuation.mjs';
import {canOverride,validOverrides,validWeights} from './weights.mjs';
import {validBenchmark} from './riskFree.mjs';
import ORIGINAL_METHODS from './original-methods.mjs';
import {qualityScore,finite} from './finance.mjs';
export function makeSaved(report,options){return {format:'tickertwister-desktop',version:1,savedAt:new Date().toISOString(),report,options};}
// Earlier snapshots contain FCF or a multiple-based model. Their cash flow, growth and
// scenarios cannot be reused as owner earnings. Keep the original snapshot intact.
export function restoreValuation(report,options={}){
 const old=options.valuationInputs;
 let inputs=defaultValuation(report);
 const current=old?.model==='dcf';
 const recoverMissing=current && old.waccBeta===undefined && old.ownerEarnings==='' &&
   inputs.ownerEarnings!=='' && valuationSources(report).assumedZero?.length>0;
 if(current)inputs=recoverMissing?{...old,waccBeta:'',ownerEarnings:inputs.ownerEarnings,growth:old.growth||inputs.growth}:old;
 else if(old)inputs={...inputs,rate:old.rate,terminal:old.terminal==='2'?inputs.terminal:old.terminal,dividend:old.dividend,
  netDebt:old.basis==='enterprise'?old.netDebt:inputs.netDebt};
 const migrateEarnings=current && old.earningsMethod!==currentEarningsMethod;
 const oldScenarios=options.valuationScenarios;
 let migratedScenarios;
 if(migrateEarnings){
  const defaults=defaultValuation(report), previous=previousEarningsDefaults(report,old.earningsMethod);
  const keys=['ownerEarnings','growth'];
  const sector=sectorModel(report), oldSector=reportedSectorModel(report);
  const previousEquity=old.earningsMethod==='sector-blend-v1' && (oldSector==='bank'||oldSector==='insurance');
  if(sector==='financial'){
   previous.rate=String(minimumDiscountRate(report));
   defaults.rate=financialDiscountInput(report,old.waccBeta);
   // Preview 6's "Use WACC" stored twelve significant digits. Recognize that
   // selection so the sourced rate can follow the next company-data refresh.
   if(old.earningsMethod==='sector-blend-v1' && inputs.rate===String(Number(Number(defaults.rate).toPrecision(12)))){
    previous.rate=inputs.rate;
   }
   keys.push('rate');
  }
  const updated={...inputs,earningsMethod:defaults.earningsMethod};
  for(const key of keys)if(inputs[key]===previous[key])updated[key]=defaults[key];
  const reclassifiedAsBank=directEquityModel(report) && !previousEquity && old.earningsMethod==='sector-blend-v1';
  if(reclassifiedAsBank){
   updated.personalEquityRate=inputs.rate!==String(minimumDiscountRate(report)) && Number(inputs.rate)>0;
   updated.rate=updated.personalEquityRate?inputs.rate:equityDiscountInput(report,inputs.waccBeta);
   updated.netDebt='';
  }
  if(oldScenarios){
   const baseline=valuationScenarios(old,report,previousEquity), target=valuationScenarios(updated,report);
   migratedScenarios=oldScenarios.map((scenario,i)=>{
    const revised={...scenario,earningsMethod:defaults.earningsMethod};
    for(const key of keys)if(scenario[key]===baseline[i][key])revised[key]=target[i][key];
    if(reclassifiedAsBank){
     const ownRate=scenario.rate!==baseline[i].rate;
     if(ownRate)revised.independentEquityRate=true;
     revised.personalEquityRate=ownRate||updated.personalEquityRate;
     revised.rate=ownRate?scenario.rate:updated.rate;
     revised.netDebt='';
    }
    return revised;
   });
  }
  inputs=updated;
 }
 const originalInputs=inputs;
 inputs=withDiscountPolicy(inputs,report);
 const originalScenarios=migratedScenarios||(current&&options.valuationScenarios?options.valuationScenarios:valuationScenarios(inputs,report));
 const recovered=recoverMissing?valuationScenarios(inputs,report):null;
 const scenarios=originalScenarios.map((s,i)=>withDiscountPolicy(recovered?{...s,ownerEarnings:s.ownerEarnings||recovered[i].ownerEarnings,growth:s.growth||recovered[i].growth}:s,report));
 return {inputs,scenarios,legacy:migrateEarnings||recoverMissing||!current||inputs!==originalInputs||scenarios.some((s,i)=>s!==originalScenarios[i])};
}
function withDiscountPolicy(inputs,report){
 if(directEquityModel(report)){
  if(inputs.personalEquityRate===true)return inputs;
  const rate=equityDiscountInput(report,inputs.waccBeta);
  return inputs.rate===rate?inputs:{...inputs,rate};
 }
 const minimum=minimumDiscountRate(report);
 if(inputs.rate===''||!Number.isFinite(Number(inputs.rate))||Number(inputs.rate)>=minimum)return inputs;
 return {...inputs,rate:String(minimum)};
}
// Recalculate sourced defaults when financial data changes. Explicit edits survive a refresh.
function applyOverrides(next,previous,actual){
 const result={...next};
 for(const key of Object.keys(next))if(actual[key]!==undefined&&actual[key]!==previous[key])result[key]=actual[key];
 return result;
}
export function updateValuationScenarios(scenarios,previousInputs,nextInputs,previousReport,nextReport=previousReport){
 const previous=valuationScenarios(previousInputs,previousReport), next=valuationScenarios(nextInputs,nextReport);
 return next.map((scenario,index)=>{
  const actual=scenarios[index]||{};
  const result=applyOverrides(scenario,previous[index],actual);
  if(directEquityModel(nextReport)){
   result.waccBeta=nextInputs.waccBeta;
   if(actual.independentEquityRate){
    result.independentEquityRate=true;
    result.personalEquityRate=true;
    result.rate=actual.rate;
   }else{
    result.personalEquityRate=nextInputs.personalEquityRate===true;
    result.rate=nextInputs.rate;
   }
  }
  return withDiscountPolicy(result,nextReport);
 });
}
export function refreshedValuationOptions(saved,report){
 const {inputs,scenarios}=restoreValuation(saved.report,saved.options);
 const overrides=applyOverrides(defaultValuation(report),defaultValuation(saved.report),inputs);
 if(sectorModel(report)==='financial' && sectorModel(saved.report)==='financial' &&
    inputs.rate===financialDiscountInput(saved.report,inputs.waccBeta)){
  overrides.rate=financialDiscountInput(report,inputs.waccBeta);
 }
 if(directEquityModel(report) && inputs.personalEquityRate===true){
  overrides.personalEquityRate=true;
  overrides.rate=inputs.rate;
 }
 const next=withDiscountPolicy(overrides,report);
 return {method:saved.options.method,...(saved.options.scratchpad!==undefined?{scratchpad:saved.options.scratchpad}:{}),scoreWeights:saved.options.scoreWeights||{},scoreOverrides:(saved.options.scoreOverrides||[]).filter(key=>report.score?.criteria?.some(c=>c.key===key&&canOverride(c))),valuationInputs:next,
  valuationScenarios:updateValuationScenarios(scenarios,inputs,next,saved.report,report)};
}
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
 for(const k of ['website','sector','industry','country'])if(r[k]!==undefined&&(typeof r[k]!=='string'||r[k].length>2000))throw Error('INVALID_SAVED');
 if(r.provenance.length>300||r.provenance.some(p=>['field','tag','end','filed','accession'].some(k=>typeof p[k]!=='string'||p[k].length>300)))throw new Error('INVALID_SAVED');
 if(r.quote!==null&&(!finite(r.quote?.price)||r.quote.price<=0||typeof r.quote.currency!=='string'))throw new Error('INVALID_SAVED');
 // Optional 5.0.3 currency metadata travels with snapshots; reject corrupt conversion inputs.
 if(r.fx!==undefined&&(!r.fx||!finite(r.fx.rate)||r.fx.rate<=0||!/^[A-Z]{3}$/.test(r.fx.from)||!/^[A-Z]{3}$/.test(r.fx.to)||typeof r.fx.at!=='string'||!Number.isFinite(Date.parse(r.fx.at))))throw Error('INVALID_SAVED');
 if(r.quoteBasis!==undefined&&(!r.quoteBasis||r.quoteBasis.verified!==true||!finite(r.quoteBasis.ordinaryPerQuote)||r.quoteBasis.ordinaryPerQuote<=0||typeof r.quoteBasis.source!=='string'||!r.quoteBasis.source.startsWith('https://')))throw Error('INVALID_SAVED');
 if(!['dcf','gordon'].includes(s.options.method)||(s.options.valuationInputs?.model!=='dcf'&&['rate','growth','terminal','price','cashFlow'].some(k=>typeof s.options[k]!=='string'||s.options[k].length>32)))throw new Error('INVALID_SAVED');
 if(s.options.multipleInputs!==undefined&&(!s.options.multipleInputs||['rate','growth','multiple','cashFlow'].some(k=>typeof s.options.multipleInputs[k]!=='string'||s.options.multipleInputs[k].length>32)))throw new Error('INVALID_SAVED');
 if(s.options.labScenarios!==undefined&&(!Array.isArray(s.options.labScenarios)||s.options.labScenarios.length!==3||s.options.labScenarios.some(v=>!v||['rate','growth','multiple','cashFlow'].some(k=>typeof v[k]!=='string'||v[k].length>32))))throw new Error('INVALID_SAVED');
 const ownerModel=s.options.valuationInputs?.model==='dcf';
 const numericText=value=>typeof value==='string'&&value.length<=32&&(value===''||Number.isFinite(Number(value)));
 const validValuation=v=>{
  if(!v)return false;
  if(v.personalEquityRate!==undefined&&typeof v.personalEquityRate!=='boolean')return false;
  if(v.independentEquityRate!==undefined&&(v.independentEquityRate!==true||v.personalEquityRate!==true||v===s.options.valuationInputs))return false;
  if(ownerModel)return v.model==='dcf'&&(v.earningsMethod===undefined||['sector-blend-v1',currentEarningsMethod].includes(v.earningsMethod))&&v.years==='10'&&(v.waccBeta==null||numericText(v.waccBeta))&&['ownerEarnings','rate','growth','terminal','dividend','netDebt','shares'].every(k=>numericText(v[k]));
  return v.model===undefined&&['equity','enterprise'].includes(v.basis)&&['cashFlow','expansionCapex','interestAdjustment','netDebt','rate','growth','terminal','years','dividend'].every(k=>numericText(v[k]));
 };
 if(s.options.valuationInputs!==undefined&&!validValuation(s.options.valuationInputs))throw Error('INVALID_SAVED');
 if(s.options.valuationScenarios!==undefined&&(!Array.isArray(s.options.valuationScenarios)||s.options.valuationScenarios.length!==3||!s.options.valuationScenarios.every(validValuation)))throw Error('INVALID_SAVED');
 if(r.beta!=null&&!finite(r.beta))throw Error('INVALID_SAVED');
 if(r.riskFreeRates!=null&&(typeof r.riskFreeRates!=='object'||Array.isArray(r.riskFreeRates)||Object.entries(r.riskFreeRates).some(([code,obs])=>!validBenchmark(code,obs))))throw Error('INVALID_SAVED');
 if(r.waccAccounts!=null){
  const a=r.waccAccounts, date=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&Number.isFinite(Date.parse(v));
  if(!date(a.balanceDate)||(a.flowDate!=null&&(!date(a.flowDate)||a.flowDate!==a.balanceDate))||
     (a.flowBasis!=null&&!['TTM','FY=TTM'].includes(a.flowBasis))||['debt','tax','pretax','interest'].some(k=>a[k]!=null&&!finite(a[k])))throw Error('INVALID_SAVED');
 }
 if(r.waccTreasury!=null){const q=r.waccTreasury;if(!finite(q.yield)||q.yield<=-100||q.yield>=100||!/^\d{4}-\d{2}-\d{2}$/.test(q.date))throw Error('INVALID_SAVED');}
 if(r.valuationData!==undefined){const d=r.valuationData;if(!d||typeof d!=='object'||['netDebt','afterTaxInterest','leaseDebt','cash','grossDebt'].some(k=>d[k]!=null&&!Number.isFinite(d[k])))throw Error('INVALID_SAVED');}
 if(r.treasury!==undefined&&r.treasury!==null){const q=r.treasury;if(!Number.isFinite(q.yield)||q.yield<=-100||q.yield>=100||typeof q.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(q.date))throw Error('INVALID_SAVED');}
 if(s.options.scratchpad!==undefined&&(typeof s.options.scratchpad!=='string'||s.options.scratchpad.length>12000))throw Error('INVALID_SAVED');
 if(s.options.scoreOverrides!==undefined&&!validOverrides(s.options.scoreOverrides))throw Error('INVALID_SAVED');
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
