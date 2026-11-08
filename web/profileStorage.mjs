// SPDX-License-Identifier: AGPL-3.0-only
// Preferences only: passwords and API keys never enter browser storage.
export const profileStorage={
 getItem(key){return window.localStorage.getItem(window.__ttProfile?.id?'tt-profile:'+window.__ttProfile.id+':'+key:key);},
 setItem(key,value){window.localStorage.setItem(window.__ttProfile?.id?'tt-profile:'+window.__ttProfile.id+':'+key:key,value);}
};
