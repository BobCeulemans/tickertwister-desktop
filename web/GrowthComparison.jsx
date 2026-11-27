// SPDX-License-Identifier: AGPL-3.0-only
import {valuationGrowthBand} from './valuation.mjs';

export default function GrowthComparison({report,inputs,t,number,percent,print=false}){
 const band=valuationGrowthBand(report,inputs);
 const metric=(label,period,growth)=><>{label}{period&&' ('+period+')'} · <b>{percent(growth)}</b></>;
 const growthLines=<>{metric(t.term('Historical owner earnings growth'),band.period,band.historical)}<br/>
  {metric(t.term('Revenue CAGR'),band.revenuePeriod,band.revenueGrowth)} · {metric(t.term('Net income CAGR'),band.incomePeriod,band.incomeGrowth)}</>;
 const method=band.method;
 if(band.suggested===null)return <div className="growth-comparison"><b>{t.term('Valuation range')}</b><p>{growthLines}</p><small>{t('Insufficient history for a growth estimate.')}</small></div>;
 const same=band.strict===band.moderate;
 const endpoints=same?[[t('Both caps'),'10% / 12%',band.strict,band.strictValue]]:[
  [t('Strict'),'10%',band.strict,band.strictValue],[t('Moderate'),'12%',band.moderate,band.moderateValue]
 ];
 const perShare=value=>value===null?'—':number(value)+' '+report.currency;
 if(print)return <p>{growthLines}<br/>{metric(t(method),band.suggestedPeriod,band.suggested)}<br/>
  {t.term('Valuation range')} · {endpoints.map(([label,cap,growth,price])=>label+' ('+cap+'): '+number(Number(growth))+'% → '+perShare(price)).join(' · ')}</p>;
 return <div className="growth-comparison">
  <h3>{t.term('Valuation range')}</h3>
  <p>{growthLines}<br/>{metric(t(method),band.suggestedPeriod,band.suggested)}</p>
  <div className="table-scroll"><table>
   <thead><tr><th>{t.term('Growth cap')}</th><th>{t.term('Growth used')}</th><th>{t.term('Model value per share')}</th></tr></thead>
   <tbody>{endpoints.map(([label,cap,growth,price])=><tr key={label}><th scope="row">{label} · {cap}</th><td>{number(Number(growth))}%</td><td>{perShare(price)}</td></tr>)}</tbody>
  </table></div>
 </div>;
}
