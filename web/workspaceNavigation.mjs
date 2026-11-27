// SPDX-License-Identifier: AGPL-3.0-only
export const initialHistory=()=>({entries:[{view:'overview'}],index:0});
const sameRoute=(a,b)=>a.view===b.view&&a.ticker===b.ticker&&a.anchor===b.anchor;

export function visit(history,route,position){
 if(sameRoute(history.entries[history.index],route))return history;
 const entries=history.entries.slice(0,history.index+1);
 entries[history.index]={...entries[history.index],position};
 entries.push(route);
 if(entries.length>100)entries.shift();
 return {entries,index:entries.length-1};
}
export function move(history,offset,position){
 const index=history.index+offset;
 if(index<0||index>=history.entries.length)return history;
 const entries=history.entries.slice();
 entries[history.index]={...entries[history.index],position};
 return {entries,index};
}
export function forgetAnalysis(history,ticker){
 const keep=entry=>entry.view!=='analysis'||entry.ticker!==ticker;
 const entries=history.entries.filter(keep);
 if(!entries.length)return initialHistory();
 const previous=history.entries.slice(0,history.index+1).filter(keep);
 return {entries,index:Math.max(0,previous.length-1)};
}
