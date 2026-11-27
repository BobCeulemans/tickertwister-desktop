// SPDX-License-Identifier: AGPL-3.0-only
const components={
 roe:['Net income','Book value / equity'],roa:['Net income','Total assets'],grossMargin:['Gross profit','Revenue'],netMargin:['Net income','Revenue'],
 fcfMargin:['Free cash flow','Revenue'],currentRatio:['Total current assets','Total current liabilities'],quickRatio:[['Cash & equivalents','Short-term investments','Receivables'],'Total current liabilities'],
 debtEquity:['Total debt','Book value / equity'],liabilitiesEquity:['Total liabilities','Book value / equity'],interestCoverage:['Operating income','Interest expense'],
 cashConversion:['Operating cash flow','Net income'],assetTurnover:['Revenue','Total assets'],capexIncome:['Capital expenditure','Net income'],dividendCoverage:['Free cash flow','Dividends paid'],
 dio:['Inventory','Cost of revenue'],dso:['Receivables','Revenue'],dpo:['Accounts payable','Cost of revenue'],
};
export default function RatioFormulas({rows,t}){
 function formula(key,unit){
  if(key==='ccc')return 'DIO + DSO − DPO';
  const [numerator,denominator]=components[key];
  const top=Array.isArray(numerator)?'('+numerator.map(label=>t.term(label)).join(' + ')+')':t.term(numerator);
  return top+' ÷ '+t.term(denominator)+(unit==='%'?' × 100':unit==='d'?' × 365':'');
 }
 return <details className="ratio-formulas"><summary>{t('Ratio formulas')}</summary><dl>{rows.map(([key,label,unit])=><div key={key}><dt>{t.term(label)}</dt><dd>{formula(key,unit)}</dd></div>)}</dl></details>;
}
