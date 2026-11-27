// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
export function businessExcerpt(text,max=620){
 if(typeof text!=='string'||!text.trim())return '';
 if(text.length<=max)return text;
 const part=text.slice(0,max),sentence=part.lastIndexOf('. ');
 return sentence>max/2?part.slice(0,sentence+1):part.slice(0,part.lastIndexOf(' '))+'…';
}
