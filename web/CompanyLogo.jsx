// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import {useEffect,useState} from 'react';
import {nativeCall} from './native.mjs';
const cache=new Map();
export default function CompanyLogo({report,t}){
 const [image,setImage]=useState(null);
 useEffect(()=>{let active=true;setImage(null);if(report.website){if(!cache.has(report.website))cache.set(report.website,nativeCall('company-logo',{website:report.website}).catch(()=>null));cache.get(report.website).then(v=>{if(active)setImage(v);});}return ()=>{active=false;};},[report.website]);
 return <span className="company-logo" title={image?t("Company icon from ")+image.source:t("Company icon unavailable; ticker shown instead")}>{image?<img src={image.image} alt={report.name+' '+t("company icon")}/>:<span>{report.symbol.split('.')[0].slice(0,4)}</span>}</span>;
}
