import {dateLabel} from './presentation.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
import {printRecords} from './aiArchiveData.mjs';
import {useAIArchive} from './aiArchive.mjs';
import {recordText} from './aic.mjs';
import {notePages} from './presentation.mjs';
export default function AIPrint({symbols,t}){
 const {records,selectedIds}=useAIArchive(),items=printRecords(records,symbols,selectedIds);
 return <>{items.flatMap(r=>notePages(recordText(r),82,29).map((text,i)=><section className="print-page" key={r.id+'-'+i}><div className="print-heading"><strong>Tickertwister · AI-AIC</strong><span>{t("AI appendix")} · {i+1}</span></div><h1>{r.input.companies.map(c=>c.symbol).join(' / ')}</h1><p className="print-meta">{r.input.period} · {dateLabel(r.createdAt,t.language)} · {r.language.toUpperCase()} · {r.result.model} · {r.settings?.effort||'—'}<br/>{t("Saved comparison; source data and valuation assumptions may since have changed.")} {r.translationOf?t("Translation of saved analysis."):''}</p>{i===0&&<p className="print-meta">{r.input.companies.map(c=>c.symbol+': '+(c.start?c.start+' → ':'')+c.end+' · '+c.currency).join(' | ')}</p>}<pre className="research-note-print">{text}</pre><div className="print-foot">Copyright ©2026 Bob Ceulemans<br/>All Rights Reserved. · {t("AI screening, not personalised investment advice. Verify sources.")}</div></section>))}</>;
}
