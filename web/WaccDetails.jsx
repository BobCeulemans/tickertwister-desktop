// SPDX-License-Identifier: AGPL-3.0-only
import {dateLabel} from './presentation.mjs';
import {treasuryReference} from './valuation.mjs';

export function capitalPrecision(value,language) {
 return Number.isFinite(value) ? new Intl.NumberFormat(language,{maximumSignificantDigits:12}).format(value) : '—';
}
export function capitalPercent(value,language) {
 return Number.isFinite(value) ? new Intl.NumberFormat(language,{minimumFractionDigits:2,maximumFractionDigits:2}).format(value*100)+'%' : '—';
}

export default function WaccDetails({wacc:w,field,t,currency}){
 const term=t.term, precision=x=>capitalPrecision(x,t.language), pct=x=>Number.isFinite(x)?precision(x*100)+'%':'—';
 const money=x=>Number.isFinite(x)?precision(x)+' '+currency:'—';
 const treasury=treasuryReference(w.riskObservation);
 const row=(label,value,formula)=><tr key={label}><th scope="row">{label}</th><td>{value}</td><td>{formula}</td></tr>;
 const asOf=w.flowBasis ? w.flowBasis+' · '+dateLabel(w.fiscalDate,t.language) : t('Matching trailing twelve months unavailable.');
 const statutory=w.taxBenchmark;
 return <details className="valuation-wacc"><summary>{term(w.equityOnly?'Cost of equity (Re)':'Weighted average cost of capital')} · {w.equityOnly?pct(w.rate):capitalPercent(w.rate,t.language)} · {currency}</summary>
  <p><strong>{w.equityOnly?'Rₑ = Rf + β × ERP':'WACC = (E/V) × Rₑ + (D/V) × Rd × (1 − T)'}</strong></p>
  <div className="table-scroll"><table><thead><tr><th>{t('Parameter')}</th><th>{t('Value')}</th><th>{t('Source')} / {t('Formula')}</th></tr></thead>
   <tbody>
    {!w.equityOnly&&<>
     {row('E',money(w.equity),term('Market capitalisation'))}
     {row('D',money(w.debt),term('Total debt')+' · '+dateLabel(w.balanceDate,t.language))}
     {row('V',money(w.total),'E + D')}
     {row('E/V',pct(w.equityWeight),'E / (E + D)')}
     {row('D/V',pct(w.debtWeight),'D / (E + D)')}
    </>}
    {row('Rf',pct(w.riskFree),<>{treasury?<a href={treasury.url} target="_blank" rel="noreferrer">{treasury.label} ↗</a>:currency} · {dateLabel(w.riskObservation?.date,t.language)}</>)}
    {row('β',precision(w.beta),w.personalBeta?term('Personal beta (optional)'):term('Beta (5Y monthly)'))}
    {row('ERP',pct(w.premium),t('Assumed equity risk premium'))}
    {row('Rₑ',pct(w.equityCost),'Rf + β × ERP')}
    {!w.equityOnly&&<>
     {row(term('Interest expense'),money(w.interest),asOf)}
     {row('Rd',pct(w.debtCost),w.debt===0?'D = 0':<>{w.debtCostAssumed?'Rf + 1.5%':term('Interest expense')+' / D = '+pct(w.rawDebtCost)} · Rf ≤ Rd ≤ Rf + 10%</>)}
     {row(term('Income tax expense'),money(w.incomeTax),asOf)}
     {row(term('Pre-tax income'),money(w.pretax),asOf)}
     {row('T',pct(w.tax),<>{w.taxAssumed?<>{t(statutory.source?'Country tax assumption':'General tax assumption')}{statutory.source&&<> · {w.country} · <a href={statutory.url} target="_blank" rel="noreferrer">{statutory.source} ↗</a></>}</>:term('Income tax expense')+' / '+term('Pre-tax income')} = {pct(w.rawTax)} · 0% ≤ T ≤ 35%</>)}
    </>}
   </tbody></table></div>
  <div className="input-grid">{field('waccBeta',term('Personal beta (optional)'))}</div>
  <p>{t('An empty beta field uses Yahoo’s five-year monthly beta.')}</p>
 </details>;
}
