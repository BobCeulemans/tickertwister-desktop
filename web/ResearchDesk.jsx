import {profileStorage as localStorage} from './profileStorage.mjs';
import {dateLabel} from './presentation.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import AIArchive from './AIArchive.jsx';
import ResearchTransfer from './researchTransferUI.jsx';
import {sameDossier} from './dossierTransfer.mjs';
import {personalScore} from './weights.mjs';
import './research-review.css';
import ResearchPrint from './ResearchPrint.jsx';
import {printHTML} from './print.mjs';
import {statuses,statusLabel} from './presentation.mjs';
import Comparison from './Comparison.jsx';
import {loadAnalysis} from './data.mjs';
import {useEffect,useImperativeHandle,useLayoutEffect,useRef,useState} from 'react';
import {nativeCall} from './native.mjs';
import {makeSaved,refreshedValuationOptions} from './saved.mjs';
import {emptyDesk,emptyNotes,parseDesk,comparison,selectedAIReports} from './research.mjs';
export default function ResearchDesk({ref,requestedEntry,onEntries,onClose,visible,mode="research",report,options,t,number,percent}){
 const deskElement=useRef(null),committed=useRef(emptyDesk()),writing=useRef(false);
 const [forExport,setForExport]=useState([]),[fullArchive,setFullArchive]=useState(false),[transferring,setTransferring]=useState(false);
 useLayoutEffect(()=>{
  if(visible)deskElement.current?.querySelectorAll('details[open]').forEach(el=>{el.open=false;});
 },[visible,mode,requestedEntry]);
 const [view,setView]=useState(()=>{try{return localStorage.getItem('tt-desk-view')==='cards'?'cards':'list';}catch{return 'list';}});
 function chooseView(v){setView(v);try{localStorage.setItem('tt-desk-view',v);}catch{}}
 const [search,setSearch]=useState(''),[statusFilter,setStatusFilter]=useState('all');
 const [removeConfirm,setRemoveConfirm]=useState(''),[removals,setRemovals]=useState([]);
 const lastRemoval=removals.at(-1);
 const [snapshot,setSnapshot]=useState(null);
 const [refreshing,setRefreshing]=useState(false);
 const [desk,setDesk]=useState(emptyDesk),[ready,setReady]=useState(false),[error,setError]=useState(''),[dirty,setDirty]=useState(false),[saving,setSaving]=useState(false),[active,setActive]=useState(''),[selected,setSelected]=useState([]),[savedAt,setSavedAt]=useState('');
 useEffect(()=>{nativeCall('research-load',{}).then(result=>{const loaded=result.content?parseDesk(result.content):emptyDesk();committed.current=loaded;setDesk(loaded);setReady(true);setActive(loaded.entries[0]?.saved.report.symbol||'');}).catch(()=>setError('load'));},[]);
 useEffect(()=>{onEntries?.(desk.entries);},[desk,onEntries]);
 useEffect(()=>{if(ready&&requestedEntry&&desk.entries.some(e=>e.saved.report.symbol===requestedEntry.symbol)){setActive(requestedEntry.symbol);setSelected([]);setSearch('');setStatusFilter('all');}},[ready,requestedEntry]);
 const filteredEntries=desk.entries.filter(e=>(statusFilter==='all'||e.notes.status===statusFilter)&&(!search.trim()||(e.saved.report.symbol+' '+e.saved.report.name).toLocaleLowerCase().includes(search.trim().toLocaleLowerCase())));
 const update=next=>{setDesk(next);setDirty(true);setError('');};
 function stamp(){setSavedAt(new Date().toLocaleTimeString(undefined,{timeZone:window.__ttTimeZone,hour:"2-digit",minute:"2-digit"}));}
 async function persist(next){
  const checked=parseDesk(next);await nativeCall('research-save',{content:JSON.stringify(checked)});committed.current=checked;stamp();return checked;
 }
 async function save(next=desk){
  if(!ready||writing.current||transferring)return;
  writing.current=true;setSaving(true);
  try{setDesk(await persist(next));setDirty(false);setRemovals([]);setRemoveConfirm('');setError('');}
  catch{setError('save');}finally{writing.current=false;setSaving(false);}
 }
 useEffect(()=>{nativeCall('research-dirty',{dirty}).catch(()=>{});},[dirty]);
 useImperativeHandle(ref,()=>({async saveCurrent(){
  if(!ready||writing.current||transferring||refreshing||!report)throw Error('DOSSIER_NOT_READY');
  if(removals.length)throw Error('DOSSIER_DIRTY');
  const name=report.symbol,saved=makeSaved(report,options);
  const withSnapshot=previous=>{
   if(!previous.entries.some(e=>e.saved.report.symbol===name)&&previous.entries.length>=30)throw Error('DOSSIER_FULL');
   return {...previous,entries:[{saved,notes:previous.entries.find(e=>e.saved.report.symbol===name)?.notes??emptyNotes()},...previous.entries.filter(e=>e.saved.report.symbol!==name)]};
  };
  const disk=withSnapshot(committed.current),draft=withSnapshot(desk);
  writing.current=true;setSaving(true);
  try{const checked=await persist(disk);setDesk(dirty?draft:checked);setActive(name);if(fullArchive)setForExport(draft.entries.map(e=>e.saved.report.symbol));setError('');}
  catch{throw Error('SAVE_FAILED');}finally{writing.current=false;setSaving(false);}
 }}));
 function chooseAll(checked){setFullArchive(checked);setForExport(checked?desk.entries.map(e=>e.saved.report.symbol):[]);}
 function chooseExport(name,checked){setFullArchive(false);setForExport(s=>checked?[...s,name]:s.filter(x=>x!==name));}
 function imported(next){committed.current=next;setDesk(next);setDirty(false);setRemovals([]);setRemoveConfirm('');setError('');setSelected([]);setActive(next.entries.some(e=>e.saved.report.symbol===active)?active:(next.entries[0]?.saved.report.symbol||''));chooseAll(false);stamp();}
 function removeEntry(entry){
  const symbol=entry.saved.report.symbol;
  const index=desk.entries.indexOf(entry);
  if(index<0)return;
  const entries=desk.entries.filter(e=>e!==entry);
  setRemovals(previous=>[...previous,{entry,index}]);
  setForExport(previous=>previous.filter(x=>x!==symbol));
  setFullArchive(false);
  setSelected(previous=>previous.filter(x=>x!==symbol));
  if(active===symbol)setActive(entries[0]?.saved.report.symbol||'');
  setRemoveConfirm('');
  update({...desk,entries});
 }
 function undoRemoval(){
  if(!lastRemoval)return;
  const {entry,index}=lastRemoval;
  const entries=[...desk.entries];
  entries.splice(index,0,entry);
  const next={...desk,entries};
  setDesk(next);
  setRemovals(previous=>previous.slice(0,-1));
  setActive(entry.saved.report.symbol);
  setRemoveConfirm('');
  setError('');
  setDirty(removals.length>1||!sameDossier(next,committed.current));
 }
 const current=desk.entries.find(e=>e.saved.report.symbol===active),chosen=desk.entries.filter(e=>selected.includes(e.saved.report.symbol));
 const note=(key,value)=>update({...desk,entries:desk.entries.map(e=>e===current?{...e,notes:{...e.notes,[key]:value}}:e)});
 const targets=chosen.length?chosen:current?[current]:[];
 async function refresh(){setRefreshing(true);setError('');let entries=[...desk.entries],failed=[];for(const e of targets){try{const r=await loadAnalysis(e.saved.report.symbol);entries=entries.map(x=>x===e?{...e,saved:makeSaved(r,refreshedValuationOptions(e.saved,r))}:x);}catch{failed.push(e.saved.report.symbol);}}update({...desk,entries});if(failed.length)setError('refresh:'+failed.join(', '));setRefreshing(false);}

 const thesis=current&&<details className="thesis-editor"><summary>{t("My investment thesis")}</summary><div className="studio-title"><h3>{current.saved.report.symbol} - {current.saved.report.name}</h3><button onClick={()=>window.dispatchEvent(new CustomEvent('desktop-open-report',{detail:current.saved}))}>{t("Open saved analysis")}</button></div><p className="small muted">{t("Open saved analysis displays the saved figures, weights and valuation assumptions on the results page. No new Yahoo data is fetched.")}</p><label>{t("Notes for company")}<select aria-label={t("Company for notes")} value={active} onChange={e=>{setActive(e.target.value);setRemoveConfirm('');}}>{desk.entries.map(e=><option key={e.saved.report.symbol} value={e.saved.report.symbol}>{e.saved.report.symbol} · {e.saved.report.name}</option>)}</select></label><div className="inputs thesis-meta"><label>{t("Research status")}<select value={current.notes.status} onChange={e=>note('status',e.target.value)}>{statuses.map(([value,nl,en])=><option key={value} value={value}>{t(nl,en)}</option>)}</select></label><label>{t("Review again on")}<span className="review-moment"><input type="date" aria-label={t("Review date")} value={current.notes.reviewDate?.slice(0,10)||''} onChange={e=>note('reviewDate',e.target.value+(e.target.value&&current.notes.reviewDate?.includes('T')?current.notes.reviewDate.slice(10):''))}/><input type="time" aria-label={t("Time (optional)")} step="60" disabled={!current.notes.reviewDate} value={current.notes.reviewDate?.includes('T')?current.notes.reviewDate.slice(11,16):''} onChange={e=>note('reviewDate',current.notes.reviewDate.slice(0,10)+(e.target.value?'T'+e.target.value:''))}/></span></label></div><div className="thesis-notes">{[['thesis',t("Why would I want to own this business?")],['risks',t("What could go wrong?")],['disconfirm',t("What evidence would disprove my thesis?")],['nextStep',t("My next research question")]].map(([k,l])=><label key={k}>{l}<textarea data-note={k} rows={6} maxLength={12000} value={current.notes[k]} onChange={e=>note(k,e.target.value)}/></label>)}</div><p className="muted small">{t("The date is your own reminder in this dossier; no notifications are sent.")}</p><AIArchive symbols={[active]} t={t}/><div className="thesis-save"><button className="primary" data-action="thesis-save" disabled={!dirty||saving||refreshing} onClick={()=>save()}>{saving?t("Saving…"):t("Save changes")}</button><span role="status">{dirty?t("Changes not saved yet"):t("All changes saved")}</span></div></details>;
 return <section ref={deskElement} className={'card research-desk research-mode-'+mode+(!visible?' studio-hidden':'')} id="research-desk"><div className="studio-title"><div><div className="mac-kicker">{t("Library")}</div><h2>{mode==="archive"?t("AI archive"):t("My research dossier")}</h2><p>{t("A private library of companies and ideas.")}</p></div><span className="studio-badge">{desk.entries.length}/30 {t("dossiers")}</span></div>
 <div className="desk-actions"><button disabled={!ready||saving||transferring||refreshing||!dirty} data-action="desk-save" onClick={()=>save()}>{saving?t("Saving…"):t("Save dossier changes")}</button><button disabled={!ready||saving||refreshing||!desk.entries.length} data-action="desk-print" title={t("Prints checked companies, or the open dossier if none are checked. Includes current notes, even if not saved yet.")} onClick={async()=>{try{const html=printHTML('#research-print');if(html)await nativeCall('print',{html});}catch{setError('print');}}}>{chosen.length?t("Print selected companies"):t("Print this company")}</button><span role="status">{dirty?t("Changes not saved yet"):savedAt?t("Saved locally at ")+savedAt:ready?t("Local dossier loaded"):t("Loading dossier…")}</span></div>
 {error&&<p className="error" role="alert">{error==='load'?t("The local dossier could not be read safely. Nothing will be overwritten. Regular analysis remains available."):error==='print'?t("The dossier could not be printed. Please try again."):error.startsWith('refresh:')?t("Refresh failed for: ")+error.slice(8):error==='full'?t("Maximum 30 companies. Remove a dossier first."):t("Saving failed; your changes remain in this window.")}</p>}
 <p className="method-note">{t("Save edits before quitting. Saving an analysis updates the snapshot and keeps its thesis. Dossier transfers are protected with a separate password.")}</p>
 {!desk.entries.length&&<div className="desk-empty"><h3>{t("Your first conviction starts with a question.")}</h3><p>{t("Analyse a company and add it here. Then record your thesis and your strongest counterargument.")}</p></div>}
 {ready&&mode!=="archive"&&<><ResearchTransfer desk={desk} committed={committed.current} selected={forExport} full={fullArchive} dirty={dirty} busy={saving||refreshing||transferring} setBusy={setTransferring} onImported={imported} t={t}/>
 {!desk.entries.length&&<label className="export-all"><input type="checkbox" checked={fullArchive} onChange={e=>chooseAll(e.target.checked)}/>{t('Include the entire AI archive')}</label>}</>}
 <fieldset className="desk-fields" disabled={saving||refreshing||transferring}>{desk.entries.length>0&&<><div className="company-collection-frame">{current&&<div className="desk-selected-actions"><strong>{current.saved.report.symbol} · {current.saved.report.name}</strong><button className="primary" data-action="view-selected-analysis" onClick={()=>window.dispatchEvent(new CustomEvent("desktop-open-report",{detail:current.saved}))}>{t("View analysis")}</button></div>}<details className="company-collection"><summary>{t("My companies")} · {desk.entries.length}</summary><label className="export-all"><input type="checkbox" ref={el=>{if(el)el.indeterminate=!fullArchive&&forExport.length>0;}} checked={fullArchive} onChange={e=>chooseAll(e.target.checked)}/>{t('Select all for export, including the entire AI archive')}</label><div className="library-controls"><label className="library-search"><span className="sr-only">{t("Search companies…")}</span><input type="search" placeholder={t("Search companies…")} value={search} onChange={e=>setSearch(e.target.value)}/></label><label className="library-filter"><span className="sr-only">{t("Research status")}</span><select aria-label={t("Research status")} value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}><option value="all">{t("All companies")}</option>{statuses.map(([value,nl,en])=><option key={value} value={value}>{t(nl,en)}</option>)}</select></label><div className="desk-view-controls" role="group" aria-label={t("Company view")}><button aria-pressed={view==='cards'} onClick={()=>chooseView('cards')}>{t("Cards")}</button><button data-action="list-view" aria-pressed={view==='list'} onClick={()=>chooseView('list')}>{t("List")}</button></div></div>{!filteredEntries.length&&<p className="library-no-results">{t("No companies match these filters.")}</p>}<aside className={'watchlist watchlist-'+view}>{filteredEntries.map(e=>{const r=e.saved.report,personal=personalScore(r,e.saved.options.scoreWeights,e.saved.options.scoreOverrides);return <article key={r.symbol} className={active===r.symbol?'active':''}><button className="watch-open" aria-pressed={active===r.symbol} onClick={()=>setActive(r.symbol)}><strong>{r.symbol}</strong><span>{r.name}</span></button><span className={"status-badge status-"+e.notes.status}>{statusLabel(e.notes.status,t)}</span><span className="watch-score">{number(personal.custom?personal.value:r.score.value,0)}/100 <small>· {r.score.available}/{r.score.total}{personal.custom?' · '+t("My score"):''}</small></span><span className="watch-dates"><small>{t("Fiscal year")}: {dateLabel(r.years.at(-1).end,t.language)}</small><small>{t("Retrieved")}: {dateLabel(r.fetchedAt,t.language)}</small></span><div className="watch-selections"><label className="export-toggle"><input type="checkbox" aria-label={t('Export')+' '+r.symbol} checked={forExport.includes(r.symbol)} onChange={ev=>chooseExport(r.symbol,ev.target.checked)}/>{t('Export')}</label><label className="compare-toggle"><input type="checkbox" checked={selected.includes(r.symbol)} disabled={!selected.includes(r.symbol)&&selected.length>=4} onChange={ev=>setSelected(s=>ev.target.checked?[...s,r.symbol]:s.filter(x=>x!==r.symbol))}/>{t("Compare")}</label></div><button className="watch-remove" aria-label={t("Remove ")+r.symbol} title={t("Remove company from study")} onClick={()=>setRemoveConfirm(r.symbol)}>×</button>{removeConfirm===r.symbol&&<div className="watch-confirm" role="alert"><span>{t("Remove company and notes? Save changes afterwards.")} <b>{r.symbol}</b></span><div className="confirm-actions"><button onClick={()=>setRemoveConfirm('')}>{t("Cancel")}</button><button className="desk-remove" onClick={()=>removeEntry(e)}>{t("Remove")}</button></div></div>}</article>;})}</aside></details></div><Comparison reports={selectedAIReports(targets,report,options)} refresh={refresh} refreshing={refreshing} t={t} number={number} percent={percent} onSnapshot={setSnapshot} afterFinancials={thesis}/>

</>}
 </fieldset>{mode==="archive"&&<AIArchive symbols={[]} all t={t}/>}<div className="desk-archive-link"><button onClick={()=>window.dispatchEvent(new CustomEvent("desktop-navigate",{detail:"archive"}))}>{t("AI archive")}</button></div>{dirty&&<div className="desk-savebar"><button className="primary" disabled={saving||refreshing} onClick={()=>save()}>{t("Save dossier changes")}</button>{lastRemoval&&<button disabled={saving||refreshing||transferring} onClick={undoRemoval}>{t("Undo removal")} · {lastRemoval.entry.saved.report.symbol}</button>}</div>}<ResearchPrint entries={chosen.length?chosen:current?[current]:[]} snapshot={chosen.length>=2?snapshot:null} t={t} number={number} percent={percent}/></section>;
}
