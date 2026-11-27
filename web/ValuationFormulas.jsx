// SPDX-License-Identifier: AGPL-3.0-only
export default function ValuationFormulas({t,dcf,sector}) {
 const term=t.term;
 const directEquity=sector==='bank'||sector==='insurance';
 const formulas=dcf?[
  [term('Owner earnings'),directEquity?term('Net income'):sector==='financial'
   ?term('Net income')+' + '+term('Depreciation & amortisation')+' − |'+term('Capital expenditure')+'|'
   :term('Net income')+' + '+term('Depreciation & amortisation')+' − '+term('Maintenance capex estimate')+' + '+term('Working capital cash effect')],
  ...sector==='other'?[[term('Maintenance capex estimate'),'min('+term('Depreciation & amortisation')+', |'+term('Capital expenditure')+'|)']]:[],
  [term('Historical owner earnings growth')+' / '+term('Revenue CAGR')+' / '+term('Net income CAGR'),'CAGR = (Xₙ / X₀)^(1/n) − 1'],
  [term('Cash flow projection'),'OEₜ = OE₀ × (1 + g)ᵗ'],
  [term('Present value · years 1–10'),'PV₁₋₁₀ = ∑ₜ₌₁¹⁰ OEₜ / (1 + r)ᵗ'],
  [term('Terminal value · year 10'),'TV₁₀ = OE₁₀ × (1 + g∞) / (r − g∞)'],
  [term('Present value · terminal value'),'PV(TV) = TV₁₀ / (1 + r)¹⁰'],
  ...directEquity?[[term('Model equity value'),'PV₁₋₁₀ + PV(TV)']]:[[term('Enterprise value'),'EV = PV₁₋₁₀ + PV(TV)'],
  [term('Net debt'),term('Total debt')+' − '+term('Cash and cash equivalents')],
  [term('Model equity value'),'EV − '+term('Net debt')]],
  [term('Model value per share'),term('Model equity value')+' / '+term('Outstanding shares')]
 ]:[
  [term('Next annual dividend · D1'),'D₁ = D₀ × (1 + g∞)'],
  [term('Model value per share'),'D₁ / (r − g∞)'],
  [term('Model equity value'),term('Model value per share')+' × '+term('Outstanding shares')]
 ];
 formulas.push([term('Margin of safety'),'1 − '+term('Current price')+' / '+term('Model value per share')],
  [term('Upside potential'),term('Model value per share')+' / '+term('Current price')+' − 1']);
 return <details className="valuation-formulas"><summary>{t('Calculation formulas')}</summary>
  <p>{t('r = discount rate. g = annual growth. g∞ = perpetual growth. t and n are years.')}</p>
  <dl>{formulas.map(([title,expression])=><div key={title}><dt>{title}</dt><dd>{expression}</dd></div>)}</dl>
 </details>;
}
