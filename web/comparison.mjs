// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
// Period-aligned figures, separate from the original multi-year 39-criterion score.
import {finite} from './finance.mjs';
export const ratio=(a,b)=>finite(a)&&finite(b)&&b>0?a/b:null;
const sum=(...v)=>v.every(finite)?v.reduce((a,b)=>a+b,0):null;
const flows='revenue income gross cost operating interest sga rd opex pretax tax assetSalesGain otherIncome da taxPaid cfo capex netBorrowings dividends buybacks cfi cff stockIssued eps'.split(' ');
const serial=k=>Number(k.slice(0,4))*4+Number(k.slice(-1))-1;
export function periods(report){
 const result=new Map();
 for(const y of report.years||[])result.set('FY:'+y.end,{...y,periodType:'annual',periodStart:null});
 const q=(report.quarters||[]).slice().sort((a,b)=>a.end.localeCompare(b.end));
 for(const y of q){
  result.set('Q:'+y.periodKey,{...y,periodType:'quarter'});
  const window=q.filter(r=>serial(r.periodKey)<=serial(y.periodKey)&&serial(r.periodKey)>serial(y.periodKey)-4);
  if(window.length!==4||new Set(window.map(r=>r.periodKey)).size!==4)continue;
  const row={...y,periodType:'ttm',periodStart:window[0].end};
  for(const key of flows)row[key]=sum(...window.map(r=>r[key]));
  row.fcf=finite(row.cfo)&&finite(row.capex)?row.cfo-row.capex:null;
  row.fcfe=sum(row.fcf,row.netBorrowings);
  result.set('TTM:'+y.periodKey,row);
 }
 for(const [key,y] of result){
  const priorKey=key.replace(/(\d{4})/,year=>String(Number(year)-1)),prior=result.get(priorKey);
  for(const field of ['eps','retained','income','revenue'])y[field+'YoY']=prior&&finite(y[field])&&finite(prior[field])&&prior[field]>0?y[field]/prior[field]-1:null;
 }
 return result;
}
export function commonPeriods(reports){
 if(reports.length<1)return [];
 const maps=reports.map(periods);
 const matched=[...maps[0].keys()].filter(k=>maps.every(m=>m.has(k))).sort((a,b)=>{
  const type=k=>k.startsWith('TTM:')?0:k.startsWith('Q:')?1:2;
  return type(a)-type(b)||b.localeCompare(a);
 }).map(key=>({key,rows:maps.map(m=>m.get(key))}));
 const long=maximumHistory(reports);return long?[...matched,long]:matched;
}
export const groups=[['core','Belangrijkste verhoudingen','Key ratios'],['income','Resultatenrekening','Income statement'],['balance','Balans','Balance sheet'],['cash','Kasstroomoverzicht en uitkeringen','Cash flow statement and distributions']];
export const metrics=[];
const add=(group,key,label,unit,formula,chapter,value)=>metrics.push({group,key,label,unit,formula,chapter,value});
const raw=(g,k,l,c)=>add(g,k,l,'money',l+' (reported; no estimate)',c,y=>y[k]);
const div=(g,k,l,a,b,c,unit='%')=>add(g,k,l,unit,`${a} / ${b}${unit==='%'?' × 100%':''}`,c,y=>ratio(y[a],y[b]));
div('core','roe','Return on equity (ROE)','income','equity','47–48');
div('core','roa','Return on assets (ROA)','income','assets','34');
div('core','grossMargin','Gross profit margin','gross','revenue','10');
div('core','netMargin','Net profit margin','income','revenue','19');
div('core','currentRatio','Current ratio','currentAssets','currentLiabilities','28, 39','×');
div('core','debtEquity','Debt / equity · interest-bearing debt','debt','equity','42 (alternative definition)');
div('core','liabilitiesEquity','Liabilities / equity · book definition','liabilities','equity','42');
div('core','cashConversion','CFO / net income','cfo','income','50','×');
for(const [k,l,c] of [['revenue','Revenue',8],['cost','Cost of revenue',9],['gross','Gross profit',10],['opex','Operating expenses',11],['sga','Selling, general & administrative expenses',12],['rd','Research & development',13],['da','Depreciation & amortisation',14],['operating','Operating income',11],['interest','Interest expense',15],['assetSalesGain','Gains / losses on asset sales',16],['otherIncome','Other non-operating income / expenses',16],['pretax','Pretax income',17],['tax','Income tax expense',18],['income','Net income',19]])raw('income',k,l,c);
div('income','sgaGross','SG&A / gross profit','sga','gross',12);div('income','rdGross','R&D / gross profit','rd','gross',13);div('income','daGross','D&A / gross profit','da','gross',14);div('income','interestOperating','Interest / operating income','interest','operating',15);div('income','effectiveTax','Effective tax rate','tax','pretax',18);
add('income','eps','Diluted earnings per share','perShare','Reported diluted EPS; TTM = sum of four quarterly EPS (rounding possible)',20,y=>y.eps);
for(const [k,l,c] of [['cash','Cash & equivalents',24],['investments','Short-term investments',24],['inventory','Inventory',25],['receivables','Net receivables',26],['prepaid','Prepaid expenses',27],['otherCurrentAssets','Other current assets',27],['currentAssets','Total current assets',28],['ppe','Property, plant & equipment · net',29],['goodwill','Goodwill',30],['intangibles','Other intangible assets',31],['longInvestments','Long-term investments & advances',32],['otherLongAssets','Other non-current assets',33],['assets','Total assets',34],['payables','Accounts payable',36],['accrued','Accrued expenses',36],['otherCurrentLiabilities','Other current liabilities',36],['currentDebt','Current debt',37],['longDebtCurrent','Current portion of long-term debt',38],['currentLiabilities','Total current liabilities',39],['longDebt','Long-term debt',40],['deferredTax','Non-current deferred tax liabilities',41],['minorityInterest','Non-controlling interests',41],['otherLiabilities','Other non-current liabilities',41],['liabilities','Total liabilities',42],['debt','Interest-bearing debt',42],['equity','Shareholders’ equity / book value',43],['preferredStock','Preferred stock',44],['commonStock','Common stock',44],['paidInCapital','Additional paid-in capital',44],['retained','Retained earnings',45],['treasuryStock','Treasury stock · carrying amount',46]])raw('balance',k,l,c);
div('balance','receivablesSales','Receivables / revenue','receivables','revenue',26);
div('balance','longDebtIncome','Long-term debt / net income','longDebt','income',40,'×');
div('balance','leverage','Financial leverage','assets','equity',49,'×');
div('balance','bookPerShare','Book value per share','equity','shares',43,'perShare');
add('balance','adjustedDebt','Liabilities / treasury-adjusted equity','%','liabilities / (equity + absolute treasuryStock carrying amount) × 100%; missing treasury stock ≠ zero',42,y=>ratio(y.liabilities,sum(y.equity,finite(y.treasuryStock)?Math.abs(y.treasuryStock):null)));
add('balance','adjustedRoe','Treasury-adjusted ROE','%','income / (equity + absolute treasuryStock carrying amount) × 100%',47,y=>ratio(y.income,sum(y.equity,finite(y.treasuryStock)?Math.abs(y.treasuryStock):null)));
for(const [k,l,c] of [['cfo','Operating cash flow',50],['cfi','Investing cash flow',50],['cff','Financing cash flow',50],['taxPaid','Cash income taxes paid',18],['capex','Capital expenditure',51],['fcf','Free cash flow',51],['buybacks','Share buybacks · cash outflow',52],['stockIssued','Stock issuance · cash inflow',52],['dividends','Dividends paid',52]])raw('cash',k,l,c);
div('cash','capexIncome','Capex / net income · selected period','capex','income',51);
div('cash','pretaxPerShare','Pretax earnings per share · period-end shares','pretax','shares','53–54','perShare');
for(const [key,label,chapter] of [['eps','Diluted EPS · year-on-year growth',20],['retained','Retained earnings · year-on-year growth',45],['income','Net income · year-on-year growth',19],['revenue','Revenue · year-on-year growth',8]])add('cash',key+'YoY',label,'%',`(${key} / same period one year earlier − 1) × 100%; positive prior value required`,chapter,y=>y[key+'YoY']);
export function interpret(reports,period,t,number,percent){
 const out=[];
 out.push(t("Period: ")+period.key+'. '+t("This is a rule-based summary, not a language model or a buy recommendation."));
 if(period.key.startsWith('LONG:'))out.push(t("Long-term view: ratios use mean annual figures. Fiscal year ends may differ by up to 190 days; these windows are approximately comparable, not a replacement for matched quarters."));
 reports.forEach((r,i)=>{const y=period.rows[i],get=k=>metrics.find(m=>m.key===k).value(y),missing=metrics.filter(m=>!finite(m.value(y))).length;
  const parts=[`ROA ${percent(get('roa'))}`,`ROE ${percent(get('roe'))}`,`net margin ${percent(get('netMargin'))}`,`debt/equity ${percent(get('debtEquity'))}`];
  if(finite(y.income)&&y.income<=0)parts.push(t("loss or zero profit; earnings-based coverage ratios are not meaningful"));
  if(finite(y.equity)&&y.equity<=0)parts.push(t("non-positive equity: review solvency separately"));
  const c=get('cashConversion');if(finite(c))parts.push(c<1?t("CFO trails earnings; investigate working capital and one-offs"):t("CFO covers reported earnings in this period"));
  const liq=get('currentRatio');if(finite(liq)&&liq<1)parts.push(t("current ratio below 1; assess working capital in sector context"));
  out.push(r.symbol+': '+parts.join(' · ')+'. '+missing+'/'+metrics.length+t(" metrics unavailable."));
 });
 const sectors=new Set(reports.map(r=>r.sector||'?'));if(sectors.size>1||sectors.has('?'))out.push(t("Sectors differ or are missing: margins and leverage do not form a direct ranking."));
 if(new Set(reports.map(r=>r.currency)).size>1)out.push(t("Different reporting currencies: absolute amounts have not been converted."));
 out.push(t("Conclusion: use this comparison to choose questions for further research. Check annual reports, earnings quality, capital needs and valuation assumptions. A single period does not establish a durable competitive advantage."));
 return out;
}

