// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import METHODS from './original-methods.mjs';
export function validWeights(weights){return weights!==null&&typeof weights==='object'&&!Array.isArray(weights)&&Object.entries(weights).every(([k,v])=>METHODS.includes(k)&&typeof v==='number'&&Number.isFinite(v)&&v>=0&&v<=100);}
export function personalScore(report,weights={}){
 if(!validWeights(weights))throw Error('INVALID_WEIGHTS');
 if(report.schema!=='yahoo39-v1')return {value:null,points:0,weight:0,custom:false,criteria:[]};
 const criteria=report.score.criteria.map(c=>{const multiplier=weights[c.key]??1,weight=c.available&&c.weight>0?c.weight*multiplier:0;return {...c,multiplier,effectiveWeight:weight,personalPoints:weight?c.points/c.weight*weight:0};});
 const points=criteria.reduce((s,c)=>s+c.personalPoints,0),weight=criteria.reduce((s,c)=>s+c.effectiveWeight,0);
 return {value:weight?100*points/weight:null,points,weight,criteria,custom:Object.values(weights).some(v=>v!==1)};
}
