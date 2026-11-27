// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import METHODS from './original-methods.mjs';

export function validWeights(weights){
 return weights!==null&&typeof weights==='object'&&!Array.isArray(weights)&&
  Object.entries(weights).every(([k,v])=>METHODS.includes(k)&&Number.isFinite(v)&&v>=0&&v<=100);
}

export function validOverrides(keys){
 return Array.isArray(keys)&&keys.length<=METHODS.length&&new Set(keys).size===keys.length&&keys.every(k=>METHODS.includes(k));
}

export function canOverride(c){
 return c.available===true&&c.weight>0&&Number.isFinite(c.points)&&c.points<c.weight;
}

export function personalScore(report,weights={},overrides=[]){
 if(!validWeights(weights)||!validOverrides(overrides))throw Error('INVALID_WEIGHTS');
 if(report.schema!=='yahoo39-v1')return {value:null,points:0,weight:0,custom:false,criteria:[]};
 const selected=new Set(overrides);
 const criteria=report.score.criteria.map(c=>{
  const multiplier=weights[c.key]??1;
  const effectiveWeight=c.available&&c.weight>0?c.weight*multiplier:0;
  const overridden=canOverride(c)&&selected.has(c.key);
  const personalPoints=effectiveWeight?(overridden?effectiveWeight:c.points*multiplier):0;
  return {...c,multiplier,effectiveWeight,overridden,personalPoints};
 });
 const points=criteria.reduce((s,c)=>s+c.personalPoints,0),weight=criteria.reduce((s,c)=>s+c.effectiveWeight,0);
 return {value:weight?100*points/weight:null,points,weight,criteria,custom:Object.values(weights).some(v=>v!==1)||criteria.some(c=>c.overridden)};
}