export function formulaText(metric){const labels=Object.fromEntries(metrics.filter(m=>m.unit==='money').map(m=>[m.key,m.label]));Object.assign(labels,{eps:'Diluted EPS',shares:'Period-end ordinary shares',treasuryStock:'Treasury stock',fcf:'Free cash flow'});return metric.formula.replace(/\b[A-Za-z]+\b/g,word=>labels[word]||word);}

// Compare the longest common annual window (max 5 observations), with explicit
// fiscal-calendar tolerance. Annual means, never multi-year profit / one balance.
export function maximumHistory(reports){
 if(reports.length<1)return null;
 const all=reports.map(r=>(r.years||[]).slice().sort((a,b)=>a.end.localeCompare(b.end)));
 const day=s=>Date.parse(s+'T00:00:00Z')/86400000,spread=dates=>Math.max(...dates.map(day))-Math.min(...dates.map(day));
 for(let n=Math.min(5,...all.map(a=>a.length));n>=2;n--){
  const windows=all.map(a=>a.map((_,i)=>a.slice(i,i+n)).filter(w=>w.length===n&&w.every((y,i)=>!i||(day(y.end)-day(w[i-1].end)>=330&&day(y.end)-day(w[i-1].end)<=400))));
  let best=null;
  function visit(chosen,i){if(i===windows.length){if(spread(chosen.map(w=>w[0].end))>190||spread(chosen.map(w=>w.at(-1).end))>190)return;const freshness=Math.min(...chosen.map(w=>day(w.at(-1).end)));if(!best||freshness>best.freshness)best={chosen,freshness};return;}for(const w of windows[i])visit([...chosen,w],i+1);}
  visit([],0);if(!best)continue;
  const rows=best.chosen.map(w=>{const result={periodType:'longterm',periodStart:w[0].end,end:w.at(-1).end,observations:n};
   const keys=new Set(w.flatMap(Object.keys));for(const k of keys){if(['end','periodType','periodKey'].includes(k))continue;const values=w.map(y=>y[k]);result[k]=values.every(finite)?values.reduce((a,b)=>a+b,0)/n:null;}
   for(const f of ['eps','retained','income','revenue'])result[f+'YoY']=w[0][f]>0&&w.at(-1)[f]>0?(w.at(-1)[f]/w[0][f])**(365.25/(day(w.at(-1).end)-day(w[0].end)))-1:null;
   return result;
  });return {key:'LONG:'+n,rows,observations:n};
 }
 return null;
}
