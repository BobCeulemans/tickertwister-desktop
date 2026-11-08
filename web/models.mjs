import {comparablePrice} from './currency.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {decimalInput} from './presentation.mjs';
import {finite,cagr} from './finance.mjs';
export function cashFlowBasis(report){
 const y=report.years.at(-1)||{};
 if(finite(y.fcfe))return {value:y.fcfe,kind:'fcfe',end:y.end};
 if(finite(report.originalValuation?.fcfe))return {value:report.originalValuation.fcfe,kind:'fcfe',end:y.end};
 // Missing borrowing is not zero in the underlying statements or quality score.
 if(finite(y.fcf))return {value:y.fcf,kind:'fcf-proxy',end:y.end};
 return {value:null,kind:'missing',end:y.end};
}
export function cashFlowExplanation(report,t){const b=cashFlowBasis(report);return b.kind==='fcf-proxy'?t("Starting value: FCF (CFO − capex) as an FCFE proxy, assuming zero net borrowing. Debt cash flows are missing; check this assumption. Source data and quality score are unchanged."):b.kind==='missing'?t("No usable cash flow available. Enter your own normalised cash flow."):t("Starting value: calculated FCFE for the latest fiscal year.");}
// Shared by the main model and Valuation Lab. Do not substitute revenue growth
// or silently shorten the displayed history when cash-flow endpoints are absent.
export function historicalCashFlowGrowth(report){
 const history=report.years.slice().sort((a,b)=>a.end.localeCompare(b.end));
 return cagr(history,report.schema==='yahoo39-v1'?'fcfe':'fcf');
}
export function multipleDefaults(report){
 const v=report.originalValuation||{},historical=historicalCashFlowGrowth(report);
 return {rate:decimalInput((v.rate??.12)*100),growth:decimalInput((finite(historical)?historical:0)*100),multiple:String(v.multiple??15),cashFlow:finite(cashFlowBasis(report).value)?String(cashFlowBasis(report).value/1e6):''};
}
export function scenarioDefaults(report){
 const latest=report.years.at(-1),historical=cagr(report.years,report.schema==='yahoo39-v1'?'fcfe':'fcf');
 const growth=finite(historical)?historical:(finite(report.revenueGrowth)?report.revenueGrowth:report.originalValuation?.growth??0);
 const base=cashFlowBasis(report).value;
 return {rate:'12',growth:decimalInput(growth*100),terminal:'2',cashFlow:finite(base)?String(base/1e6):'',growthSource:finite(historical)?'history':'fallback'};
}
export function multipleValuation(report,inputs){
 if(Object.values(inputs).some(v=>typeof v!=='string'||!v.trim()))return {error:'INVALID_ASSUMPTIONS'};
 const rate=Number(inputs.rate)/100,growth=Number(inputs.growth)/100,multiple=Number(inputs.multiple),base=Number(inputs.cashFlow)*1e6;
 if(![rate,growth,multiple,base].every(finite)||rate<0||rate>1||growth<=-1||multiple<=0||multiple>100)return {error:'INVALID_ASSUMPTIONS'};
 if(!report.currency||report.currency==='onbekend')return {error:'CURRENCY_MISMATCH'};
 const shares=report.valuationShares;
 if(!(base>0&&shares>0))return {error:'NO_CASHFLOW'};
 const rows=Array.from({length:10},(_,i)=>{const year=i+1,flow=base*(1+growth)**year;return {year,flow,pv:flow/(1+rate)**year};});
 const terminalPV=rows.at(-1).pv*multiple,total=rows.reduce((s,r)=>s+r.pv,0)+terminalPV,perShare=total/shares;
 if(![total,perShare,terminalPV].every(finite))return {error:'INVALID_ASSUMPTIONS'};
 const price=comparablePrice(report);
 return {base,rate,growth,multiple,shares,rows,total,perShare,terminalPV,price,margin:price>0?1-price/perShare:null};
}
export function businessExcerpt(text,max=620){
 if(typeof text!=='string'||!text.trim())return '';
 if(text.length<=max)return text;
 const part=text.slice(0,max),sentence=part.lastIndexOf('. ');
 return sentence>max/2?part.slice(0,sentence+1):part.slice(0,part.lastIndexOf(' '))+'…';
}
