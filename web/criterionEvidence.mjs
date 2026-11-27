// SPDX-License-Identifier: AGPL-3.0-only
import {dateLabel} from './presentation.mjs';
// Presentation only: do not recompute points or infer pass/fail for individual years.
export function evidenceLines(text,hasHistory=false){return String(text||'').split('\n').map(s=>s.trim()).filter(Boolean).filter(s=>!(hasHistory&&/^[↳↪→]?\s*\d{4}-\d{2}-\d{2}.*:/.test(s))).map(s=>({status:/^[✅✓]/u.test(s)?'pass':/^[⛔🚫❌]/u.test(s)?'fail':null,text:s.replace(/^[✅✓⛔🚫❌↳↪→]\s*/u,'').trim()}));}

// Rule descriptions are keyed by the saved method, independent of the source engine's message language.
// Expressions use the financial glossary; explanations and observations use the interface language.
const up='The model rewards increases from one period to the next.';
const down='The model rewards decreases from one period to the next.';
const cash='The model examines whether cash flow stays positive and grows from year to year.';
const growth='The model gives full credit for annualised growth of at least 20% and partial credit for positive growth below 20%.';
const thresholds=(expression,operator,limit,unit='')=>({expression,operator,limit,unit});
export const scoreRules={
 priceToBookValue:{expression:'{Current price} / {Book value per share}',guide:'The model favours a price below book value. The neutral band runs from 1 to 1.5 times book value.'},
 priceToEarningsTTM:{expression:'{Trailing P/E} > {Forward P/E}',guide:'The model compares the historical multiple with the multiple based on expected earnings.'},
 priceToEarningsGrowthTTM:{expression:'{Trailing PEG} > {Forward PEG}',guide:'The model compares historical and expected earnings multiples adjusted for growth.'},
 evToEbitda:{expression:'0 ≤ EV/EBITDA < 4'},
 returnOnEquityHistory:thresholds('{Net income} / {Shareholders’ equity / book value}','>',15,'%'),
 returnOnNetTangibleAssetsHistory:thresholds('{Net income} / {Net tangible assets}','>',15,'%'),
 returnOnAssetsHistory:thresholds('{Net income} / {Total assets}','>',1,'%'),
 daysInventoryOnHandHistory:{expression:'365 × {Average inventory} / {Cost of revenue}',guide:down},
 inventoryTurnoverHistory:{expression:'{Cost of revenue} / {Average inventory}',guide:up},
 daysReceivablesOutstandingHistory:{expression:'365 × {Average receivables} / {Revenue}',guide:down},
 receivablesTurnoverHistory:{expression:'{Revenue} / {Average receivables}',guide:up},
 daysPayablesOutstandingHistory:{expression:'365 × {Average payables} / {Cost of revenue}',guide:up},
 payablesTurnoverHistory:{expression:'{Cost of revenue} / {Average payables}',guide:down},
 cashConversionCycleHistory:{expression:'DIO + DSO − DPO',guide:'The model favours a negative or shortening cash conversion cycle.'},
 grossProfitMarginHistory:thresholds('{Gross profit} / {Revenue}','≥',40,'%'),
 netProfitMarginHistory:thresholds('{Net income} / {Revenue}','≥',20,'%'),
 retainedEarningsHistory:{expression:'{Retained earnings}',guide:up},
 netEarningsTocommonHistory:{expression:'{Inventory} · {Net Income to Common Shareholders}',guide:'The model checks whether inventories and earnings attributable to common shareholders rise together.'},
 earningsPerShareHistory:{expression:'{Diluted earnings per share}',guide:up},
 sellingGeneralAdministrativeMarginHistory:thresholds('{Selling, general & administrative expenses} / {Gross profit}','<',30,'%'),
 researchAndDevelopmentHistory:thresholds('{Research & development} / {Gross profit}','<',30,'%'),
 capexToEarningsHistory:thresholds('{Capital expenditure} / {Net income}','<',50,'%'),
 depreciationMarginHistory:thresholds('{Depreciation & amortisation} / {Gross profit}','<',10,'%'),
 interestExpenseMarginHistory:thresholds('{Interest expense} / {Operating income}','<',10,'%'),
 netReceivablesMarginHistory:thresholds('{Net receivables} / {Revenue}','<',20,'%'),
 currentRatioHistory:thresholds('{Total current assets} / {Total current liabilities}','≥',1),
 quickRatioHistory:thresholds('({Cash & equivalents} + {Short-term investments} + {Net receivables}) / {Total current liabilities}','≥',0.8),
 totalCashToMonthlyOperatingExpensesHistory:thresholds('{Cash & equivalents} / ({Operating expenses} / 12)','≥',3,'months'),
 debtToEquityHistory:thresholds('{Interest-bearing debt} / {Shareholders’ equity / book value}','≤',50,'%'),
 totalLiabilityToEquityHistory:thresholds('{Total liabilities} / {Shareholders’ equity / book value}','≤',80,'%'),
 netBorrowingsHistory:{expression:'{Net Borrowings} · {Net Borrowings} / {Operating cash flow}',guide:'This series shows the contribution of net borrowing to cash flow. It carries no points.'},
 freeCashFlow:{expression:'{Operating cash flow} − {Capital expenditure}',guide:cash},
 freeCashFlowCAGR:{expression:'{Free Cash Flow — CAGR}',guide:growth},
 freeCashFlowToFirm:{expression:'{Free cash flow} + {After-tax interest}',guide:cash},
 freeCashFlowToFirmCAGR:{expression:'{FCFF — CAGR}',guide:growth},
 freeCashFlowToEquity:{expression:'{Free cash flow} + {Net Borrowings}',guide:cash},
 freeCashFlowToEquityCAGR:{expression:'{FCFE — CAGR}',guide:growth},
 buyBacksHistory:{expression:'{Share Buybacks}',guide:'The model examines how regularly the company repurchases shares.'},
 dividendsHistory:{expression:'{Dividends paid} · {Dividends per Share}',guide:'The model checks for annual payments and evaluates dividend growth per share over completed calendar years.'}
};

