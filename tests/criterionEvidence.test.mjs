import test from 'node:test';import assert from 'node:assert/strict';import {evidenceLines} from '../web/criterionEvidence.mjs';
test('structured history replaces only dated number lines and keeps original pass/fail and exceptions',()=>{const text='⛔ Not consistently decreasing\n\t↳ 2023-06-30-2026-06-30: 83.86 days, 82.92 days\n↳ although: first > last';const result=evidenceLines(text,true);assert.equal(result.length,2);assert.equal(result[0].status,'fail');assert.equal(result[1].text,'although: first > last');assert.equal(evidenceLines(text,false).length,3);});
test('multiple subrules keep their own outcome rather than infer it from overall points',()=>{const r=evidenceLines('✅ Threshold met\n⛔ Trend failed');assert.deepEqual(r.map(x=>x.status),['pass','fail']);});

import {criterionDescription,criterionFindings,scoreRules} from '../web/criterionEvidence.mjs';
import {translator,languageCodes,catalogs} from '../web/i18n.mjs';
import METHODS from '../web/original-methods.mjs';
test('all 39 methods have readable formulas and explanations in each interface language',()=>{
 assert.deepEqual(Object.keys(scoreRules),METHODS);
 for(const language of languageCodes){
  const t=translator(language), financial=translator(language,true);
  for(const [key,rule] of Object.entries(scoreRules)){
   assert.ok(criterionDescription({key},t).trim());
   if(rule.guide)assert.ok(catalogs[language][rule.guide],rule.guide);
   for(const [,term] of rule.expression.matchAll(/\{([^}]+)\}/g)){
    assert.ok(catalogs[language][term],language+': '+term);
    assert.ok(criterionDescription({key},financial).includes(translator('en').term(term)));
   }
  }
 }
});
test('partial result preserves threshold, latest observation and localized trend',()=>{
 const nl=translator('nl');
 const c={key:'totalLiabilityToEquityHistory',weight:3,points:1.5,available:true,threshold:'TL/E > 80%'};
 const text=criterionFindings(c,{pairs:[['2024-12-31',90],['2025-12-31',78]]},nl,v=>String(v)).join(' ');
 assert.match(text,/Voldoet · 1 \/ 2/);
 assert.match(text,/2025 · Voldoet\./);
 assert.match(text,/een deel van de punten/);
 assert.equal(criterionFindings({...c,available:false},null,nl,String).length,1);
 const fcfe={...c,key:'freeCashFlowToEquity',points:5,weight:6};
 assert.match(criterionFindings(fcfe,{pairs:[['2023',12],['2024',110],['2025',50]]},nl,String).join(' '),/elke beoordeelde periode positief/);
});
