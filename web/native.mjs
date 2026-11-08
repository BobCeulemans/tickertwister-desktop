// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
const requests=new Map();let counter=Math.floor(Math.random()*1_000_000_000);
window.__tickertwisterReply=(id,ok,encoded)=>{
 const item=requests.get(id);if(!item)return;requests.delete(id);clearTimeout(item.timer);
 try{const bytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));const value=JSON.parse(new TextDecoder().decode(bytes));ok?item.resolve(value):item.reject(new Error(value.error||'NATIVE_ERROR'));}catch(e){item.reject(e);}
};
export function nativeCall(action,payload){
 return new Promise((resolve,reject)=>{
  const id=++counter;const timer=setTimeout(()=>{requests.delete(id);reject(new Error('TIMEOUT'));},action==='analyse'?165000:action==='fetch'?35000:600000);
  requests.set(id,{resolve,reject,timer});
  const handler=window.webkit?.messageHandlers?.desktop;
  if(!handler){clearTimeout(timer);requests.delete(id);reject(new Error('NATIVE_UNAVAILABLE'));return;}
  handler.postMessage({id,action,...payload});
 });
}
