import {formatDate,languageInfo} from './i18n.mjs';
// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
export function decimalInput(value){if(value===''||value==null)return '';const n=Number(value);return Number.isFinite(n)?n.toFixed(2):String(value);}
export const statuses=[['research','In onderzoek','Researching'],['watch','Opvolgen','Watch'],['hard','Too hard','Too hard'],['candidate','Beleggingskandidaat','Investment candidate']];
export const statusLabel=(status,t)=>{const s=statuses.find(s=>s[0]===status)||statuses[0];return t(s[1],s[2]);};
// Conservative line wrapping for printable, user-written notes; preserve all text.
export function notePages(text,columns=85,lines=32){
 const wrapped=[];for(const paragraph of String(text||'').split('\n')){let rest=paragraph;while(rest.length>columns){let cut=rest.lastIndexOf(' ',columns);if(cut<1)cut=columns;wrapped.push(rest.slice(0,cut));rest=rest.slice(cut);if(rest.startsWith(' '))rest=rest.slice(1);}wrapped.push(rest);}
 const pages=[];for(let i=0;i<wrapped.length;i+=lines)pages.push(wrapped.slice(i,i+lines).join('\n'));return pages;
}
export function roundedAssumptions(value){return {...value,rate:decimalInput(value.rate),growth:decimalInput(value.growth)};}

export function dateLabel(value,language=globalThis.document?.documentElement?.lang||'nl'){return formatDate(value,language);}

export function shortAmount(value,number,t){if(!Number.isFinite(value))return '—';const a=Math.abs(value);const [d,u]=a>=1e12?[1e12,t("trn")]:a>=1e9?[1e9,t("bln")]:a>=1e6?[1e6,t("mln")]:a>=1e3?[1e3,t("k")]:[1,''];return number(value/d)+(u?' '+u:'');}
export function marketValue(report){const cap=report?.quote?.marketCap;if(Number.isFinite(cap)&&cap>0)return cap;const p=report?.quote?.price,n=report?.valuationShares;if(report?.quote?.currency!==report?.currency&&report?.quoteBasis?.verified!==true)return null;const ratio=report.quoteBasis?.ordinaryPerQuote||1;return Number.isFinite(p)&&p>0&&Number.isFinite(n)&&n>0?p*n/ratio:null;}

export function archiveDateTime(value,language=globalThis.document?.documentElement?.lang||'nl'){const d=new Date(value);return Number.isFinite(d.getTime())?d.toLocaleDateString(languageInfo(language).locale,{day:'2-digit',month:'2-digit',year:'numeric',timeZone:globalThis.__ttTimeZone})+' · '+d.toLocaleTimeString(languageInfo(language).locale,{hour:'2-digit',minute:'2-digit',timeZone:globalThis.__ttTimeZone}):'—';}

// Choose a shared table unit around the median non-zero monetary observation.
export function tableScale(values,t){const a=values.filter(v=>Number.isFinite(v)&&v!==0).map(Math.abs).sort((a,b)=>a-b);const typical=a.length?a[Math.floor(a.length/2)]:0;return typical>=1e13?[1e12,t("trillion")]:typical>=1e10?[1e9,t("billion")]:typical>=1e7?[1e6,t("million")]:typical>=1e4?[1e3,t("thousand")]:[1,t("units")];}

// Local reminder: preserve the entered wall-clock time, without timezone conversion.
export function reminderLabel(value){const s=String(value||'');return dateLabel(s)+(s.includes('T')?' · '+s.slice(11,16):'');}
