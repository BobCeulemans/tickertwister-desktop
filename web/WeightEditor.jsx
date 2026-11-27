// SPDX-License-Identifier: AGPL-3.0-only
import {useState} from 'react';
import {personalScore} from './weights.mjs';
export default function WeightEditor({report,weights,onWeights,overrides,t,number}){
 const [query,setQuery]=useState(''),[modified,setModified]=useState(false);
 if(report.schema!=='yahoo39-v1')return null;
 const score=personalScore(report,weights,overrides),items=score.criteria.filter(c=>(!modified||c.multiplier!==1||c.overridden)&&[c.heading,c.label,t.term(c.label,c.heading)].join(' ').toLowerCase().includes(query.toLowerCase()));
 return <details className="weight-editor" id="score-weights"><summary>{t("My weighting of the 39 analysis criteria")} · {number(score.value)}/100</summary>
 <p className="small">{t("1× = default · 2× = double importance · 0× = exclude. Your score updates immediately.")}</p>
 <div className="weight-tools"><input type="search" aria-label={t("Search criterion")} placeholder={t("Search criterion…")} value={query} onChange={e=>setQuery(e.target.value)}/><button aria-pressed={modified} onClick={()=>setModified(v=>!v)}>{t("Modified only")}</button><button data-action="weights-reset" onClick={()=>onWeights({})}>{t("Restore defaults")}</button><span>{items.length}/39</span></div>
 <div className="weight-grid">{items.map(c=><label className="weight-item" key={c.key}><span>{t.term(c.label,c.heading)}<small>{t("Default")} {number(c.weight)} → {t("effective")} {number(c.effectiveWeight)}{!c.available?t(" · No data"):!c.weight?t(" · Informational"):''}</small></span><span className="weight-factor"><input aria-label={t.term(c.label,c.heading)} type="number" min="0" max="100" step="0.1" value={c.multiplier} onChange={e=>{const n=Number(e.target.value);if(Number.isFinite(n)&&n>=0&&n<=100)onWeights({...weights,[c.key]:n});}}/>×</span></label>)}</div>
 {!items.length&&<p>{t("No criteria match this filter.")}</p>}
 <details className="weight-help"><summary>{t("Calculation and saving")}</summary><p>{t("Personal score = adjusted points / available adjusted weights × 100. A checked override awards the available points for that criterion in this analysis. Missing and unweighted criteria add no points. Add the analysis to the dossier again to update its saved score.")}</p></details></details>;
}
