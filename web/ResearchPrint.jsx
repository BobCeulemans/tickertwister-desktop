import {reminderLabel,dateLabel} from './presentation.mjs';
import {restoreValuation} from './saved.mjs';
import {calculateValuation} from './valuation.mjs';
import ValuationPrint from './ValuationPrint.jsx';
import AIPrint from './AIPrint.jsx';
// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {personalScore} from './weights.mjs';
import {businessExcerpt} from './models.mjs';
import {statusLabel,notePages} from './presentation.mjs';
import {metrics,periods} from './comparison.mjs';
function SavedValuation({entry,t,number,percent}){
 const {report,options}=entry.saved;
 const {inputs,legacy}=restoreValuation(report,options);
 const value=calculateValuation(report,inputs,options.method);
 return <>{legacy&&<p className="print-note">{t('The current model uses this earlier snapshot. Review the assumptions behind the recalculated value.')}</p>}
  <ValuationPrint report={report} method={options.method} inputs={inputs} value={value} t={t} number={number} percent={percent}/></>;

}
export default function ResearchPrint({entries,snapshot,t,number,percent}){
 const pages=[];
 for(const e of entries){const r=e.saved.report,y=periods(r).get('FY:'+r.years.at(-1).end),personal=personalScore(r,e.saved.options.scoreWeights,e.saved.options.scoreOverrides);
 pages.push(<><h1>{r.symbol} · {r.name}</h1><p>{t("Research status")}: <strong>{statusLabel(e.notes.status,t)}</strong> · {t("Review date")}: {e.notes.reviewDate?reminderLabel(e.notes.reviewDate):'—'}</p><p className="print-meta">{r.source||'SEC EDGAR'} · {t("Retrieved")}: {dateLabel(r.fetchedAt,t.language)}<br/>{t("Annual figures ending")} {dateLabel(y.end,t.language)} · {r.currency}</p><h2>{t("The business")}</h2><p>{businessExcerpt(r.summary,500)||'—'}</p><div className="print-score"><div><span>{t("Quality")}</span><strong>{number(personal.custom?personal.value:r.score.value)}/100</strong></div><div><span>{t("Coverage")}</span><strong>{r.score.available}/{r.score.total}</strong></div><div><span>{t("Price")}</span><strong>{number(r.quote?.price)} {r.quote?.currency||''}</strong></div></div>{personal.custom&&<p>{t("Personal score: ")}{number(personal.value)}/100 · {t("Default score: ")}{number(r.score.value)}/100</p>}<h2>{t("Saved valuation assumptions")}</h2><SavedValuation entry={e} t={t} number={number} percent={percent}/><table><caption>{t("Key ratios from the saved annual analysis")}</caption><tbody>{metrics.filter(m=>m.group==='core').map(m=><tr key={m.key}><th>{t.term(m.label)}</th><td>{m.unit==='%'?percent(m.value(y)):number(m.value(y))+' ×'}</td></tr>)}</tbody></table><p className="print-note">{t("This dossier uses the saved snapshot and personal assumptions. Price, annual figures and quarterly comparison may have different reference dates. Personal notes follow on separate pages.")}</p></>);
 const list=metrics.filter(m=>m.group!=='core'&&(m.unit!=='money'||['cfo','capex','fcf','buybacks','dividends'].includes(m.key)));
 pages.push(<><h1>{r.symbol} · Buffett & Clark</h1><p>{dateLabel(y.end,t.language)} · {r.currency} · {t("Amounts in millions; per-share amounts in units.")}</p><table><tbody>{list.map(m=><tr key={m.key}><th>{t.term(m.label)}</th><td>{m.unit==='%'?percent(m.value(y)):number(m.unit==='money'&&m.value(y)!=null?m.value(y)/1e6:m.value(y))+(m.unit==='×'?' ×':'')}</td></tr>)}</tbody></table></>);
 const text=[['thesis',t("My investment thesis")],['risks',t("Risks")],['disconfirm',t("What would disprove my thesis?")],['nextStep',t("Next research question")]].filter(([key])=>e.notes[key]?.trim()).map(([key,label])=>label+'\n'+e.notes[key]).join('\n\n');
 if(text)notePages(text).forEach((chunk,i)=>pages.push(<><h1>{r.symbol} · {t("Personal notes")}</h1><p className="print-meta">{statusLabel(e.notes.status,t)} · {i+1}</p><pre className="research-note-print">{chunk}</pre></>));

 }
 if(snapshot&&snapshot.reports.length>=2){const {reports,period}=snapshot;
 pages.push(<><h1>{t("Companies side by side")}</h1><p>{period.key} · {period.key.startsWith('LONG:')?t("Annual means; fiscal year ends may differ by up to 190 days."):t("Common period; 52/53-week calendars may differ by up to seven days.")}</p><table><thead><tr><th>{t("Metric")}</th>{reports.map((r,i)=><th key={r.symbol}>{r.symbol}<br/>{r.currency}<br/>{period.rows[i].periodStart||''}<br/>{dateLabel(period.rows[i].end,t.language)}</th>)}</tr></thead><tbody>{metrics.filter(m=>m.group==='core').map(m=><tr key={m.key}><th>{t.term(m.label)}</th>{period.rows.map((y,i)=><td key={i}>{m.unit==='%'?percent(m.value(y)):number(m.value(y))+' ×'}</td>)}</tr>)}</tbody></table><p className="print-note">{t("Amounts are not converted between currencies. The original 39-criterion score is a multi-year snapshot, not a score for this comparison period. Quarterly returns are not annualised.")}</p><h2>{t("Follow-up research")}</h2><p>{t("Investigate differences in business model, accounting and one-offs. Compare the figures with your own investment thesis and review valuation assumptions in the company report.")}</p></>);
 }
 return <article id="research-print" className="print-report" aria-hidden="true">{pages.map((content,i)=><section className="print-page" key={i}><div className="print-heading"><strong>Tickertwister</strong><span>{t("Private research dossier")} · {i+1}/{pages.length}</span></div>{content}<div className="print-foot">Copyright ©2026 Bob Ceulemans<br/>All Rights Reserved. · {t("Personal research — not investment advice.")}</div></section>)}<AIPrint symbols={entries.map(e=>e.saved.report.symbol)} t={t}/></article>;
}
