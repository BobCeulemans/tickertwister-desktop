// SPDX-License-Identifier: AGPL-3.0-only
import {minimumDiscountRate, valuationMarket, waccEstimate} from './valuation.mjs';
import {directEquityModel} from './valuationSector.mjs';
import {capitalPercent,capitalPrecision} from './WaccDetails.jsx';
import GrowthComparison from './GrowthComparison.jsx';
import {shortAmount} from './presentation.mjs';

export default function ValuationPrint({report,method,inputs,value,t,number,percent}){
 const dcf=method==='dcf';
 const entered=n=>n==null||n===''?'—':number(Number(n));
 const amount=(n,currency=report.currency)=>Number.isFinite(n)?shortAmount(n,number,t.term)+' '+currency:'—';
 const market=valuationMarket(report), wacc=waccEstimate(report,inputs.waccBeta,'cashFlow');
 return <div className="print-valuation">
  <div>{dcf?t.term('Owner earnings · DCF'):'Gordon Growth'}</div>
  <strong>{number(value.perShare)} {report.currency} {t('per share')}</strong>
  <p>{t.term('Current price')}: {number(market.price)} {market.currency} · {t.term('Market capitalisation')}: {amount(market.capitalisation,market.currency)} · {t.term('Margin of safety')}: {percent(value.margin)} · {t.term('Upside potential')}: {percent(value.upside)}<br/>
   {wacc.equityOnly?t.term('Cost of equity (Re)'):t.term('Discount rate (%)')}: {wacc.equityOnly&&inputs.personalEquityRate?t('Personal assumption')+' · ':''}{wacc.equityOnly&&inputs.rate!==''?capitalPrecision(Number(inputs.rate),t.language)+'%':entered(inputs.rate)} · {t.term('Perpetual growth (%)')}: {entered(inputs.terminal)} · {wacc.equityOnly?'CAPM':'WACC'}: {wacc.equityOnly&&Number.isFinite(wacc.rate)?capitalPrecision(wacc.rate*100,t.language)+'%':capitalPercent(wacc.rate,t.language)}</p>
  {dcf?<p>{t.term('Starting owner earnings')}: {entered(inputs.ownerEarnings)} {t.term('million')} {report.currency} · {t.term('Annual owner earnings growth (%)')}: {entered(inputs.growth)}<br/>
   {t.term('Present value · years 1–10')}: {amount(value.projectionPV)} · {t.term('Terminal value · year 10')}: {amount(value.terminalValue)} · {t.term('Present value · terminal value')}: {amount(value.terminalPV)}<br/>
   {directEquityModel(report)?t('Net income is the equity cash flow proxy for banks and insurers.'):<>{t.term('Enterprise value')}: {amount(value.enterpriseValue)} · {t.term('Net debt')}: {amount(value.netDebt)}</>}<br/>
   {t.term('Model equity value')}: {amount(value.equityValue)} · {t.term('Outstanding shares')}: {number(value.shares,0)}</p>:
   <p>{t.term('Annual dividend per share (D₀)')}: {entered(inputs.dividend)} · {t.term('Next annual dividend · D1')}: {number(value.dividendNext)} {report.currency}</p>}
  {dcf&&<GrowthComparison print report={report} inputs={inputs} t={t} number={number} percent={percent}/>}
  {value.error&&<p>{t(value.error)} {value.error==='Enter a discount rate at or above the model minimum.'&&number(minimumDiscountRate(report))+'%'}</p>}
 </div>;
}
