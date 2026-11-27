import {dateLabel} from './presentation.mjs';
import {comparablePrice} from './currency.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {useState} from 'react';
import DiscountRateInput from './DiscountRateInput.jsx';
import {directEquityModel} from './valuationSector.mjs';
import {calculateValuation,minimumDiscountRate,historicalGrowthBand,revenueHistory,valuationScenarios as scenariosFrom,reverseGrowth} from './valuation.mjs';

export default function ValuationLab({report,inputs,onInputs,scenarios,onScenarios,t,number,percent}){
 const history=report.years.slice().sort((a,b)=>a.end.localeCompare(b.end)),earningsBand=historicalGrowthBand(report) ,revenue=revenueHistory(report);
 const equityOnly=directEquityModel(report);
 const [margin,setMargin]=useState('25');
 const base=calculateValuation(report,inputs),values=scenarios.map(s=>calculateValuation(report,s));
 function changeScenario(index,key,value){
  onScenarios(scenarios.map((scenario,i)=>{
   if(i!==index)return scenario;
   const next={...scenario,[key]:value};
   if(equityOnly&&key==='rate'){
    next.independentEquityRate=true;
    next.personalEquityRate=true;
   }
   return next;
  }));
 }
 const quote=comparablePrice(report);
 const reverse=reverseGrowth(report,inputs,quote),validMargin=margin.trim()!==''&&Number(margin)>=0&&Number(margin)<100;
 const buyPrice=!base.error&&validMargin?base.perShare*(1-Number(margin)/100):null;
 return <section className="card lab" id="lab"><div className="eyebrow">RESEARCH STUDIO / 01</div><div className="studio-title"><div><h2>{t("How robust is your valuation?")}</h2><p className="muted">{t("A valuation range, a stress test and the expectations behind the price.")}</p></div><span className="studio-badge">VALUATION LAB</span></div>
 <div className="lab-insights"><article><span>{t("What growth would justify the price?")}</span><strong>{percent(reverse)}</strong><p>{t("Annual growth that matches the current price, holding your other DCF assumptions fixed. Not a forecast or observed market consensus.")}</p><div className="historical-growth"><b>{t("Historical growth from Yahoo data")}</b><p>{t.term("Historical owner earnings growth")}{earningsBand.period&&' ('+earningsBand.period+')'}: <strong>{percent(earningsBand.historical)}</strong><br/>{t.term("Revenue CAGR")}{revenue.period&&' ('+revenue.period+')'}: <strong>{percent(revenue.growth)}</strong></p><small>{dateLabel(history[0].end,t.language)} → {dateLabel(history.at(-1).end,t.language)} · {history.length} {t("fiscal years; full available annual history, uncapped. CAGR requires positive endpoints; otherwise —. Historical growth is not a forecast.")}</small></div>{reverse===null&&<small>{base.error||quote===null?t("A valid valuation and a price in the same currency are required."):t("No solution within −99% to +200%.")}</small>}</article><article><span>{t("Price at your margin of safety")}</span><strong>{number(buyPrice)} <small>{report.currency}</small></strong><label>{t.term("Desired margin (%)")}<input type="number" min="0" max="99" step="0.1" value={margin} onChange={e=>setMargin(e.target.value)}/></label><p>{t("Model value × (1 − desired margin). Your own price threshold, not a buy recommendation.")}</p></article><article><span>{t("Dependence on terminal value")}</span><strong>{!base.error?percent(base.terminalWeight):'—'}</strong><p>{t("This share of model value comes from perpetual cash flows after the projection period. The higher it is, the more the terminal assumption matters.")}</p></article></div>
 <details><summary>{t("Three scenarios: bear, base and bull")}</summary><p className="method-note">{t(equityOnly?"Scenarios follow the main cost of equity until you enter a scenario-specific rate. Bear and bull vary starting earnings by 15% and growth by 5 points.":"Bear: starting owner earnings ×0.85, growth −5 points, discount rate +2 points. Bull: ×1.15, +5 points, −2 points. The model minimum applies.")}</p><div className="scenario-grid">{scenarios.map((s,i)=><article key={i} className={'scenario scenario-'+i}><div className="eyebrow">{['BEAR','BASE','BULL'][i]}</div><strong>{number(values[i].perShare)} <small>{report.currency}</small></strong><p>{t.term("Margin of safety")}: {percent(values[i].margin)}</p>{[['growth',t.term("Growth (%)")],['rate',t.term("Required return (%)")],['terminal',t.term("Perpetual growth (%)")],['ownerEarnings',t.term('Starting owner earnings')+' · '+t("million")+' '+report.currency]].map(([key,label])=>{
 const Input=key==='rate'&&!equityOnly?DiscountRateInput:'input';
 return <label key={key}>{label}{key==='rate'&&s.independentEquityRate&&' · '+t('Personal assumption')}<Input type="number" step="any" min={!equityOnly&&key==='rate'?minimumDiscountRate(report):undefined} value={s[key]} onChange={e=>changeScenario(i,key,e.target.value)}/></label>;})}{values[i].error&&<p className="error">{t(values[i].error)} {values[i].error==='Enter a discount rate at or above the model minimum.'&&number(minimumDiscountRate(report))+'%'}</p>}</article>)}</div><button className="reset-model" onClick={()=>onScenarios(scenariosFrom(inputs,report))}>{t("Reset scenarios from main model")}</button></details>

 <details className="lab-formulas"><summary>{t('Calculation formulas')}</summary><dl>
  <div><dt>{t('What growth would justify the price?')}</dt>
   <dd><span>DCF(<i>g</i><sup>∗</sup>) = {t.term('Current price')}</span></dd></div>
  <div><dt>{t('Price at your margin of safety')}</dt>
   <dd><span>{t.term('Model value per share')} × (1 − {t.term('Margin of safety')})</span></dd></div>
  <div><dt>{t('Dependence on terminal value')}</dt>
   <dd><math><mfrac><mrow><mi>PV</mi><mo>(</mo><mi>TV</mi><mo>)</mo></mrow>
    <mrow><msub><mi>PV</mi><mtext>1–10</mtext></msub><mo>+</mo><mi>PV</mi><mo>(</mo><mi>TV</mi><mo>)</mo></mrow></mfrac></math></dd></div>
 </dl></details>
 <p className="method-note">{t("All tools use the same DCF model. The reverse calculation varies only growth; many combinations of assumptions can explain the same price.")} <a href="https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation" target="_blank" rel="noreferrer">{t("Methodological background")} ↗</a></p>
 </section>;
}
