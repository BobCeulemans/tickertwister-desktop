// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {useState} from 'react';
import {personalScore} from './weights.mjs';
import {dateLabel} from './presentation.mjs';
import {TickerBatchForm} from './TickerBatch.jsx';
import {MacIcon} from './MacShell.jsx';
import {statusLabel} from './presentation.mjs';
export default function FocusHome({t,symbol,setSymbol,onAnalyse,onBatch,batchRunning,error,quote,entries,onEntry,onResearch,onOpenAnalysis}) {
 const [selected,setSelected]=useState(null);
 const entry=entries.find(e=>e.saved.report.symbol===selected)||entries[0];
 const preview=entry?.saved.report;
 const score=preview?personalScore(preview,entry.saved.options?.scoreWeights,entry.saved.options?.scoreOverrides):null;
 return <div className="focus-home focus-with-inspector"><div className="focus-content">
  <blockquote className="focus-quote"><span>{t('QUOTE FROM THE GOAT')}</span><p>“{quote.text}”</p><cite>{quote.author} <a href={quote.url} target="_blank" rel="noreferrer">{quote.year} ↗</a></cite></blockquote>
  <section className="focus-welcome"><div className="focus-intro"><span className="mac-kicker">TICKERTWISTER</span><h1>{t('Start your research')}</h1><p>{t('Understand the business. Then consider the price.')}</p>
   <form id="start" onSubmit={e=>{e.preventDefault();onAnalyse(symbol);}}><label htmlFor="ticker">{t('Company ticker')}</label><div className="focus-ticker"><span className="focus-ticker-field"><MacIcon name="search"/><input id="ticker" autoCapitalize="characters" autoComplete="off" spellCheck="false" required maxLength={20}  placeholder="AAPL" value={symbol} onChange={e=>setSymbol(e.target.value.toUpperCase())}/></span><button className="primary" type="submit">{t('Analyse business')} <span aria-hidden="true">↗</span></button></div></form>
   <div className="focus-examples"><span>{t('Try')}</span>{['AAPL','MSFT','ASML.AS','KO'].map(s=><button key={s} onClick={()=>{setSymbol(s);onAnalyse(s);}}>{s}</button>)}</div>{error&&<p className="error" role="alert">{error}</p>}
  <TickerBatchForm t={t} onStart={onBatch} running={batchRunning}/>
  </div></section>
  <section className="focus-library"><div className="focus-section-heading"><h2>{t('Your research')}</h2><button onClick={onResearch}>{t('Open research dossier')} <span aria-hidden="true">→</span></button></div>{entries.length?<div className="focus-recent">{entries.slice(0,3).map(e=><button key={e.saved.report.symbol} aria-pressed={preview?.symbol===e.saved.report.symbol} onClick={()=>setSelected(e.saved.report.symbol)}><span className="company-monogram">{e.saved.report.symbol.slice(0,2)}</span><span><strong>{e.saved.report.name}</strong><small>{e.saved.report.symbol}</small></span><span className={'status-badge status-'+e.notes.status}>{statusLabel(e.notes.status,t)}</span><span className="focus-row-arrow" aria-hidden="true">→</span></button>)}</div>:<div className="focus-empty"><MacIcon name="library"/><p>{t('Your first conviction starts with a question.')}<small>{t('Analyse a company and add it here. Then record your thesis and your strongest counterargument.')}</small></p></div>}</section>

  <div className="focus-principles">{[['01','Quality before price','A score with visible criteria, weights and data coverage.'],['02','Follow the cash flow','Four charts connect earnings, cash flow, capital and margins.'],['03','Value is an assumption','Explore DCF and Gordon Growth with your own expectations.']].map(([n,title,copy])=><article key={n}><span>{n}</span><h3>{t(title)}</h3><p>{t(copy)}</p></article>)}</div>
 </div><div className="focus-rail"><figure className="focus-portrait"><img src="./buffett-munger.png" alt={t('Illustration of Warren Buffett and Charlie Munger')}/><figcaption>{t('Quality. Value. Patience.')}</figcaption></figure><aside className="focus-inspector" aria-label={t("Dossier preview")}><span className="mac-kicker">{t("Dossier preview")}</span>{preview?<><h2>{preview.symbol}</h2><h3>{preview.name}</h3><span className={"status-badge status-"+entry.notes.status}>{statusLabel(entry.notes.status,t)}</span><dl><div><dt>{t("Quality score")}</dt><dd>{Number.isFinite(score?.value)?score.value.toFixed(2):"—"} / 100</dd></div><div><dt>{t("Data coverage")}</dt><dd>{preview.score.available} / {preview.score.total}</dd></div><div><dt>{t("Retrieved")}</dt><dd>{dateLabel(preview.fetchedAt,t.language)}</dd></div></dl><button className="primary" onClick={()=>onOpenAnalysis(entry.saved)}>{t("View analysis")}</button><button onClick={()=>onEntry(preview.symbol)}>{t("Open research dossier")}</button></>:<p>{t("Select a company to preview its research dossier.")}</p>}</aside></div></div>;
}