// Before Yahoo's 39-rule model, saved SEC analyses used sixteen single-value tests.
const legacyRules={
 roe:['{Net income} / {Shareholders’ equity / book value}','≥15%', '>0%'],
 roa:['{Net income} / {Total assets}','≥1%', '>0%'],
 grossMargin:['{Gross profit} / {Revenue}','≥40%','≥20%'],
 netMargin:['{Net income} / {Revenue}','≥20%','≥10%'],
 currentRatio:['{Total current assets} / {Total current liabilities}','≥1','≥0.8'],
 quickRatio:['({Cash & equivalents} + {Short-term investments} + {Net receivables}) / {Total current liabilities}','≥0.8','≥0.5'],
 debtEquity:['{Interest-bearing debt} / {Shareholders’ equity / book value}','≤0.5','≤1'],
 liabilitiesEquity:['{Total liabilities} / {Shareholders’ equity / book value}','≤1','≤2'],
 fcf:['{Operating cash flow} − {Capital expenditure}','>0'],
 cashConversion:['{Operating cash flow} / {Net income}','≥1','≥0.8'],
 interestCoverage:['{Operating income} / {Interest expense}','≥5','≥2'],
 capexIncome:['{Capital expenditure} / {Net income}','≤25%','≤50%'],
 retained:['{Retained earnings}','>0'],
 revenueGrowth:['{Revenue} · CAGR','≥10%','>0%'],
 epsGrowth:['{Diluted earnings per share} · CAGR','≥10%','>0%'],
 fcfGrowth:['{Free cash flow} · CAGR','≥20%','>0%']
};

const terms=(expression,t)=>expression.replace(/\{([^}]+)\}/g,(_,term)=>t.term(term));
export function criterionDescription(criterion,t){
 const rule=scoreRules[criterion.key];
 if(!rule){
  const legacy=legacyRules[criterion.key];
  if(!legacy)return t(criterion.label);
  const [expression,full,partial]=legacy;
  const localLimit=v=>v.replace(/\d+(?:\.\d+)?/g,match=>new Intl.NumberFormat(t.language).format(Number(match)));
  return [terms(expression,t),t('Full points')+' '+localLimit(full),partial&&t('Partial points')+' '+localLimit(partial)].filter(Boolean).join(' · ');
 }
 const expression=terms(rule.expression,t);
 const threshold=rule.operator?' '+rule.operator+' '+new Intl.NumberFormat(t.language).format(rule.limit)+(rule.unit==='months'?' '+t('months'):rule.unit):'';
 return [expression+threshold,rule.guide&&t(rule.guide)].filter(Boolean).join(' · ');
}

