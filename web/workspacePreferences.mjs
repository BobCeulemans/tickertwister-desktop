// SPDX-License-Identifier: AGPL-3.0-only
import {languageCodes} from './i18n.mjs';

// The original Modern and Professional labels used the internal IDs professional and modern.
export const themeLabels={professional:'Green',modern:'Blue',library:'Brown',futuristic:'Purple'};
const choices={language:languageCodes,theme:Object.keys(themeLabels),appearance:['system','light','dark']};
const globalPrefix='tt-workspace-';
const pendingPrefix='tt-next-login-';
const profileKey=(id,key)=>'tt-profile:'+id+':tt-'+key;

export function initialPreferences(storage,locale,profileID,defaultAppearance='system'){
 const base=String(locale||'').toLowerCase().split(/[-_]/)[0];
 const defaults={language:languageCodes.includes(base)?base:'en',theme:'professional',appearance:defaultAppearance};
 for(const key of Object.keys(defaults)){
  const keys=[profileID&&profileKey(profileID,key),globalPrefix+key,'tt-'+key].filter(Boolean);
  try{
   const value=keys.map(k=>storage.getItem(k)).find(v=>choices[key].includes(v));
   if(value)defaults[key]=value;
  }catch{/* A disabled storage area still allows session preferences. */}
 }
 return defaults;
}
export function savePreference(storage,key,value,profileID){
 if(!choices[key]?.includes(value))return false;
 try{storage.setItem(profileID?profileKey(profileID,key):globalPrefix+key,value);}catch{/* Session settings still apply. */}
 return true;
}
export function rememberLoginChoice(session,key,value){
 if(choices[key]?.includes(value))try{session.setItem(pendingPrefix+key,value);}catch{}
}
export function clearLoginChoices(session){
 for(const key of Object.keys(choices))try{session.removeItem(pendingPrefix+key);}catch{}
}
export function openProfilePreferences(storage,session,locale,profileID){
 const preferences=initialPreferences(storage,locale,profileID);
 for(const key of Object.keys(choices)){
  let explicit;
  try{explicit=session.getItem(pendingPrefix+key);}catch{}
  if(choices[key].includes(explicit))preferences[key]=explicit;
  // Capture defaults on first use so later sign-in changes belong only to the next account.
  savePreference(storage,key,preferences[key],profileID);
 }
 clearLoginChoices(session);
 return preferences;
}
export function applyAppearance(preferences,dark){
 const {dataset}=document.documentElement;
 dataset.theme='mac';
 dataset.accent=preferences.theme;
 dataset.appearance=preferences.appearance==='system'?(dark?'dark':'light'):preferences.appearance;
}
