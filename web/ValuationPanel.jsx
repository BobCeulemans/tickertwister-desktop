// SPDX-License-Identifier: AGPL-3.0-only
import React from 'react';
import {calculateValuation, riskFreeObservation, defaultValuation, minimumDiscountRate, treasuryReference, valuationMarket, valuationSources, historicalGrowthBand, historicalOwnerEarnings, equityDiscountInput, financialDiscountInput, waccEstimate} from './valuation.mjs';
import './valuation.css';
import {dateLabel,shortAmount} from './presentation.mjs';
import {finite} from './finance.mjs';
import GrowthComparison from './GrowthComparison.jsx';
import Sensitivity from './Sensitivity.jsx';
import DiscountRateInput from './DiscountRateInput.jsx';
import WaccDetails,{capitalPercent,capitalPrecision} from './WaccDetails.jsx';
import ValuationFormulas from './ValuationFormulas.jsx';

export default function ValuationPanel({legacy,report,inputs,onInputs,method,onMethod,t,number,percent}){
 const dcf=method==='dcf', value=calculateValuation(report,inputs,method), data=valuationSources(report);
 const benchmark=riskFreeObservation(report,'cashFlow'), treasury=treasuryReference(benchmark), minimum=minimumDiscountRate(report);
 const market=valuationMarket(report);
 const listedYield=market.currency!==report.currency?riskFreeObservation(report):null;
 const listedSource=treasuryReference(listedYield);
 const term=t.term;
 const wacc=waccEstimate(report,inputs.waccBeta,'cashFlow');
 const waccPercent=finite(wacc.rate)?wacc.rate*100:null;
 const estimates=dcf?historicalOwnerEarnings(report).filter(y=>finite(y.ownerEarnings)&&y.assumedZero.length):[];
 const amount=(n,currency=report.currency)=>finite(n)?shortAmount(n,number,term)+' '+currency:'—';
 const money=(n,currency=report.currency)=>finite(n)?number(n)+' '+currency:'—';
 const field=(key,label,step='any')=>{
  const Input=key==='rate'&&!wacc.equityOnly?DiscountRateInput:'input';
  return <label>{label}<Input type="number" step={step}
   min={key==='rate'&&!wacc.equityOnly?minimum:undefined} value={inputs[key]??''} onChange={e=>{
    const next={...inputs,[key]:e.target.value};
    if(key==='rate'&&wacc.equityOnly)next.personalEquityRate=true;
    if(key==='waccBeta'){
     if(wacc.equityOnly&&!inputs.personalEquityRate)next.rate=equityDiscountInput(report,next.waccBeta);
     if(data.sector==='financial'&&inputs.rate===financialDiscountInput(report,inputs.waccBeta))next.rate=financialDiscountInput(report,next.waccBeta);
    }
    onInputs(next);
   }}/></label>;
 };
 const inMillions=' ('+term('million')+' '+report.currency+')';
 const row=(label,text)=><React.Fragment key={label}><dt>{term(label)}</dt><dd>{text}</dd></React.Fragment>;
 const directEquity=data.sector==='bank'||data.sector==='insurance';
 const band=dcf?historicalGrowthBand(report):null;
 const earningsBreakdown=[
  ['Net income',data.netIncome],
  ...(directEquity?[]:[['Depreciation & amortisation',data.depreciation],
   data.sector==='financial'?['Capital expenditure',data.capex]:['Maintenance capex estimate',data.maintenanceCapex]]),
  ...(data.sector==='other'?[['Working capital cash effect',data.workingCapitalCashEffect]]:[]),
  ['Owner earnings',data.ownerEarnings]
 ];
 return <section className="valuation card primary-valuation" id="valuation">
  <div className="section-heading"><div className="eyebrow">{t('Value and price')}</div><h2>{t('What is the business worth to you?')}</h2></div>
  <div className="scenario-tabs"><button aria-pressed={dcf} onClick={()=>onMethod('dcf')}>{term('Owner earnings · DCF')}</button><button aria-pressed={!dcf} onClick={()=>onMethod('gordon')}>Gordon Growth</button></div>
  {legacy&&<p className="method-note">{t('The current model uses this earlier snapshot. Review the assumptions behind the recalculated value.')}</p>}
  <div className="valuation-grid"><div>
   {!dcf&&<p>{t('Optional dividend model for mature businesses with a sustainable, stable dividend policy. A low dividend does not imply a low total business value.')}</p>}
   <div className="input-grid">
    {dcf?<>{field('ownerEarnings',term('Starting owner earnings')+inMillions)}{field('growth',term('Annual owner earnings growth (%)'))}</>:field('dividend',term('Annual dividend per share · D0'))}
    {field('rate',term(wacc.equityOnly?'Cost of equity (Re)':'Discount rate (%)')+(wacc.equityOnly?' (%)':'')+(wacc.equityOnly&&inputs.personalEquityRate?' · '+t('Personal assumption'):''))}{field('terminal',term('Perpetual growth (%)'))}
   </div>
   <p className="valuation-footnote">{dcf?<>{t('Projection years')} · 10</>:t('D1 = D0 × (1 + perpetual growth). Value per share = D1 / (discount rate − perpetual growth).')} {!wacc.equityOnly&&<> · {term('Minimum discount rate')} · {number(minimum)}%</>}</p>
   <div className="wacc-reference"><span>{term(wacc.equityOnly?'Cost of equity (Re)':'Weighted average cost of capital')}{wacc.equityOnly&&' · CAPM'} <strong>{wacc.equityOnly&&waccPercent!==null?capitalPrecision(waccPercent,t.language)+'%':capitalPercent(wacc.rate,t.language)}</strong> · {report.currency}</span>
    {wacc.equityOnly&&inputs.personalEquityRate&&<button onClick={()=>onInputs({...inputs,personalEquityRate:false,rate:equityDiscountInput(report,inputs.waccBeta)})}>{t('Use CAPM')}</button>}
    {!wacc.equityOnly&&waccPercent!==null&&waccPercent>=minimum&&waccPercent<=100&&<button onClick={()=>onInputs({...inputs,rate:data.sector==='financial'?financialDiscountInput(report,inputs.waccBeta):String(waccPercent)})}>{t('Use WACC')}</button>}
   </div>
   {wacc.equityOnly&&<p className="valuation-footnote">{t('Banks and insurers use the cost of equity. Deposits and policy liabilities fund their core operations.')}</p>}
   {waccPercent===null&&!wacc.equityOnly&&<p className="valuation-footnote">{t('See the WACC inputs in Sources and assumptions.')}</p>}
   <button onClick={()=>onInputs(defaultValuation(report))}>{t('Restore initial values')}</button>
   {dcf&&<GrowthComparison report={report} inputs={inputs} t={t} number={number} percent={percent}/>}
  </div><div>
   <details className="valuation-assumptions"><summary>{t('Sources and assumptions')}</summary>
    <WaccDetails wacc={wacc} field={field} t={t} currency={report.currency}/>
    <ValuationFormulas t={t} dcf={dcf} sector={data.sector}/>
    {!value.error&&<dl className="valuation-steps">
     {dcf?<>{row('Present value · years 1–10',money(value.projectionPV))}
      {row('Terminal value · year 10',money(value.terminalValue))}
      {row('Present value · terminal value',money(value.terminalPV))}
      {!directEquity&&<>{row('Enterprise value',money(value.enterpriseValue))}{row('Net debt',money(value.netDebt))}</>}</>:row('Next annual dividend · D1',money(value.dividendNext))}
     {row('Model equity value',money(value.equityValue))}
     {row('Outstanding shares',number(value.shares,0))}
     {row('Model value per share',money(value.perShare))}
    </dl>}
    {dcf&&<>
     <p>{directEquity?t('Bank and insurance earnings are an equity cash flow proxy. Capital requirements can limit how much can be distributed.'):data.sector==='financial'?t('Financial services use net income plus depreciation and amortisation less total capital expenditure. Working capital movements are excluded.'):t('Owner earnings equal net income plus depreciation and amortisation, less maintenance capex, plus the signed cash effect of working capital.')}</p>
     {data.sector==='other'&&<p>{t('Maintenance capex is estimated as the lower of depreciation and total capex. You can enter your own estimate of starting owner earnings.')}</p>}
     <table><caption>{term('Latest fiscal year')} · {dateLabel(data.ownerEarningsDate,t.language)} · {report.currency}</caption>
      <tbody>{earningsBreakdown.map(([key,n])=><tr key={key}><th scope="row">{term(key)}</th><td>{number(n)}</td></tr>)}</tbody></table>
     {finite(data.average)&&<p>{t('Three-year average')} · {amount(data.average)}. {data.normalized&&t('Starting earnings use the three-year average because the latest year differs by more than 30%.')}</p>}
     {estimates.length>0&&<div className="valuation-imputation"><strong>{t('Model-only zero assumptions')}</strong>
      {estimates.map(y=><p key={y.end}>{dateLabel(y.end,t.language)} · {y.assumedZero.map(termKey=>term(termKey)).join(', ')}</p>)}
     </div>}
     <p>{data.sector==='other'
       ?t('Growth uses the mean of available comparable CAGRs. When owner earnings growth is more than 10 percentage points above or below both revenue and income growth, net income growth is used. The range caps are 10% and 12%, with a −20% floor.')
       :t('For financial companies, historical revenue growth is the starting assumption. If unavailable, the model uses net income growth, then owner earnings growth. The caps are 10% and 12%, with a −20% floor.')}</p>
     {band.suggestedPeriod&&<p>{band.suggestedPeriod} · {term('Revenue CAGR')} {percent(band.comparable.sales)} · {term('Net income CAGR')} {percent(band.comparable.ni)}{!directEquity&&<> · {term('Historical owner earnings growth')} {percent(band.comparable.oe)}</>}</p>}
     <div className="input-grid">{!directEquity&&field('netDebt',term('Net debt')+inMillions)}{field('shares',term('Outstanding shares'),'1')}</div>
     {!directEquity&&<><p>{term('Net debt')} · {dateLabel(data.balanceDate,t.language)} · {amount(data.netDebt)}. {t('Net debt equals reported debt less cash and cash equivalents. Check lease coverage in the annual report.')}</p>
     <p>{t('This model deducts net debt from discounted owner earnings after interest. This additional deduction can count financing costs twice.')}</p></>}
    </>}
    {!dcf&&<div className="input-grid">{field('shares',term('Outstanding shares'),'1')}</div>}
    {listedYield&&listedSource&&listedYield.currency!==report.currency&&<p>{t('Listing currency')} · <a href={listedSource.url} target="_blank" rel="noreferrer">{listedSource.label} ↗</a> · {listedYield.currency} · {number(listedYield.yield,4)}% · {dateLabel(listedYield.date,t.language)}</p>}
    {benchmark&&treasury&&<p><a href={treasury.url} target="_blank" rel="noreferrer">{treasury.label} ↗</a> · {benchmark.currency} · {number(benchmark.yield,4)}% · {dateLabel(benchmark.date,t.language)}</p>}
    {data.sector==='financial'&&<p>{t('Financial services start with WACC in the cash-flow currency. If it is unavailable or below the model minimum, the minimum applies.')}</p>}
    <p>{!wacc.equityOnly&&t('The standard DCF floor is the higher of 6% and the recent ten-year yield in the cash-flow currency.')} {!benchmark&&t('No recent ten-year benchmark is available in this currency.')}</p>
    <p>{t('Source')} · {report.source||'Yahoo Finance'} · {dateLabel(report.fetchedAt,t.language)}. {!dcf&&t('Dividend source: reported trailing annual dividend per share, or the latest fiscal-year dividend if unavailable. A verified currency conversion is required when quote and statement currencies differ.')}</p>
   </details>
   <div className="value-box valuation-summary">
    <div className="value-label">{term('Model value per share')} <strong>{report.symbol}</strong></div>
    <div className="big-value">{number(value.perShare)} {finite(value.perShare)&&<small>{report.currency}</small>}</div>
    {value.error&&<p role="alert">{t(value.error)} {value.error==='Enter a discount rate at or above the model minimum.'&&number(minimum)+'%'}</p>}
    <dl>
     {row('Current price',money(market.price,market.currency))}
     {row('Total outstanding shares',Number.isSafeInteger(value.shares)&&value.shares>0?number(value.shares,0):'—')}
     {row('Market capitalisation',amount(market.capitalisation,market.currency))}
     {row('Model equity value',amount(value.equityValue))}
     {row('Margin of safety',percent(value.margin))}
     {row('Upside potential',percent(value.upside))}
    </dl>
    <p>{dateLabel(report.quote?.at||report.fetchedAt,t.language)} · {report.quote?.source||report.source||'—'}<br/>
     {t('A model result, not a price target or a buy recommendation.')}</p>
   </div>
  </div></div>
  {dcf&&!value.error&&<details className="cashflow-projection"><summary>{term('Cash flow projection')}</summary><div className="table-scroll">
   <table><thead><tr><th>{t('Year')}</th><th>{term('Owner earnings')} · {report.currency}</th><th>{term('Present value')} · {report.currency}</th></tr></thead>
    <tbody>{value.rows.map(row=><tr key={row.year}><th scope="row">{row.year}</th><td>{number(row.flow)}</td><td>{number(row.pv)}</td></tr>)}</tbody>
    <tfoot><tr><th scope="row">{term('Terminal value')} · {t('Year')} 10</th><td>{number(value.terminalValue)}</td><td>{number(value.terminalPV)}</td></tr></tfoot></table>
   </div></details>}
   {dcf&&<Sensitivity report={report} inputs={inputs} onInputs={onInputs} t={t} number={number}/>}
 </section>;
}
