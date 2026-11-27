// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {useEffect,useRef,useState} from 'react';
import {LANGUAGES} from './i18n.mjs';
import {themeLabels} from './workspacePreferences.mjs';
import {profileStorage} from './profileStorage.mjs';
import BrandMark from './BrandMark.jsx';

export function MacIcon({name}) {
 const paths={note:'M5 3h14a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1ZM8 8h8M8 12h8M8 16h5',sidebar:'M3 4h18v16H3ZM9 4v16',forward:'m10 5 7 7-7 7',language:'M2 12h20M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20ZM12 2c-6 5-6 15 0 20 6-5 6-15 0-20Z',lock:'M5 10h14v11H5ZM8 10V7a4 4 0 0 1 8 0v3M12 14v3',edit:'m4 16-1 5 5-1L20 8l-4-4ZM13 7l4 4',trash:'M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7',heart:'M12 21 3.6 13C-3 6 6.6-2 12 6c5.4-8 15 .1 8.4 7Z',palette:'M12 3a9 9 0 1 0 0 18h1a2 2 0 0 0 1-3.7c-1.3-1 .1-3.3 2.2-3.3h1.3C24 14 21 3 12 3ZM6 10h.1M9 6.6h.1M14 6h.1M18 9h.1',home:'M3 11 12 3l9 8M5 10v11h5v-7h4v7h5V10',library:'M4 4h4v17H4ZM11 4h4v17h-4ZM18 4l3 16',open:'M3 8h7l2 2h9l-3 10H3ZM3 8V4h7l2 4',search:'m16 16 5 5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',settings:'M4 6h16M4 12h16M4 18h16M8 3v6M16 9v6M10 15v6',account:'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M4 21v-2a8 8 0 0 1 16 0v2',chart:'M4 3v18h17M8 16v-4M13 16V7M18 16V4',value:'M12 3v18M17 6H9a3 3 0 0 0 0 6h6a3 3 0 0 1 0 6H7',quality:'M12 3 3 7v6c0 5 9 9 9 9s9-4 9-9V7ZM8 12l3 3 5-6',table:'M3 4h18v16H3ZM3 10h18M9 4v16',back:'m14 5-7 7 7 7',save:'M4 3h14l3 3v15H3V3ZM7 3v7h10V3M7 21v-7h10v7',print:'M6 8V3h12v5M6 17H3V8h18v9h-3M6 14h12v7H6Z',expand:'M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5',plus:'M12 5v14M5 12h14',sun:'M12 2v2M12 20v2M2 12h2M20 12h2M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0'};
 return <svg viewBox="0 0 24 24" className="mac-icon" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]||paths.chart}/></svg>;
}

export function PreferenceFields({preferences,onChange,t}){
 return <div className="workspace-preferences">
  <label><span><MacIcon name="language"/>{t('App language')}</span><select data-preference="language" value={preferences.language} onChange={e=>onChange('language',e.target.value)}>{LANGUAGES.map(l=><option key={l.code} value={l.code}>{l.name}</option>)}</select></label>
  <label><span><MacIcon name="palette"/>{t('Accent theme')}</span><select value={preferences.theme} onChange={e=>onChange('theme',e.target.value)}>{Object.entries(themeLabels).map(([id,label])=><option key={id} value={id}>{t(label)}</option>)}</select></label>
  <label><span><MacIcon name="sun"/>{t('Appearance')}</span><select value={preferences.appearance} onChange={e=>onChange('appearance',e.target.value)}>{[['system','Follow macOS'],['light','Light'],['dark','Dark']].map(([id,label])=><option key={id} value={id}>{t(label)}</option>)}</select></label>
 </div>;
}

