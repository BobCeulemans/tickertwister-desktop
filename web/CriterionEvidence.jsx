// SPDX-License-Identifier: AGPL-3.0-only
import {dateLabel,tableScale} from './presentation.mjs';
import {criterionDescription,criterionFindings} from './criterionEvidence.mjs';
import {canOverride} from './weights.mjs';

function HistoryTable({history,currency,t,number}){
 const observations=[...history.pairs].sort(([a],[b])=>b.localeCompare(a));
 if(!observations.length)return <p>{t("No data")}</p>;
 const [divisor,scale]=history.kind==='money'?tableScale(observations.map(([,value])=>value),t):[1,''];
 const units={money:scale+' '+currency,percent:'%',perShare:currency+' / '+t("share"),days:t("days"),months:t("months"),ratio:'×'};
 function period(label){
  if(/^\d{4}-\d{2}-\d{2}$/.test(label))return dateLabel(label,t.language);
  return label.includes('TTM')?t('Yahoo current/TTM'):label;
 }
 return <div className="table-scroll"><table className="criterion-history"><caption>{t.term(history.label,history.heading)} · {units[history.kind]}</caption>
  <thead><tr>{observations.map(([date],i)=><th scope="col" key={i}>{period(date)}</th>)}</tr></thead>
  <tbody><tr>{observations.map(([,value],i)=><td key={i}>{Number.isFinite(value)?number(value/divisor):'—'}</td>)}</tr></tbody>
 </table></div>;
}

export default function ScoreEvidence({criteria,histories=[],currency,t,number,overrides=[],onOverrides}){
 const historyByName=new Map(histories.map(h=>[h.name,h]));
 const scoredNames=new Set(criteria.map(c=>c.key));
 const extras=histories.filter(h=>!scoredNames.has(h.name));
 return <>
  <div className="compact-disclosures">{criteria.map(c=>{
   const history=historyByName.get(c.key);
   const points=c.factor===null?t("No data"):(c.effectiveWeight??c.weight)?number(c.personalPoints??c.points)+' / '+number(c.effectiveWeight??c.weight):t("Available · unweighted");
   const label=t.term(c.label,c.heading);
   return <details key={c.key}><summary><span>{label}</span><span className="criterion-actions">
    {onOverrides&&c.available&&c.weight>0&&<label className="criterion-override" title={canOverride(c)?t('Award full points'):t('Full points from source')} onClick={e=>e.stopPropagation()}>
      <input type="checkbox" aria-label={(canOverride(c)?t('Award full points'):t('Full points from source'))+' · '+label} checked={c.points===c.weight||overrides.includes(c.key)} disabled={!canOverride(c)||(c.effectiveWeight===0&&!c.overridden)} onChange={e=>onOverrides(e.target.checked?[...overrides,c.key]:overrides.filter(key=>key!==c.key))}/>
    </label>}
    <span className={'pill '+(c.factor===null?'missing':c.overridden||c.factor===1?'good':'')}>{points}</span></span></summary>
    <p className="criterion-description">{criterionDescription(c,t)}</p><div className="criterion-evidence">{criterionFindings(c,history,t,number).map(text=><p key={text}>{text}</p>)}</div>
    {c.overridden&&<p className="criterion-source">{t('Source points')} · {number(c.points)} / {number(c.weight)}</p>}
    {history&&<HistoryTable history={history} currency={currency} t={t} number={number}/>}
   </details>;
  })}</div>
  {extras.length>0&&<><h3>{t("Additional historical series")}</h3><div className="compact-disclosures additional-histories">{extras.map(h=><details key={h.name}>
   <summary>{t.term(h.label,h.heading)}</summary><HistoryTable history={h} currency={currency} t={t} number={number}/>
  </details>)}</div></>}
 </>;
}
