import {profileStorage as localStorage} from './profileStorage.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
import {useSyncExternalStore,useEffect} from 'react';
import {nativeCall} from './native.mjs';
import {readRecord} from './aiArchiveData.mjs';
export {archiveKey,readRecord,relevantRecords} from './aiArchiveData.mjs';
let selection=[];try{const stored=JSON.parse(localStorage.getItem('tt-ai-print-selection')||'[]');if(Array.isArray(stored))selection=stored.filter(x=>typeof x==='string');}catch{}
let state={records:[],error:'',loaded:false,selectedIds:selection};const listeners=new Set();let pending;
const emit=()=>listeners.forEach(f=>f());
export function rememberRecord(raw,error=''){
 const r={...readRecord(raw),persisted:!error};state={...state,records:[r,...state.records.filter(x=>x.id!==r.id)],error};emit();return r;
}
export async function loadArchive(){if(pending)return pending;pending=nativeCall('ai-archive-list',{}).then(({records,invalid})=>{const good=[];let bad=invalid||0;for(const raw of records){try{good.push(readRecord(raw));}catch{bad++;}}
 const merged=new Map([...good,...state.records].map(r=>[r.id,r]));state={...state,records:[...merged.values()].sort((a,b)=>b.createdAt.localeCompare(a.createdAt)),error:[...merged.values()].some(r=>!r.persisted)?'ARCHIVE_SAVE_FAILED':bad?'ARCHIVE_PARTIAL':'',loaded:true};emit();}).catch(()=>{state={...state,error:'ARCHIVE_READ_FAILED',loaded:true};emit();}).finally(()=>{pending=null;});return pending;}
export async function retrySave(record){await nativeCall('ai-archive-save',{record:{id:record.id,input:record.input,language:record.language,response:record.response,createdAt:record.createdAt,translationOf:record.translationOf||null,settings:record.settings||null}});const records=state.records.map(r=>r.id===record.id?{...r,persisted:true}:r);state={...state,records,error:records.some(r=>!r.persisted)?'ARCHIVE_SAVE_FAILED':''};emit();}
export function useAIArchive(){useEffect(()=>{if(!state.loaded)loadArchive();window.addEventListener('ai-archive-refresh',loadArchive);return()=>window.removeEventListener('ai-archive-refresh',loadArchive);},[]);return useSyncExternalStore(f=>{listeners.add(f);return()=>listeners.delete(f);},()=>state);}

export function selectAIPrint(id,checked){const ids=new Set(state.selectedIds);checked?ids.add(id):ids.delete(id);state={...state,selectedIds:[...ids]};try{localStorage.setItem('tt-ai-print-selection',JSON.stringify(state.selectedIds));}catch{}emit();}
