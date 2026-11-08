import {dateLabel} from './presentation.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
import {shortAmount} from './presentation.mjs';
import {evidenceLines} from './criterionEvidence.mjs';
export default function CriterionEvidence({criterion,report,t,number}){
 const history=(report.originalHistories||[]).find(h=>h.name===criterion.key),lines=evidenceLines(criterion.threshold,!!history?.pairs?.length);
 return <div className="criterion-evidence">{lines.map((line,i)=><div key={i} className={line.status?'criterion-rule':'criterion-note'}>{line.status&&<span className={line.status} aria-label={line.status==='pass'?t("Pass"):t("Fail")}>{line.status==='pass'?'✓':'✕'}</span>}<span>{t.prose(line.text)}</span></div>)}{history?.pairs?.length>0&&<div className="criterion-series">{[...history.pairs].reverse().map(([date,value],i)=><div key={i}><small>{/^\d{4}-/.test(date)?dateLabel(date,t.language):t('Yahoo current/TTM')}</small><strong>{history.kind==='percent'||history.kind==='days'?number(value):shortAmount(value,number,t)}{history.kind==='percent'?'%':history.kind==='days'?t(" days"):''}</strong></div>)}</div>}</div>;
}
