import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {LANGUAGES,catalogs,translator,formatDate,outputLanguage} from '../web/i18n.mjs';
import {financialInput,apiRequest,translationRequest,outputSchema} from '../web/aic.mjs';
import {archiveKey,readRecord} from '../web/aiArchiveData.mjs';
import {shortAmount,marketValue} from '../web/presentation.mjs';
const company={symbol:'TEST',name:'Test',currency:'USD',quote:{price:100,currency:'USD',marketCap:1e9},valuationShares:1e7};
const period={key:'FY:2025-12-31',rows:[{end:'2025-12-31',income:10,equity:100,debt:14,assets:200,revenue:100}]};
test('seven complete catalogs and English fallback for unknown keys/languages',()=>{
 for(const {code} of LANGUAGES){for(const key of Object.keys(catalogs.en))assert.ok(typeof catalogs[code][key]==='string'&&catalogs[code][key],`${code}: ${key}`);assert.equal(translator(code)('Untranslated example'),'Untranslated example');}
 assert.equal(translator('unknown')('New analysis'),'New analysis');
});
test('static UI keys exist in the English source catalog',()=>{for(const f of fs.readdirSync('web').filter(f=>/\.(jsx|mjs)$/.test(f))){for(const m of fs.readFileSync('web/'+f,'utf8').matchAll(/\bt\(\s*("(?:[^"\\]|\\.)*")\s*\)/g))assert.ok(JSON.parse(m[1]) in catalogs.en,`${f}: ${m[1]}`);}});
test('locale formatting changes presentation only, never USD or financial values',()=>{
 const before=JSON.stringify(company);const strings=new Set();
 for(const {code,locale} of LANGUAGES){const t=translator(code),n=v=>new Intl.NumberFormat(locale,{minimumFractionDigits:2,maximumFractionDigits:2}).format(v);strings.add(n(1234.56));assert.ok(shortAmount(1e9,n,t));assert.equal(marketValue(company),1e9);assert.equal(company.currency,'USD');assert.equal(JSON.stringify(company),before);}
 assert.ok(strings.size>=4);assert.equal(formatDate('2025-12-31','en'),'12/31/2025');assert.equal(formatDate('2025-12-31','de'),'31.12.2025');assert.equal(formatDate('2025-12-31','nl'),'31/12/2025');
});
test('English financial term preference retains abbreviations while controls remain localized',()=>{
 for(const {code} of LANGUAGES){const t=translator(code,true);assert.equal(t.term('Return on Equity (ROE)'),'Return on Equity (ROE)');assert.equal(t('New analysis'),catalogs[code]['New analysis']);}
});
test('AI language follows app unless independently selected; financial input and archive identity stay identical',()=>{
 let first;for(const {code,english} of LANGUAGES){assert.equal(outputLanguage('auto',code),code);assert.equal(outputLanguage('fr',code),'fr');const d=financialInput([company],period,code),q=apiRequest(d);assert.equal(d.language,code);assert.ok(q.instructions.includes(english));assert.equal(d.companies[0].currency,'USD');assert.equal(d.companies[0].metrics.debtEquity,.14);first??=archiveKey(d);assert.equal(archiveKey(d),first);
 const sections=Object.fromEntries(Object.keys(outputSchema.properties).map(k=>[k,'Fixture text']));const raw={id:'test-'+code,input:d,language:code,createdAt:'2026-11-07T12:00:00Z',response:{status:'completed',output:[{content:[{type:'output_text',text:JSON.stringify(sections)}]}]}};
 const record=readRecord(raw);assert.equal(record.language,code);assert.deepEqual(record.result.sections,sections);assert.ok(translationRequest(record,code).instructions.includes(english));}
});
