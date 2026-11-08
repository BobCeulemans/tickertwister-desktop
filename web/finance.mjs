import {comparablePrice,dividendInStatementCurrency} from './currency.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
/** Tickertwister Sites · inspired by Bob Ceulemans' Apache-2.0 analysis rules.
 * Values are raw USD; ratios are fractions. Missing data is never zero-filled. */
export const finite = v => typeof v === 'number' && Number.isFinite(v);
export const div = (a,b) => finite(a)&&finite(b)&&b>0 ? a/b : null;
const sum = (...v) => v.every(finite) ? v.reduce((a,b)=>a+b,0) : null;
const sub = (a,b) => finite(a)&&finite(b) ? a-b : null;
const tags = {
 revenue:['RevenueFromContractWithCustomerExcludingAssessedTax','RevenueFromContractWithCustomerIncludingAssessedTax','Revenues','SalesRevenueNet'],
 income:['NetIncomeLoss','ProfitLoss'],gross:['GrossProfit'],cost:['CostOfRevenue','CostOfGoodsAndServicesSold'],
 operating:['OperatingIncomeLoss'],interest:['InterestExpense','InterestAndDebtExpense'],
 assets:['Assets'],equity:['StockholdersEquity'],liabilities:['Liabilities'],currentAssets:['AssetsCurrent'],currentLiabilities:['LiabilitiesCurrent'],
 cash:['CashAndCashEquivalentsAtCarryingValue'],investments:['ShortTermInvestments','MarketableSecuritiesCurrent'],receivables:['AccountsReceivableNetCurrent'],inventory:['InventoryNet'],payables:['AccountsPayableCurrent'],
 longDebt:['LongTermDebtNoncurrent'],currentDebt:['LongTermDebtCurrent'],shortDebt:['ShortTermBorrowings','CommercialPaper'],
 retained:['RetainedEarningsAccumulatedDeficit'],cfo:['NetCashProvidedByUsedInOperatingActivities'],capex:['PaymentsToAcquirePropertyPlantAndEquipment'],
 debtIssued:['ProceedsFromIssuanceOfLongTermDebt'],debtRepaid:['RepaymentsOfLongTermDebt'],
 buybacks:['PaymentsForRepurchaseOfCommonStock'],dividends:['PaymentsOfDividendsCommonStock','PaymentsOfDividends'],
 eps:['EarningsPerShareDiluted'],dps:['CommonStockDividendsPerShareCashPaid','CommonStockDividendsPerShareDeclared'],shares:['CommonStockSharesOutstanding'],
};
const stockFields=new Set(['assets','equity','liabilities','currentAssets','currentLiabilities','cash','investments','receivables','inventory','payables','longDebt','currentDebt','shortDebt','retained','shares']);
const annual=f=>['10-K','10-K/A'].includes(f.form)&&f.start&&((Date.parse(f.end)-Date.parse(f.start))/86400000>=330)&&((Date.parse(f.end)-Date.parse(f.start))/86400000<=400);
export function normalizeFacts(raw,symbol){
 const facts=raw.facts?.['us-gaap'];
 if(!facts)throw new Error('UNSUPPORTED_GAAP');
 const entries=(key,unit='USD')=>(facts[key]?.units?.[unit]||[]).filter(f=>finite(f.val));
 const ends=[...new Set([...tags.revenue,...tags.income].flatMap(t=>entries(t).filter(annual).map(f=>f.end)))].sort().slice(-4);
 if(!ends.length)throw new Error('NO_ANNUAL_USD');
 const provenance=[];
 const value=(key,end)=>{
  const unit=key==='shares'?'shares':['eps','dps'].includes(key)?'USD/shares':'USD';
  for(const tag of tags[key]){
   const matches=entries(tag,unit).filter(f=>f.end===end&&(stockFields.has(key)?!f.start&&['10-K','10-K/A'].includes(f.form):annual(f))).sort((a,b)=>b.filed.localeCompare(a.filed));
   if(matches.length){const f=matches[0];provenance.push({field:key,tag,end,filed:f.filed,accession:f.accn});return f.val;}
  }return null;
 };
 const years=ends.map(end=>{
  const r=Object.fromEntries(Object.keys(tags).map(k=>[k,value(k,end)]));r.end=end;
  if(r.gross===null)r.gross=sub(r.revenue,r.cost);
  // Require every debt component; absent disclosures must not become zero debt.
  r.debt=sum(r.longDebt,r.currentDebt,r.shortDebt);
  r.fcf=sub(r.cfo,r.capex);
  r.roe=div(r.income,r.equity);r.roa=div(r.income,r.assets);r.grossMargin=div(r.gross,r.revenue);r.netMargin=div(r.income,r.revenue);
  r.currentRatio=div(r.currentAssets,r.currentLiabilities);r.quickRatio=div(sum(r.cash,r.investments,r.receivables),r.currentLiabilities);
  r.debtEquity=div(r.debt,r.equity);r.liabilitiesEquity=div(r.liabilities,r.equity);r.interestCoverage=div(r.operating,r.interest);
  r.fcfMargin=div(r.fcf,r.revenue);r.cashConversion=div(r.cfo,r.income);r.assetTurnover=div(r.revenue,r.assets);
  r.capexIncome=div(r.capex,r.income);r.dividendCoverage=div(r.fcf,r.dividends);
  r.dio=finite(div(r.inventory,r.cost))?365*div(r.inventory,r.cost):null;
  r.dso=finite(div(r.receivables,r.revenue))?365*div(r.receivables,r.revenue):null;
  r.dpo=finite(div(r.payables,r.cost))?365*div(r.payables,r.cost):null;
  r.ccc=sub(sum(r.dio,r.dso),r.dpo);
  return r;
 });
 const latest=years.at(-1);
 return {symbol,name:raw.entityName,cik:String(raw.cik).padStart(10,'0'),currency:'USD',years,provenance,score:qualityScore(years),fetchedAt:new Date().toISOString(),latestEnd:latest.end,stale:(Date.now()-Date.parse(latest.end))/86400000>550};
}
export function cagr(years,key){
 if(years.length<2)return null;const a=years[0],b=years.at(-1),elapsed=(Date.parse(b.end)-Date.parse(a.end))/86400000/365.25;
 if(!finite(a[key])||!finite(b[key])||a[key]<=0||b[key]<=0||!finite(elapsed)||elapsed<=0)return null;
 const growth=Math.pow(b[key]/a[key],1/elapsed)-1;
 return finite(growth)?growth:null;
}
export function qualityScore(years){
 const r=years.at(-1)||{};
 const definitions=[
  ['roe','Return on Equity',9,r.roe,.15,0,'high','Net income / closing equity','≥15%; partial credit >0%'],
  ['roa','Return on Assets',9,r.roa,.01,0,'high','Net income / closing assets','≥1%; partial credit >0%'],
  ['grossMargin','Gross Profit Margin',4,r.grossMargin,.40,.20,'high','Gross profit / revenue','≥40%; partial credit ≥20%'],
  ['netMargin','Net Profit Margin',4,r.netMargin,.20,.10,'high','Net income / revenue','≥20%; partial credit ≥10%'],
  ['currentRatio','Current Ratio',6,r.currentRatio,1,.8,'high','Current assets / current liabilities','≥1; partial credit ≥0.8'],
  ['quickRatio','Quick Ratio',2,r.quickRatio,.8,.5,'high','(Cash + short-term investments + receivables) / current liabilities','≥0.8; partial credit ≥0.5'],
  ['debtEquity','Debt / Equity',9,r.debtEquity,.5,1,'low','(Long-term + current + short-term debt) / equity','≤0.5; partial credit ≤1'],
  ['liabilitiesEquity','Liabilities / Equity',3,r.liabilitiesEquity,1,2,'low','Total liabilities / equity','≤1; partial credit ≤2'],
  ['fcf','Free Cash Flow',9,r.fcf,0,0,'positive','Operating cash flow − capital expenditure','Positive = full credit'],
  ['cashConversion','Cash Conversion',4,r.cashConversion,1,.8,'high','Operating cash flow / net income','≥1; partial credit ≥0.8'],
  ['interestCoverage','Interest Coverage',2,r.interestCoverage,5,2,'high','Operating income / interest expense','≥5; partial credit ≥2'],
  ['capexIncome','Capex / Net Income',2,r.capexIncome,.25,.5,'low','Capital expenditure / net income','≤25%; partial credit ≤50%'],
  ['retained','Retained Earnings',9,r.retained,0,0,'positive','Accumulated retained earnings','Positive = full credit'],
  ['revenueGrowth','Revenue CAGR',3,cagr(years,'revenue'),.10,0,'high','(Last / first revenue)^(1 / elapsed years) − 1','≥10%; partial credit >0%'],
  ['epsGrowth','EPS CAGR',4,cagr(years,'eps'),.10,0,'high','(Last / first diluted EPS)^(1 / elapsed years) − 1','≥10%; partial credit >0%'],
  ['fcfGrowth','FCF CAGR',3,cagr(years,'fcf'),.20,0,'high','(Last / first FCF)^(1 / elapsed years) − 1','≥20%; partial credit >0%'],
 ];
 const criteria=definitions.map(([key,label,weight,value,good,partial,direction,formula,threshold])=>{
  const available=finite(value);let factor=null;
  if(available)factor=direction==='positive'?(value>0?1:0):direction==='low'?(value<=good?1:value<=partial?.5:0):(value>=good?1:(partial===0?value>0:value>=partial)?.5:0);
  return {key,label,weight,value:available?value:null,factor,points:available?factor*weight:null,formula,threshold};
 });
 const available=criteria.filter(c=>c.factor!==null),weight=available.reduce((a,c)=>a+c.weight,0),points=available.reduce((a,c)=>a+c.points,0);
 return {value:weight?100*points/weight:null,points,weight,totalWeight:criteria.reduce((a,c)=>a+c.weight,0),available:available.length,total:criteria.length,coverage:weight/criteria.reduce((a,c)=>a+c.weight,0),criteria};
}
export function valuation(report,options={}){
 const r=report.years.at(-1), {rate=.10,growth=.05,terminal=.025,method='dcf'}=options;
 if(!['dcf','gordon'].includes(method))throw new Error('INVALID_MODEL');
 if(![rate,growth,terminal].every(finite)||rate<=0||rate>0.5||growth<=-1||terminal<0||terminal>.1||rate<=terminal)throw new Error('INVALID_ASSUMPTIONS');
 if(report.schema==='yahoo39-v1'&&(!report.currency||report.currency==='onbekend'))return {error:'CURRENCY_MISMATCH'};
 const shares=report.valuationShares??r.shares,price=finite(options.price)&&options.price>0?options.price:comparablePrice(report);
 if(method==='gordon'){
  const dividend=dividendInStatementCurrency(report,report.dividendPerShare??r.dps);
  if(dividend===null&&report.dividendCurrency&&report.dividendCurrency!==report.currency)return {error:'CURRENCY_MISMATCH'};
  if(!(dividend>0))return {error:'NO_DIVIDEND'};
  const perShare=dividend*(1+terminal)/(rate-terminal);
  return {method,perShare,total:shares>0?perShare*shares:null,margin:price>0?1-price/perShare:null,price,rows:[],base:dividend,terminalWeight:1};
 }
 // Yahoo uses reported FCFE; legacy SEC reports use the original zero-net-borrowing proxy.
 const base=options.cashFlow ?? (report.schema==='yahoo39-v1'?r.fcfe:r.fcf);
 if(!(finite(base)&&base>0&&shares>0))return {error:'NO_CASHFLOW'};
 const rows=Array.from({length:10},(_,i)=>{const year=i+1,flow=base*Math.pow(1+growth,year);return {year,flow,pv:flow/Math.pow(1+rate,year)};});
 const tv=rows.at(-1).flow*(1+terminal)/(rate-terminal)/Math.pow(1+rate,10),pv=rows.reduce((a,x)=>a+x.pv,0),total=pv+tv,perShare=total/shares;
 if(![total,perShare,tv].every(finite))throw new Error('INVALID_ASSUMPTIONS');
 return {method,base,total,perShare,price,margin:price>0?1-price/perShare:null,rows,terminalPV:tv,terminalWeight:tv/total,shares};
}
