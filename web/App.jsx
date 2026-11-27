import packageMetadata from '../package.json';
import {languageInfo,translator} from './i18n.mjs';
import MacShell from './MacShell.jsx';
import {initialHistory,visit,move,forgetAnalysis} from './workspaceNavigation.mjs';
import FocusHome from './FocusHome.jsx';
import {TickerBatchStatus,useTickerBatch} from './TickerBatch.jsx';
import AnalysisActions from './AnalysisActions.jsx';
import RatioFormulas from './RatioFormulas.jsx';
import {CompanyDescription,PriceHistory} from './CompanyDetails.jsx';
import FindPanel from './FindPanel.jsx';
import {tableScale} from './presentation.mjs';
import CurrencyNote from './CurrencyNote.jsx';
import {profileStorage as localStorage} from './profileStorage.mjs';
import ScoreEvidence from './CriterionEvidence.jsx';
import {dateLabel,shortAmount,marketValue} from './presentation.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import WeightEditor from './WeightEditor.jsx';
import {personalScore,validWeights} from './weights.mjs';
import Fold from './Fold.jsx';
import CompanyLogo from './CompanyLogo.jsx';
import ResearchDesk from './ResearchDesk.jsx';
import ValuationLab from './ValuationLab.jsx';
import QualityReview from './QualityReview.jsx';
import {valuationScenarios,defaultValuation,calculateValuation} from './valuation.mjs';
import ValuationPanel from './ValuationPanel.jsx';
import {printHTML} from './print.mjs';

