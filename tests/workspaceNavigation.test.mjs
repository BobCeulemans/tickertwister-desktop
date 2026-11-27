import test from 'node:test';
import assert from 'node:assert/strict';
import {initialPreferences,savePreference,themeLabels,openProfilePreferences,rememberLoginChoice} from '../web/workspacePreferences.mjs';
import {initialHistory,visit,move,forgetAnalysis} from '../web/workspaceNavigation.mjs';

test('macOS locale, saved global choices, existing user palettes and unsupported languages',()=>{
 const values=new Map();
 const storage={getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)};
 assert.equal(initialPreferences(storage,'nl_BE').language,'nl');
 assert.equal(initialPreferences(storage,'nl_BE',null,'light').appearance,'light');
 assert.equal(initialPreferences(storage,'nl_BE').appearance,'system');
 assert.equal(initialPreferences(storage,'sv-SE').language,'en');
 values.set('tt-profile:alice:tt-language','de');
 for(const [id,color] of [['professional','Green'],['modern','Blue'],['library','Brown'],['futuristic','Purple']]){
  values.set('tt-profile:alice:tt-theme',id);
  const prior=initialPreferences(storage,'fr-FR','alice');
  assert.equal(prior.language,'de');assert.equal(themeLabels[prior.theme],color);
 }
 savePreference(storage,'theme','modern');savePreference(storage,'language','it');savePreference(storage,'appearance','light');
 assert.deepEqual(initialPreferences(storage,'es-ES','alice'),{theme:'futuristic',language:'de',appearance:'light'});
 assert.deepEqual(initialPreferences(storage,'es-ES'),{theme:'modern',language:'it',appearance:'light'});
 assert.equal(savePreference(storage,'language','arbitrary'),false);
});
test('profile settings survive switching and reload, sign-in choices affect only the next signed-in account',()=>{
 const area=()=>{const values=new Map();return {getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};};
 const storage=area(),session=area();
 savePreference(storage,'language','nl');savePreference(storage,'theme','professional');
 const open=id=>openProfilePreferences(storage,session,'en-US',id);
 open('alice');open('bob');
 savePreference(storage,'language','fr','alice');savePreference(storage,'theme','futuristic','alice');
 savePreference(storage,'language','de','bob');savePreference(storage,'theme','library','bob');
 assert.deepEqual(open('alice'),{language:'fr',theme:'futuristic',appearance:'system'});
 assert.deepEqual(open('bob'),{language:'de',theme:'library',appearance:'system'});
 assert.equal(initialPreferences(storage,'en-US').language,'nl');
 savePreference(storage,'language','es');rememberLoginChoice(session,'language','es');
 // The native sign-in reloads the page and retains only session storage and local storage.
 assert.equal(initialPreferences(storage,'en-US').language,'es');
 assert.deepEqual(open('alice'),{language:'es',theme:'futuristic',appearance:'system'});
 assert.deepEqual(open('bob'),{language:'de',theme:'library',appearance:'system'});
 assert.equal(open('new').language,'es');
});
test('analysis, sections and dossier preserve positions in both directions and new routes discard forward history',()=>{
 const a={view:'analysis',ticker:'LOTB.BR'},section={...a,anchor:'valuation'},b={view:'analysis',ticker:'B'};
 const pos={scroll:120,open:[1,3]};
 let h=visit(initialHistory(),a,{scroll:32,open:[]});
 h=visit(h,section,pos);h=visit(h,b,{scroll:400,open:[1]});
 h=move(h,-1,{scroll:5,open:[]});assert.equal(h.entries[h.index].anchor,'valuation');
 h=move(h,-1,{});assert.deepEqual(h.entries[h.index].position,pos);
 h=move(h,1,{});h=move(h,1,{});assert.equal(h.entries[h.index].ticker,'B');
 assert.equal(move(h,1,{}),h);h=move(h,-1,{});h=visit(h,{view:'archive'},{});
 assert.equal(h.entries.some(entry=>entry.ticker==='B'),false);
 assert.equal(visit(h,{view:'archive'},{}),h);
 h=forgetAnalysis(h,'LOTB.BR');assert.deepEqual(h.entries.map(item=>item.view),['overview','archive']);assert.equal(h.index,1);
});