const withinThreshold={
 '>':(value,limit)=>value>limit, '≥':(value,limit)=>value>=limit,
 '<':(value,limit)=>value<limit, '≤':(value,limit)=>value<=limit
};

export function criterionFindings(c,history,t,number){
 if(c.available===false||c.factor===null)return [t('Too few usable observations to assess this rule.')];
 const findings=[];
 const text=evidenceLines(c.threshold,!!history?.pairs?.length).map(line=>line.text).join('\n');
 // Older files store only the source message for market multiples and CAGR. Extract its
 // numeric evidence rather than displaying mixed-language messages or recomputing the rule.
 if(['priceToBookValue','priceToEarningsTTM','priceToEarningsGrowthTTM','evToEbitda'].includes(c.key)){
  const values=text.match(/\((-?\d+(?:\.\d+)?)(?:\s*([<>≤≥=])\s*(-?\d+(?:\.\d+)?))?\)/);
  if(values)findings.push(t('Observed value')+' · '+number(+values[1])+(values[2]?' '+values[2]+' '+number(+values[3]):''));
 }
 const cagr=text.match(/CAGR over ([\d.]+) jaar:\s*(-?[\d.]+)%/);
 if(cagr)findings.push(t('Observed value')+' · '+number(+cagr[2])+'% · '+number(+cagr[1])+' '+t('years'));
 // Describe the actual displayed series. This is separate from the source model's points,
 // which may combine several threshold and trend checks (including TTM data).
 const observations=(history?.pairs||[]).filter(([,v])=>Number.isFinite(v)).sort(([a],[b])=>a.localeCompare(b));
 if(observations.length>1){
  const values=observations.map(([,value])=>value);
  const rule=scoreRules[c.key];
  if(rule?.operator){
   const meets=v=>withinThreshold[rule.operator](v,rule.limit);
   const count=values.filter(meets).length, last=observations.at(-1);
   const period=/^\d{4}-\d{2}-\d{2}$/.test(last[0])?dateLabel(last[0],t.language):last[0].includes('TTM')?t('Yahoo current/TTM'):last[0];
   findings.push(t(count===values.length?'The threshold was met throughout the assessed periods.':'At least one assessed period fell outside the threshold.')+' '+t('Pass')+' · '+count+' / '+values.length+'. '+period+' · '+t(meets(last[1])?'Pass':'Fail')+'.');
  }
  if(rule?.guide===cash){
   const positive=values.filter(value=>value>0).length,negative=values.filter(value=>value<0).length;
   if(positive===values.length)findings.push(t('Cash flow was positive in every assessed period.'));
   else findings.push(t('Cash flow was zero or negative in at least one assessed period.')+' (> 0 · '+positive+' / '+values.length+', = 0 · '+(values.length-positive-negative)+' / '+values.length+', < 0 · '+negative+' / '+values.length+')');
  }
  const rising=values.slice(1).every((v,i)=>v>values[i]), falling=values.slice(1).every((v,i)=>v<values[i]);
  const flat=values.every(v=>v===values[0]);
  const pattern=rising?'The series rose in every period.':falling?'The series fell in every period.':flat?'The series was unchanged.':
   values.slice(1).every((v,i)=>v>=values[i])?'The series rose or held steady in each period.':
   values.slice(1).every((v,i)=>v<=values[i])?'The series fell or held steady in each period.':
   values.at(-1)>values[0]?'The series ended higher, with interruptions along the way.':
   values.at(-1)<values[0]?'The series ended lower, with interruptions along the way.':'The series returned to its starting level.';
  findings.push(t(pattern));
 }
 if(c.weight>0)findings.push(t(c.points===c.weight?'The source model awards full points.':c.points>0?'The source model awards partial points.':'The source model awards no points.'));
 else findings.push(t('Available · unweighted'));
 return findings;
}
