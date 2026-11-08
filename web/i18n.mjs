// SPDX-License-Identifier: AGPL-3.0-only
// Display-only localisation. Never convert stored values, currencies or identifiers.
import financialKeys from './locales/financial-keys.json' with {type:'json'};
import en from './locales/en.json' with {type:'json'};
import nl from './locales/nl.json' with {type:'json'};
import fr from './locales/fr.json' with {type:'json'};
import de from './locales/de.json' with {type:'json'};
import es from './locales/es.json' with {type:'json'};
import it from './locales/it.json' with {type:'json'};
import pt from './locales/pt.json' with {type:'json'};
export const LANGUAGES=[{code:'nl',name:'Nederlands',locale:'nl-BE',english:'Dutch'},{code:'en',name:'English',locale:'en-US',english:'English'},{code:'fr',name:'Français',locale:'fr-FR',english:'French'},{code:'de',name:'Deutsch',locale:'de-DE',english:'German'},{code:'es',name:'Español',locale:'es-ES',english:'Spanish'},{code:'it',name:'Italiano',locale:'it-IT',english:'Italian'},{code:'pt',name:'Português',locale:'pt-PT',english:'European Portuguese'}];
export const languageCodes=LANGUAGES.map(l=>l.code);
export const languageInfo=code=>LANGUAGES.find(l=>l.code===code)||LANGUAGES[1];
export const catalogs={en,nl,fr,de,es,it,pt};
export function translator(code='en',englishTerms=false){const language=languageInfo(code).code,dict=catalogs[language];const t=(key,legacyEnglish)=>{const id=legacyEnglish??key;return dict[id]||en[id]||(language==='nl'&&legacyEnglish?key:id)||'';};t.language=language;t.prose=value=>{const text=String(value||'');if(dict[text])return dict[text];const keys=financialKeys.filter(k=>k.length>3).sort((a,b)=>b.length-a.length);const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');return text.replace(new RegExp(keys.map(escape).join('|'),'gi'),m=>englishTerms?m:t(keys.find(k=>k.toLowerCase()===m.toLowerCase())||m));};t.term=(key,legacyDutch)=>englishTerms?key:t(legacyDutch||key,key);return t;}
export function formatDate(value,code){const s=String(value||''),m=s.match(/^(\d{4})-(\d{2})-(\d{2})/);if(!m)return '—';const d=new Date(Date.UTC(+m[1],+m[2]-1,+m[3]));if(!Number.isFinite(d.getTime()))return '—';return new Intl.DateTimeFormat(languageInfo(code).locale,{day:'2-digit',month:'2-digit',year:'numeric',timeZone:'UTC'}).format(d);}
export const outputLanguage=(choice,appLanguage)=>languageCodes.includes(choice)?choice:languageInfo(appLanguage).code;