import PrintReport from './PrintReport.jsx';
import {loadAnalysis} from './data.mjs';
import {nativeCall} from './native.mjs';
import {parseSaved,makeSaved,restoreValuation,refreshedValuationOptions,updateValuationScenarios} from './saved.mjs';
'use client';
import {useEffect,useState,useRef} from 'react';
import {finite} from './finance.mjs';
const buffettQuotes = [
 ["Our favorite holding period is forever.", "1988"],
 ["It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price.", "1989"],
 ["The only value of stock forecasters is to make fortune tellers look good.", "1992"],
 ["A fat wallet, however, is the enemy of superior investment results.", "1994"],
 ["Intelligent investing is not complex, though that is far from saying that it is easy.", "1996"],
 ["Lethargy bordering on sloth remains the cornerstone of our investment style", "1990"],
 ["We are never going to lose our appetite for buying companies with good economics and excellent management.", "1995"],
 ["It is better to be approximately right than precisely wrong.", "1993"],
 ["In many cases, a corporation's book value and business value are almost totally unrelated.", "1987"],
 ["What truly counts are gains in per-share intrinsic business value.", "1997"],
].map(([text, year]) => ({text, year, author:'Warren Buffett', url:'https://www.berkshirehathaway.com/letters/'+year+'.html'}));
const QUOTES = [...buffettQuotes, {
 text:'You have to keep learning if you want to become a great investor. When the world changes, you must change.',
 author:'Charlie Munger', year:'2022', url:'https://www.berkshirehathaway.com/letters/2022ltr.pdf#page=9',
}];
const moneyRows=[['revenue','Revenue'],['gross','Gross profit'],['operating','Operating income'],['income','Net income'],['cfo','Operating cash flow'],['capex','Capital expenditure'],['fcf','Free cash flow'],['assets','Total assets'],['equity','Book value / equity'],['debt','Total debt'],['cash','Cash & equivalents'],['retained','Retained earnings'],['dividends','Dividends paid'],['buybacks','Share buybacks']];
const ratioRows=[['roe','Return on Equity','%'],['roa','Return on Assets','%'],['grossMargin','Gross Profit Margin','%'],['netMargin','Net Profit Margin','%'],['fcfMargin','Free Cash Flow Margin','%'],['currentRatio','Current Ratio','×'],['quickRatio','Quick Ratio','×'],['debtEquity','Debt / Equity','%'],['liabilitiesEquity','Liabilities / Equity','%'],['interestCoverage','Interest Coverage','×'],['cashConversion','Cash Conversion','×'],['assetTurnover','Asset Turnover','×'],['capexIncome','Capex / Net Income','%'],['dividendCoverage','Dividend Coverage','×'],['dio','Days Inventory Outstanding','d'],['dso','Days Sales Outstanding','d'],['dpo','Days Payable Outstanding','d'],['ccc','Cash Conversion Cycle','d']];
function viewDetails(view){
 const scope=document.querySelector(['research','archive'].includes(view)?'.research-desk':'.analysis-view');
 return Array.from(scope?.querySelectorAll('details')||[]);
}
function capturePosition(view){
 return {scroll:window.scrollY,open:viewDetails(view).flatMap((el,index)=>el.open?[index]:[])};
}
function revealAnchor(anchor){
 const target=document.getElementById(anchor);
 if(!target)return;
 for(let el=target;el;el=el.parentElement)if(el.tagName==='DETAILS')el.open=true;
 const heading=target.closest('details.work-fold')||target;
 const offset=document.querySelector('.mac-toolbar')?.getBoundingClientRect().bottom||0;
 window.scrollBy({top:heading.getBoundingClientRect().top-offset-10,behavior:'instant'});
}
export default function Home({preferences,onPreference}){
 const lang=preferences.language;
 const [history,setHistory]=useState(initialHistory);
 const historyRef=useRef(history);
 const scrollTask=useRef(0);
 function updateHistory(next){historyRef.current=next;setHistory(next);}
 function currentPosition(){return capturePosition(historyRef.current.entries[historyRef.current.index].view);}
 function record(route,position=currentPosition()){updateHistory(visit(historyRef.current,route,position));}
 function restorePosition(route){
  const task=++scrollTask.current;
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
   if(task!==scrollTask.current)return;
   if(route.position){
    const opened=new Set(route.position.open);
    viewDetails(route.view).forEach((el,index)=>{el.open=opened.has(index);});
    window.scrollTo({top:route.position.scroll,behavior:'instant'});
   }else if(route.anchor){revealAnchor(route.anchor);}
   else window.scrollTo({top:0,behavior:'instant'});
  }));
 }
 function browse(offset){
  const next=move(historyRef.current,offset,currentPosition());
  if(next===historyRef.current)return;
  const route=next.entries[next.index];
  if(route.view==='analysis'&&route.ticker!==report?.symbol){
   const saved=openAnalyses.find(item=>item.report.symbol===route.ticker);
   if(!saved)return;
   displaySaved(saved);
  }
  updateHistory(next);setWorkspaceView(route.view);
  setDeskOpen(['research','archive'].includes(route.view));restorePosition(route);
 }
 const [researchEntries,setResearchEntries]=useState([]);
 const [workspaceView,setWorkspaceView]=useState('overview');
 const [openAnalyses,setOpenAnalyses]=useState([]);
 const [requestedEntry,setRequestedEntry]=useState(null);
 const requestSerial=useRef(0);
 const deskRef=useRef(null);
 const [scratchpad,setScratchpad]=useState('');
 useEffect(()=>{const h=document.querySelector('header');const o=new ResizeObserver(()=>document.documentElement.style.setProperty('--header-height',h.offsetHeight+'px'));o.observe(h);return ()=>o.disconnect();},[]);
 const [symbol,setSymbol]=useState(''),[report,setReport]=useState(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[quote,setQuote]=useState(0),[open,setOpen]=useState(false);
 useEffect(()=>{
  const handle=e=>{
   const link=e.target.closest('a[href^="#"]');
   if(!link?.hash||!document.getElementById(link.hash.slice(1)))return;
   const current=historyRef.current.entries[historyRef.current.index];
   if(current.view!=='analysis')return;
   e.preventDefault();
   const route={view:'analysis',ticker:current.ticker,anchor:link.hash.slice(1)};
   record(route);restorePosition(route);
  };
  document.addEventListener('click',handle);return()=>document.removeEventListener('click',handle);
 },[]);
 const [scoreOverrides,setScoreOverrides]=useState([]);
 const [scoreWeights,setScoreWeights]=useState(()=>{try{const w=JSON.parse(localStorage.getItem('tt-score-weights')||'{}');return validWeights(w)?w:{};}catch{return {};}});
 useEffect(()=>{try{localStorage.setItem('tt-score-weights',JSON.stringify(scoreWeights));}catch{}},[scoreWeights]);
 function showResearch(){navigate('research');}
 function closeResearch(){if(historyRef.current.index>0)browse(-1);else navigate('overview');}
 const [deskOpen,setDeskOpen]=useState(false);
 const [labScenarios,setLabScenarios]=useState([]);
 const [valuationInputs,setValuationInputs]=useState({});
 const [method,setMethod]=useState('dcf');
 const [legacyValuation,setLegacyValuation]=useState(false);
 const [englishTerms,setEnglishTerms]=useState(()=>localStorage.getItem('tt-english-terms')==='true');
 const t=translator(lang,englishTerms);
 useEffect(()=>{localStorage.setItem('tt-english-terms',String(englishTerms));},[englishTerms]);
 const number=(v,digits=2)=>finite(v)?new Intl.NumberFormat(languageInfo(lang).locale,{minimumFractionDigits:digits,maximumFractionDigits:digits}).format(v):'—';
 const percent=v=>finite(v)?number(v*100)+'%':'—';
 const scaleFor=values=>{const m=Math.max(0,...values.filter(finite).map(Math.abs));return m>=1e12?[1e12,t("trillion")]:m>=1e9?[1e9,t("billion")]:m>=1e6?[1e6,t("million")]:m>=1e3?[1e3,t("thousand")]:[1,t("units")];};
 const compact=v=>{if(!finite(v))return '—';const [d,s]=scaleFor([v]);return number(v/d)+' '+s;};
 const errors={PRINT_FAILED:t("The report could not be printed. Please try again."),YAHOO_UNAVAILABLE:t("Yahoo Finance is temporarily unavailable or rate-limiting requests. Try again later."),ENGINE_UNAVAILABLE:t("The bundled analysis engine could not start. Reinstall the complete app."),ENGINE_BUSY:t("Two analyses are already running. Please wait."),NO_ANNUAL_DATA:t("Yahoo did not provide usable annual statements for this ticker."),CURRENCY_MISMATCH:t("Currency is missing or differs between the price/dividend and financial statements. No automatic currency conversion."),INVALID_SAVED:t("This file is not a valid Tickertwister analysis."),SAVE_FAILED:t("The file could not be saved."),INVALID_TICKER:t("Enter a valid ticker symbol."),TICKER_NOT_FOUND:t("This ticker is not in the SEC directory. Use a US SEC ticker such as AAPL, MSFT or KO."),UNSUPPORTED_GAAP:t("This company does not use the supported US-GAAP taxonomy. IFRS and foreign exchange listings are not yet supported."),NO_ANNUAL_USD:t("No usable annual US-GAAP figures in USD were found."),SEC_UNAVAILABLE:t("SEC is temporarily unavailable or limiting requests. Please try again later."),DATA_UNAVAILABLE:t("The data could not be retrieved. Please try again later."),INVALID_ASSUMPTIONS:t("Choose a discount rate above 0% and up to 50%, higher than terminal growth (0–10%). Annual growth must exceed −100%; no upper cap. Fill in all required fields; results must be finite."),NO_CASHFLOW:t("DCF needs positive free cash flow and a reported share count. You can enter your own normalized cash flow."),NO_DIVIDEND:t("No positive dividend per share reported; Gordon Growth is not applicable.")};
 useEffect(()=>{try{const q=(Number(localStorage.getItem('tt-quote')??-1)+1)%QUOTES.length;setQuote(q);localStorage.setItem('tt-quote',String(q));}catch{}const ticker=window.__tickertwisterTestTicker||new URLSearchParams(location.search).get('ticker');if(ticker){setSymbol(ticker);analyse(ticker,false);}},[]);
 async function analyse(ticker){const position=currentPosition();setWorkspaceView('analysis');setDeskOpen(false);const requestId=++requestSerial.current;setBusy(true);setError('');setReport(null);setLegacyValuation(false);setOpen(false);try{const data=await loadAnalysis(ticker);if(requestId!==requestSerial.current)return;record({view:'analysis',ticker:data.symbol},position);restorePosition({view:'analysis'});const options=optionsForReport(data);
   showAnalysis(data,options);}catch(e){if(requestId===requestSerial.current){setError(e.message||'DATA_UNAVAILABLE');record({view:'overview'},position);setWorkspaceView('overview');restorePosition({view:'overview'});}}finally{if(requestId===requestSerial.current)setBusy(false);}}
 function optionsForReport(data){
  const previous=openAnalyses.find(item=>item.report.symbol===data.symbol)||researchEntries.find(entry=>entry.saved.report.symbol===data.symbol)?.saved;
  if(previous)return refreshedValuationOptions(previous,data);
  const inputs=defaultValuation(data);
  return {method:'dcf',scoreWeights,valuationInputs:inputs,valuationScenarios:valuationScenarios(inputs,data)};
 }
 function showAnalysis(data,options){
  setReport(data);setSymbol(data.symbol);setScoreWeights(options.scoreWeights||{});setScratchpad(options.scratchpad||'');
  setScoreOverrides(options.scoreOverrides||[]);setMethod(options.method);
  const restored=restoreValuation(data,options);setLegacyValuation(restored.legacy);
  setValuationInputs(restored.inputs);setLabScenarios(restored.scenarios);
 }
 function displaySaved(saved){
  requestSerial.current++;setWorkspaceView('analysis');setBusy(false);setError('');setDeskOpen(false);setOpen(false);
  showAnalysis(saved.report,saved.options);
 }
 function storeOpen(saved){
  setOpenAnalyses(previous=>previous.some(item=>item.report.symbol===saved.report.symbol)
   ?previous.map(item=>item.report.symbol===saved.report.symbol?saved:item):[...previous,saved]);
 }
 const queue=useTickerBatch(data=>{
  const options=optionsForReport(data);
  if(report?.symbol===data.symbol)showAnalysis(data,options);
  else storeOpen(makeSaved(data,options));
 });
 function openSession(saved){
  const route={view:'analysis',ticker:saved.report.symbol};
  record(route);displaySaved(saved);restorePosition(route);
 }
 useEffect(()=>{
  const loaded=e=>{
   try{
    const saved=parseSaved(e.detail),route={view:'analysis',ticker:saved.report.symbol};
    record(route);displaySaved(saved);restorePosition(route);
   }catch{setError('INVALID_SAVED');}
  };
  const home=()=>reset();
  window.addEventListener('desktop-open-report',loaded);window.addEventListener('desktop-new',home);
  return ()=>{window.removeEventListener('desktop-open-report',loaded);window.removeEventListener('desktop-new',home);};
 },[]);
 useEffect(()=>{const save=()=>saveReport(),print=()=>printReport();window.addEventListener('desktop-save',save);window.addEventListener('desktop-print',print);return ()=>{window.removeEventListener('desktop-save',save);window.removeEventListener('desktop-print',print);};},[report,method,valuationInputs,labScenarios,scoreWeights,scoreOverrides,scratchpad,lang,deskOpen]);
 async function printReport(){try{const html=printHTML(deskOpen?'#research-print':undefined);if(html)await nativeCall('print',{html});}catch{setError('PRINT_FAILED');}}
 async function saveReport(){if(deskOpen){document.querySelector('[data-action=desk-save]')?.click();return;}if(!report)return;try{await nativeCall('save',{filename:report.symbol+'-analyse.tickertwister',content:JSON.stringify(makeSaved(report,currentOptions),null,2)});}catch{setError('SAVE_FAILED');}}
 function reset(){record({view:'overview'});setWorkspaceView('overview');const q=(Number(localStorage.getItem('tt-quote')??-1)+1)%QUOTES.length;setQuote(q);localStorage.setItem('tt-quote',String(q));requestSerial.current++;setBusy(false);setReport(null);setError('');setDeskOpen(false);setOpen(false);window.scrollTo({top:0,behavior:'instant'});}
 const latest=report?.years.at(-1),score=report?.score,personal=report?personalScore(report,scoreWeights,scoreOverrides):null;
 const valuationValue=report?calculateValuation(report,valuationInputs,method):{};
 function changeValuation(next){
  setLabScenarios(scenarios=>updateValuationScenarios(scenarios,valuationInputs,next,report));
  setValuationInputs(next);
 }
 const currentOptions={method,scoreWeights,scoreOverrides,scratchpad,valuationInputs,valuationScenarios:labScenarios};
 useEffect(()=>{if(report)storeOpen(makeSaved(report,currentOptions));},[report,method,valuationInputs,labScenarios,scoreWeights,scoreOverrides,scratchpad]);
 function navigate(view){
  if(!['overview','research','archive'].includes(view))return;
  requestSerial.current+=busy?1:0;setBusy(false);
  record({view});setWorkspaceView(view);setDeskOpen(view!=='overview');restorePosition({view});
 }
 function openStored(saved){window.dispatchEvent(new CustomEvent('desktop-open-report',{detail:saved}));}
 function closeAnalysis(ticker){
  setOpenAnalyses(items=>items.filter(x=>x.report.symbol!==ticker));
  if(report?.symbol===ticker){
   const next=openAnalyses.find(x=>x.report.symbol!==ticker);
   if(workspaceView==='analysis'&&next)openSession(next);
   else{setReport(null);if(workspaceView==='analysis')navigate('overview');}
  }
  updateHistory(forgetAnalysis(historyRef.current,ticker));
 }
 useEffect(()=>{nativeCall('ui-state',{canSave:!!report||deskOpen,canPrint:!!report||deskOpen,hasAnalysis:!!report&&!deskOpen,busy}).catch(()=>{});},[report,deskOpen,busy]);
 useEffect(()=>{const handler=e=>{const expanded=!!e.detail;setOpen(expanded);document.querySelectorAll('.analysis-view details').forEach(d=>d.open=expanded);};window.addEventListener('desktop-expand',handler);return()=>window.removeEventListener('desktop-expand',handler);},[]);
 useEffect(()=>{const handler=e=>navigate(e.detail);window.addEventListener('desktop-navigate',handler);return()=>window.removeEventListener('desktop-navigate',handler);},[report,busy]);

 function Chart({title,fields,unit=report.currency}){
  const values=report.years.flatMap(y=>fields.map(([key])=>unit==='%'&&finite(y[key])?y[key]*100:y[key])).filter(finite);const [divisor,scale]=unit==='%'?[1,'%']:scaleFor(values);
  const lo=Math.min(0,...values)/divisor,hi=Math.max(0,...values)/divisor,span=hi-lo||1;
  const y=v=>174-(v/divisor-lo)/span*135,x=i=>82+i*420/Math.max(1,report.years.length-1);
  return <article className="chart card"><div className="eyebrow">{unit==='%'?t("Annual margins · %"):`${t("Annual figures")} · ${scale} ${unit}`}</div><h3>{title}</h3>{values.length?<svg viewBox="0 0 530 215" role="img" aria-label={title}><title>{title}</title>{[0,1,2,3].map(i=>{const v=(lo+span*i/3)*divisor;return <g key={i}><line x1="82" x2="502" y1={y(v)} y2={y(v)} stroke="#dfe6de"/><text x="72" y={y(v)+4} textAnchor="end">{number(v/divisor)}</text></g>;})}{fields.map(([key,label],j)=>{let segments=[],seg=[];report.years.forEach((r,i)=>{const val=unit==='%'&&finite(r[key])?r[key]*100:r[key];if(finite(val))seg.push(`${x(i)},${y(val)}`);else if(seg.length){segments.push(seg);seg=[];}});if(seg.length)segments.push(seg);return <g key={key}>{segments.map((s,i)=><polyline key={i} points={s.join(' ')} fill="none" stroke={j?'#bb8c45':'#286959'} strokeWidth="3"/>)}{report.years.map((r,i)=>{const val=unit==='%'&&finite(r[key])?r[key]*100:r[key];return finite(val)?<circle key={r.end} cx={x(i)} cy={y(val)} r="4" fill={j?'#bb8c45':'#286959'}><title>{t.term(label)} · {dateLabel(r.end,t.language)} · {number(val/divisor)} {scale} {unit==='%'?'':report.currency}</title></circle>:null;})}</g>;})}{report.years.map((r,i)=><text key={r.end} x={x(i)} y="201" textAnchor="middle">{r.end.slice(0,4)}</text>)}</svg>:<p className="empty">{t("Insufficient data")}</p>}<div className="legend">{fields.map(([k,label],i)=><span key={k}><i style={{background:i?'#bb8c45':'#286959'}}/>{t.term(label)}</span>)}</div></article>;
 }
 return <><MacShell t={t} preferences={preferences} onPreference={onPreference} onBack={()=>browse(-1)} onForward={()=>browse(1)} canBack={history.index>0} canForward={history.index<history.entries.length-1} englishTerms={englishTerms} setEnglishTerms={setEnglishTerms} deskOpen={deskOpen} report={report} busy={busy} onHome={()=>navigate('overview')} onNew={reset} view={workspaceView} entries={researchEntries} openAnalyses={openAnalyses} onNavigate={navigate} onSwitch={openSession} onCloseAnalysis={closeAnalysis} onResearch={showResearch} onClose={closeResearch} onOpen={()=>nativeCall('open',{}).catch(()=>setError('INVALID_SAVED'))} onSave={saveReport} onPrint={printReport} expanded={open} onExpand={()=>{setOpen(!open);[...document.querySelectorAll('.analysis-view details')].reverse().forEach(el=>{el.open=!open;});}} version={packageMetadata.version}/><FindPanel t={t} viewKey={String(deskOpen)+report?.symbol}/><main className="mac-main" data-fetching={busy||queue.batch?.running||undefined}>
 <TickerBatchStatus queue={queue} t={t} errors={errors}/>
 <ResearchDesk ref={deskRef} mode={workspaceView} requestedEntry={requestedEntry} onEntries={setResearchEntries} onClose={closeResearch} visible={deskOpen} report={report} options={currentOptions} t={t} number={number} percent={percent}/>
 <div className="analysis-view" key={requestSerial.current} hidden={deskOpen}>

 {workspaceView==='overview'&&!busy&&<FocusHome t={t} symbol={symbol} setSymbol={setSymbol} onAnalyse={analyse} onBatch={queue.start} batchRunning={!!queue.batch?.running} error={error?(errors[error]||errors.DATA_UNAVAILABLE):''} quote={QUOTES[quote]} entries={researchEntries} onResearch={showResearch} onOpenAnalysis={openStored} onEntry={symbol=>{setRequestedEntry({symbol,nonce:Date.now()});showResearch();}}/>}
 {busy&&<section className="loading card" role="status" aria-live="polite"><div className="spinner"/><div className="eyebrow">{symbol}</div><h2>{t("Opening the financial statements.")}</h2><p>{t("Retrieving data, aligning fiscal years and calculating ratios…")}</p><p className="muted">{t("This may take up to two minutes.")}</p></section>}
 {report&&workspaceView==='analysis'&&<>{error&&<div className="error" role="alert">{errors[error]||errors.DATA_UNAVAILABLE}</div>}{report.savedAt&&<p className="saved-note">{t("Saved analysis — no fresh data retrieved.")} {dateLabel(report.savedAt,t.language)} <button onClick={()=>analyse(report.symbol)}>{t("Refresh data")}</button></p>}<section className="report-head"><div><div className="eyebrow">{report.symbol} · {report.source || 'SEC EDGAR (bewaard)'} · {report.currency}</div><h1 className="company-title"><CompanyLogo report={report} t={t}/><span>{report.name}</span></h1><p className="muted">{t("Fiscal years")} {dateLabel(report.years[0].end,t.language)} — {dateLabel(latest.end,t.language)}</p></div><span className="source-badge">{t("Reported figures, not estimates")}</span></section>
 <AnalysisActions key={report.symbol} t={t} notes={scratchpad} onNotes={setScratchpad} onPin={()=>deskRef.current?.saveCurrent()??Promise.reject(Error('DOSSIER_NOT_READY'))}/>
 <CompanyDescription report={report} t={t}/>

 <div className="kpis"><article className="score-kpi"><div className="eyebrow">{personal?.custom?t("MY QUALITY SCORE"):t("QUALITY SCORE")}</div><strong>{number(personal?.custom?personal.value:score.value,personal?.custom?2:0)}<small>/100</small></strong><p>{personal?.custom?t("My personal weighting"):t("Original weighting")}</p>{report.schema==='yahoo39-v1'&&<a className="weight-link" href="#score-weights">{t("Adjust my weights")}</a>}{personal?.custom&&<p className="personal-score">{t("Original score: ")}<b>{number(score.value)}/100</b></p>}<p>{personal?.custom&&personal.value===null?t("No active score weight"):score.coverage<.6?t("Limited supporting data"):(personal?.custom?personal.value:score.value)>=75?t("Strong model signals"):(personal?.custom?personal.value:score.value)>=50?t("Mixed profile"):t("Areas of concern")}</p></article><article><div className="eyebrow">{t("DATA COVERAGE")}</div><strong>{score.available}<small>/{score.total}</small></strong><p>{percent(score.coverage)} {t("of analysis criteria available")}</p></article><article><div className="eyebrow">{t.term("Free cash flow")}</div><strong className="amount">{compact(latest.fcf)}</strong><p>{report.currency} · {dateLabel(latest.end,t.language)}</p></article><article><div className="eyebrow">{t.term("Return on Equity (ROE)")}</div><strong>{percent(latest.roe)}</strong><p>{t("Net income / closing equity")}</p></article></div>
 <PriceHistory report={report} t={t}/>
 <ValuationPanel legacy={legacyValuation} report={report} inputs={valuationInputs} onInputs={changeValuation} method={method} onMethod={setMethod} t={t} number={number} percent={percent} compact={compact}/>
 <p className="method-note">{report.schema==='yahoo39-v1'?t("The quality score is a weighted percentage from up to 39 analysis criteria with adjustable weights. Missing criteria are excluded. It is a screening model, not a probability of returns."):t("Saved SEC analysis from version 1: 16 criteria. Choose Refresh data for a new Yahoo analysis with 39 criteria.")}</p>{report.warnings?.map((w,i)=><p className="error" key={i}>{t(w)}</p>)}
 {(report.stale||(finite(latest.equity)&&latest.equity<=0))&&<p className="error">{report.stale?t("The latest available fiscal year ended more than 18 months ago."):''} {(finite(latest.equity)&&latest.equity<=0)?t("Non-positive equity: review solvency separately; excluded ratios can make the score appear more favourable."):''}</p>}
 <Fold title={t("03 · Valuation lab")}><ValuationLab report={report} inputs={valuationInputs} onInputs={changeValuation} scenarios={labScenarios} onScenarios={setLabScenarios} t={t} number={number} percent={percent}/></Fold>
 <Fold id="ratios" title={t("04 · Financial ratios")}><section className="card ratios"><div className="eyebrow">{t("RETURNS, LIQUIDITY & DEBT")}</div><h2>{t("The key ratios.")}</h2><div className="ratio-grid">{ratioRows.slice(0,8).map(([key,label,unit])=><div key={key}><span>{t.term(label)}</span><strong>{unit==='%'?percent(latest[key]):number(latest[key])+(finite(latest[key])?' ×':'')}</strong></div>)}</div><details><summary>{t("All ratios by fiscal year")}</summary><div className="table-scroll"><table><thead><tr><th>{t("Ratio")}</th>{report.years.slice().reverse().map(y=><th key={y.end}>{dateLabel(y.end,t.language)}</th>)}</tr></thead><tbody>{ratioRows.map(([k,l,u])=><tr key={k}><th>{t.term(l)}</th>{report.years.slice().reverse().map(y=><td key={y.end}>{u==='%'?percent(y[k]):number(y[k])+(finite(y[k])?' '+u:'')}</td>)}</tr>)}</tbody></table></div></details><RatioFormulas rows={ratioRows} t={t}/></section></Fold>
 <Fold id="charts" title={t("05 · Charts")}><section className="section-title"><div className="eyebrow">05 / {t("FINANCIAL HEALTH")}</div><h2>{t("The story behind the numbers.")}</h2><p>{t("Actual fiscal years; missing values remain visible as gaps.")}</p></section><div className="chart-grid"><Chart title={t("Revenue and earnings")} fields={[["revenue","Revenue"],["income","Net income"]]}/><Chart title={t("Cash flow generation")} fields={[["cfo","Operating cash flow"],["fcf","Free cash flow"]]}/><Chart title={t("Equity and debt")} fields={[["equity","Book value / equity"],["debt","Total debt"]]}/><Chart title={t("Profit margins")} unit="%" fields={[["grossMargin","Gross profit margin"],["netMargin","Net profit margin"]]}/></div></Fold>
 <Fold id="statements" title={t("06 · Financial statements")}><section className="card statements"><div className="eyebrow">{t("ANNUAL FIGURES")}</div><h2>{t("The financial backbone.")}</h2>{(()=>{const [d,s]=tableScale(report.years.flatMap(r=>moneyRows.map(([k])=>r[k])),t);return <div className="table-scroll"><table className="statement-table"><colgroup><col style={{width:'34%'}}/>{report.years.map(y=><col key={y.end} style={{width:(66/report.years.length)+'%'}}/>)}</colgroup><caption>{t("All amounts in")} {s} {report.currency} · {t("two decimal places")}</caption><thead><tr><th>{t("Metric")}</th>{report.years.slice().reverse().map(y=><th key={y.end}>{dateLabel(y.end,t.language)}</th>)}</tr></thead><tbody>{moneyRows.map(([key,label])=><tr key={key}><th>{t.term(label)}</th>{report.years.slice().reverse().map(y=><td key={y.end} title={number(y[key])}>{finite(y[key])?number(y[key]/d):'—'}</td>)}</tr>)}</tbody></table></div>;})()}<div className="table-scroll"><table className="statement-table"><colgroup><col style={{width:'34%'}}/>{report.years.map(y=><col key={y.end} style={{width:(66/report.years.length)+'%'}}/>)}</colgroup><caption>{t("Per-share amounts")+' · '+report.currency+' · '+t("margins in percent")}</caption><tbody>{[['eps','Diluted EPS'],['dps','Dividends per share *'],['grossMargin','Gross profit margin'],['netMargin','Net profit margin']].map(([k,l])=><tr key={k}><th>{t.term(l)}</th>{report.years.slice().reverse().map(y=><td key={y.end} title={k==='dps'?y.dpsSource||'':''}>{k.includes('Margin')?percent(y[k]):number(y[k])}</td>)}</tr>)}</tbody></table></div><p className="small muted">{t("* DPS: sum of per-share dividend events by ex-dividend date within the fiscal year, on a split-adjusted share basis. Refresh saved analyses to retrieve these data.")}</p></section></Fold>

 <Fold title={t("07 · Quality review")}><QualityReview report={report} t={t} number={number} percent={percent}/></Fold>
 <Fold id="criteria" title={t("08 · Score criteria")}><section className="card score-details"><div className="eyebrow">{t("ANALYSIS AND TREND RULES")}</div><h2>{t("All analysis criteria.")}</h2><WeightEditor report={report} weights={scoreWeights} overrides={scoreOverrides} onWeights={setScoreWeights} t={t} number={number}/><p>{number(personal.points)} / {number(personal.weight)} {t("weighted points × 100.")}</p><p className="method-note">{report.schema!=='yahoo39-v1'?t("Saved 16-criterion score from version 1."):t("A criterion may contain several base and trend weights. Annual series and current Yahoo/TTM values remain separate.")}</p><ScoreEvidence overrides={scoreOverrides} onOverrides={setScoreOverrides} criteria={report.schema==='yahoo39-v1'?personal.criteria:score.criteria} histories={report.originalHistories} currency={report.currency} t={t} number={number}/></section></Fold>
 <section className="card source-details"><h3>{t("Sources & interpretation")}</h3><p>{report.source||'SEC EDGAR (saved v1)'} · <a href={'https://finance.yahoo.com/quote/'+encodeURIComponent(report.symbol)+'/financials/'} target="_blank" rel="noreferrer">Yahoo Finance ↗</a></p><p>{t("Retrieved")}: {dateLabel(report.fetchedAt,t.language)}</p><p>{t("The score criteria use up to four fiscal years and current Yahoo data. Not every field is available for every ticker. Summary charts use unrounded source data; some series are rounded according to the analysis rules.")}</p><p>{t("Statement currency")}: {report.currency} · {t("Quote currency")}: {report.quoteCurrency||report.quote?.currency||'—'}</p></section></>}
 {report&&<PrintReport notes={researchEntries.find(e=>e.saved.report.symbol===report.symbol)?.notes} report={report} valuationValue={valuationValue} options={currentOptions} valuationInputs={valuationInputs} t={t} number={number} percent={percent} compact={compact} Chart={Chart}/>}
 </div></main><footer><span className="brand">Ticker<span>twister</span><small>DESKTOP · v{packageMetadata.version}</small></span><p>{t("A first investigation, not a final verdict.")}<br/>{t("For personal financial analysis. Not investment advice.")}</p><span>Copyright ©2026 Bob Ceulemans<br/>All Rights Reserved.</span></footer></>;
}