export default function MacShell({t,preferences,onPreference,onBack,onForward,canBack,canForward,englishTerms,setEnglishTerms,deskOpen,report,busy,onHome,onNew,view,entries=[],openAnalyses=[],onNavigate,onSwitch,onCloseAnalysis,onResearch,onClose,onOpen,onSave,onPrint,onExpand,expanded,version}) {
 const [settings,setSettings]=useState(false);
 const [collapsed,setCollapsed]=useState(()=>{try{return profileStorage.getItem('tt-sidebar-hidden')==='true';}catch{return false;}});
 function toggleSidebar(){
  const hide=!collapsed;setCollapsed(hide);
  try{profileStorage.setItem('tt-sidebar-hidden',String(hide));}catch{}
 }
 const dialog=useRef(null),trigger=useRef(null);
 useEffect(()=>{if(settings)dialog.current?.showModal();else if(dialog.current?.open)dialog.current.close();},[settings]);
 function close(){setSettings(false);trigger.current?.focus();}
 useEffect(()=>{const show=()=>setSettings(true);window.addEventListener('desktop-preferences',show);return()=>window.removeEventListener('desktop-preferences',show);},[]);
 const sections=[['valuation','value','Value'],['lab','chart','Valuation lab'],['ratios','table','Financial ratios'],['charts','chart','Charts'],['statements','table','Financial statements'],['quality-review','quality','Quality review'],['criteria','quality','Score criteria']];
 const action=(icon,label,fn,disabled=false)=><button type="button" className={'mac-tool'+(icon==='account'?' profile-button':'')} title={label} aria-label={label} disabled={disabled} onClick={fn}><MacIcon name={icon}/><span>{label}</span></button>;
 return <><aside className="mac-sidebar" id="workspace-sidebar" hidden={collapsed} aria-label={t('Workspace')}>
  <button className="mac-brand" onClick={onHome} aria-label="Tickertwister"><BrandMark/><span>Ticker<b>twister</b><small>RESEARCH STUDIO</small></span></button>
  <div className="mac-sidebar-fixed">
  <a className="sponsor-link" aria-label="GitHub Sponsors" title="GitHub Sponsors" href="https://github.com/sponsors/BobCeulemans" target="_blank" rel="noopener noreferrer"><MacIcon name="heart"/><span>GitHub Sponsors ↗</span></a>
  <div className="mac-nav-label">{t('Workspace')}</div>
  <nav className="mac-workspaces">{[['overview','home','Analysis'],['research','library','Research dossier']].map(([key,icon,label])=><button key={key} data-action={key==='research'?'research-toggle':undefined} aria-current={view===key?'page':undefined} onClick={()=>onNavigate(key)}><MacIcon name={icon}/><span>{t(label)}</span>{key==='research'&&<small className="nav-count">{entries.length}</small>}</button>)}</nav>
  <div className="mac-nav-label">{t('Tools')}</div><nav className="mac-workspaces"><button aria-current={view==='archive'?'page':undefined} onClick={()=>onNavigate('archive')}><MacIcon name="quality"/>{t('AI archive')}</button></nav>
  </div><div className="mac-sidebar-scroll">
  {openAnalyses.length>0&&<><div className="mac-nav-label">{t('Open analyses')}</div><nav className="mac-workspaces">{openAnalyses.map(saved=><div className="open-analysis-row" key={saved.report.symbol}><button aria-current={view==='analysis'&&report?.symbol===saved.report.symbol?'page':undefined} title={saved.report.symbol+' · '+saved.report.name} onClick={()=>onSwitch(saved)}><MacIcon name="chart"/><span>{saved.report.symbol}<small>{saved.report.name}</small></span></button><button className="close-analysis" title={t('Close analysis')} aria-label={t('Close analysis')+' '+saved.report.symbol} onClick={()=>onCloseAnalysis(saved.report.symbol)}>×</button></div>)}</nav></>}
  {report&&view==='analysis'&&<><div className="mac-nav-label">{t('In this analysis')}</div><nav className="mac-sections">{sections.map(([id,icon,label])=><a href={'#'+id} key={id}><MacIcon name={icon}/>{t(label)}</a>)}</nav></>}
  </div><div className="mac-sidebar-bottom"><button className="sidebar-profile profile-button" aria-label={window.__ttProfile?.name||t('Account')} title={window.__ttProfile?.name||t('Account')} onClick={()=>window.dispatchEvent(new Event('profile-panel'))}><span className="profile-initials" aria-hidden="true">{window.__ttProfile?.name?.trim()?Array.from(window.__ttProfile.name.trim())[0].toLocaleUpperCase(t.language):<MacIcon name="account"/>}</span><span>{window.__ttProfile?.name||t('Account')}</span></button><span>Tickertwister · v{version}</span></div>
 </aside><header className="mac-toolbar">
  <div className="mac-history"><button type="button" className="mac-tool" onClick={toggleSidebar} aria-controls="workspace-sidebar" aria-expanded={!collapsed} aria-label={t(collapsed?'Show sidebar':'Hide sidebar')} title={t(collapsed?'Show sidebar':'Hide sidebar')}><MacIcon name="sidebar"/></button>{action('back',t('Back'),onBack,!canBack||busy)}{action('forward',t('Forward'),onForward,!canForward||busy)}</div><div className="mac-toolbar-title">{view==='analysis'&&report?report.symbol:t({overview:'Analysis',research:'Research dossier',archive:'AI archive'}[view]||'Analysis')}<small>{deskOpen?t('Your private research desk'):view==='analysis'&&report?report.name:t('The Value Investor’s Notebook')}</small></div>
  <div className="mac-tools">{view==='analysis'&&report&&<>{action('plus',t('New analysis'),onNew)}{action('save',t('Save analysis'),onSave)}{action('expand',expanded?t('Collapse all'):t('Expand all'),onExpand)}{action('print',t('Print report'),onPrint)}</>}{action('open',t('Open analysis…'),onOpen,busy)}{action('search',t('Find')+' ⌘F',()=>window.dispatchEvent(new Event('desktop-find')))}<button ref={trigger} className="mac-tool" aria-label={t('Preferences')} title={t('Preferences')} onClick={()=>setSettings(true)}><MacIcon name="settings"/><span>{t('Preferences')}</span></button></div>
 </header><dialog className="mac-preferences" ref={dialog} aria-labelledby="preferences-title" onCancel={close} onClose={()=>setSettings(false)}><div className="mac-dialog-title"><h2 id="preferences-title">{t('Preferences')}</h2><button onClick={close} aria-label={t('Close')}>×</button></div>
  <PreferenceFields preferences={preferences} onChange={onPreference} t={t}/>
  <label className="mac-checkbox"><input type="checkbox" checked={englishTerms} onChange={e=>setEnglishTerms(e.target.checked)}/>{t('Keep financial terms in English')}</label>
  <p className="muted small">{t('AI output language is chosen separately in the research desk.')}</p><button className="primary" onClick={close}>{t('Done')}</button>
 </dialog></>;
}
