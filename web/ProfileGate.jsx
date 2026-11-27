// SPDX-License-Identifier: AGPL-3.0-only
import {translator} from './i18n.mjs';
import {useState,useEffect,lazy,Suspense} from 'react';
import {nativeCall} from './native.mjs';
import {MacIcon,PreferenceFields} from './MacShell.jsx';
import {initialPreferences,savePreference,openProfilePreferences,rememberLoginChoice,clearLoginChoices,applyAppearance} from './workspacePreferences.mjs';
const App=lazy(()=>import('./App.jsx'));
const readPreferences=(profileID,defaultAppearance)=>initialPreferences(window.localStorage,window.__ttSystemLanguage||navigator.language,profileID,defaultAppearance);

export default function ProfileGate(){
 const [status,setStatus]=useState(null),[panel,setPanel]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [preferences,setPreferences]=useState(()=>readPreferences(null,'light'));
 const t=translator(preferences.language);
 useEffect(()=>{
  nativeCall('profile-status',{}).then(s=>{
   window.__ttProfile=s.active;
   setPreferences(s.active?openProfilePreferences(window.localStorage,window.sessionStorage,window.__ttSystemLanguage||navigator.language,s.active.id):readPreferences(null,s.testing?'system':'light'));
   setPanel(!s.testing&&!s.active);
   setStatus(s);
  }).catch(()=>setError('Accounts could not be loaded safely. Restart the app; nothing is overwritten.'));
  const show=()=>setPanel(true);
  window.addEventListener('profile-panel',show);
  return()=>window.removeEventListener('profile-panel',show);
 },[]);
 useEffect(()=>{
  const media=window.matchMedia('(prefers-color-scheme: dark)');
  const sync=()=>applyAppearance(preferences,media.matches);
  sync();media.addEventListener('change',sync);return()=>media.removeEventListener('change',sync);
 },[preferences.theme,preferences.appearance]);
 useEffect(()=>{
  document.documentElement.lang=preferences.language;
  nativeCall('set-language',{language:preferences.language}).catch(()=>{});
 },[preferences.language]);
 useEffect(()=>{
  function openVisiblePreferences(event){
   const field=document.querySelector('.profile-overlay [data-preference="language"]');
   if(field){event.stopImmediatePropagation();field.focus();}
  }
  window.addEventListener('desktop-preferences',openVisiblePreferences,true);
  return()=>window.removeEventListener('desktop-preferences',openVisiblePreferences,true);
 },[]);
 function changePreference(key,value){
  if(!savePreference(window.localStorage,key,value,status?.active?.id))return;
  if(panel&&!status?.active)rememberLoginChoice(window.sessionStorage,key,value);
  setPreferences(previous=>({...previous,[key]:value}));
 }
 async function act(action,account){
  setBusy(true);setError('');
  try{
   const result=await nativeCall(action,{account,language:preferences.language});
   if(result?.active){window.__ttProfile=result.active;setStatus(result);setPanel(false);}
  }
  catch(e){
   const messages={LOGIN_FAILED:'Incorrect account or password. Wait briefly and try again.',LOGIN_WAIT:'Wait briefly before trying to sign in again.',ACCOUNT_EXISTS_OR_LIMIT:'This username already exists or the limit was reached.',USE_NAME_AND_12_CHARACTER_PASSWORD:'Use a name of 2–40 characters and a password of at least 12 characters.',INVALID_ACCOUNT_NAME:'Use a name of 2–40 characters.',USE_12_CHARACTER_PASSWORD:'Use a password of at least 12 characters.'};
   setError(messages[e.message]||e.message);
  }finally{setBusy(false);}
 }
 const allowed=status&&(status.testing||status.active||status.accounts.length===0);
 const action=(id,label,icon,primary=false)=><button type="button" className={primary?'primary':''} disabled={busy} onClick={()=>act(id)}><MacIcon name={icon}/>{t(label)}</button>;
 return <>{allowed&&<div inert={panel?true:undefined}><Suspense fallback={null}><App preferences={preferences} onPreference={changePreference}/></Suspense></div>}
 {(!allowed||panel)&&<div className="profile-overlay profile-signin" role="dialog" aria-modal="true" aria-labelledby="profile-heading"><div className="profile-card">
 <div className="eyebrow">TICKERTWISTER · FINANCIAL RESEARCH STUDIO</div>
 <h2 id="profile-heading"><MacIcon name="account"/>{status?.active?.name||t('Your own research space.')}</h2>
 <PreferenceFields preferences={preferences} onChange={changePreference} t={t}/>
 <div className="profile-actions">{status?.active?<>{action('profile-lock','Lock / switch user','lock',true)}{action('profile-rename','Rename account','edit')}{action('profile-password','Change password','lock')}{action('profile-create','Create local account','plus')}{action('profile-delete','Delete account','trash')}</>:<>
 {status?.accounts.map(a=><button className="account-option" disabled={busy} key={a.id} onClick={()=>act('profile-login',a.id)}><MacIcon name="account"/>{a.name}<span>{t('Unlock')} →</span></button>)}
 {status&&action('profile-create','Create local account','plus',true)}</>}</div>
 <details className="profile-help"><summary>{t('About local accounts')}</summary><p>{t('Local accounts on this Mac. A personal password protects your encrypted dossier, AI archive and optionally saved API key.')}</p><p>{t('Enter your password in a secure Mac dialog. No cloud account, email or password recovery. Keep your password in a password manager. Other accounts start with an empty dossier.')}</p>{status&&!status.accounts.length&&<p>{t('Without an account, existing data remains in the old, unencrypted storage. You can copy this data when creating your first account.')}</p>}<p>{t('Standalone exports and PDFs are not covered by profile encryption. Use separate macOS user accounts if several people share this computer.')}</p></details>
 {error&&<p role="alert" className="error">{t(error)}</p>}{allowed&&<button className="profile-continue" disabled={busy} onClick={()=>{setPanel(false);if(!status.active){clearLoginChoices(window.sessionStorage);setPreferences(readPreferences());}}}>{status.active?t('Back to app'):t('Continue without an account')} →</button>}
 </div></div>}</>;
}
