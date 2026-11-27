// SPDX-License-Identifier: AGPL-3.0-only
import {useEffect,useState} from 'react';
import {nativeCall} from './native.mjs';
import './company-tools.css';

export function CompanyDescription({report,t}){
 return <Description key={JSON.stringify([report.symbol,report.summary,t.language])} report={report} t={t}/>;
}

function Description({report,t}){
 const [open,setOpen]=useState(false),[original,setOriginal]=useState(false),[attempt,setAttempt]=useState(0);
 const [result,setResult]=useState(null);
 const text=report.summary||'',language=t.language,identity=JSON.stringify([text,language]);
 const current=result?.identity===identity?result:null;
 useEffect(()=>{
  if(!open||!text||language==='en'||original)return;
  let active=true;
  nativeCall('translate-company',{text,language,download:attempt>0})
   .then(value=>{if(active)setResult({...value,identity});})
   .catch(()=>{if(active)setResult({status:'unavailable',identity});});
  return()=>{active=false;};
 },[open,text,language,attempt,identity,original]);
 const translated=current?.status==='translated'&&!original;
 return <details className="company-profile" onToggle={e=>setOpen(e.currentTarget.open)}><summary>{t('About the company')}</summary>
  <p lang={translated?language:text?'en':language}>{translated?current.text:text||t('No business description is available for this analysis.')}</p>
  {text&&<div className="description-source"><small>{t(translated?'Yahoo Finance · translated on this Mac':'Business description as provided by Yahoo Finance.')}</small>
   {current?.status==='translated'&&<button onClick={()=>setOriginal(!original)}>{t(original?'Show translation':'Show original')}</button>}
   {current?.status==='download'&&<button onClick={()=>setAttempt(a=>a+1)}>{t('Download language and translate')}</button>}
   {['unavailable','unsupported'].includes(current?.status)&&<small>{t('Local translation unavailable.')}</small>}
  </div>}
 </details>;
}

const periods=[['1d','1D'],['5d','1W'],['1mo','1M'],['3mo','3M'],['6mo','6M'],['ytd','YTD'],['1y','1Y'],['2y','2Y'],['5y','5Y'],['10y','10Y'],['max','All']];
function PricePlot({series,language,period,t}){
 const points=series.points,prices=points.map(p=>p[1]);
 const first=points[0],last=points[points.length-1],low=Math.min(...prices),high=Math.max(...prices);
 const number=new Intl.NumberFormat(language,{maximumFractionDigits:Math.abs(last[1])<2?4:2});
 const date=new Intl.DateTimeFormat(language,{dateStyle:'medium',...(['1d','5d'].includes(period)?{timeStyle:'short'}:{}),timeZone:series.zone||'UTC'});
 const stamp=p=>date.format(new Date(p[0]*1000)),amount=v=>number.format(v)+' '+series.currency;
 const x=p=>10+655*(p[0]-first[0])/(last[0]-first[0]||1);
 const y=p=>high===low?80:145-130*(p[1]-low)/(high-low);
 const change=first[1]>0?(last[1]-first[1])/first[1]:null;
 return <div className="price-plot"><div className="price-values"><strong>{amount(last[1])}</strong>{change!==null&&<span>{t('Price change')} {new Intl.NumberFormat(language,{style:'percent',maximumFractionDigits:2,signDisplay:'exceptZero'}).format(change)}</span>}</div>
  <svg viewBox="0 0 680 158" role="img" aria-label={t('Price history')+' · '+stamp(first)+' – '+stamp(last)}><title>{amount(low)+' – '+amount(high)}</title>
   {[15,80,145].map(h=><line key={h} x1="10" x2="665" y1={h} y2={h} stroke="currentColor" opacity=".15"/>)}
   <polyline points={points.map(p=>x(p).toFixed(1)+','+y(p).toFixed(1)).join(' ')} fill="none" stroke="var(--green)" strokeWidth="2.5" strokeLinejoin="round"/>
   <circle cx={x(last)} cy={y(last)} r="3.5" fill="var(--green)"/>
  </svg><div className="price-axis"><time>{stamp(first)}</time><time>{stamp(last)}</time></div>
  <small>{t('Period low / high')} · {amount(low)} / {amount(high)}</small></div>;
}

export function PriceHistory({report,t}){
 const [open,setOpen]=useState(false),[period,setPeriod]=useState('1mo'),[retry,setRetry]=useState(0);
 const [result,setResult]=useState(null),[stockError,setStockError]=useState(false);
 const identity=JSON.stringify([report.symbol,period,retry]),current=result?.identity===identity?result:null;
 useEffect(()=>{
  if(!open)return;
  let active=true;
  nativeCall('price-history',{symbol:report.symbol,period}).then(series=>{
   if(active)setResult({identity,series:series?.points?.length?series:null});
  }).catch(()=>{if(active)setResult({identity,series:null});});
  return()=>{active=false;};
 },[open,report.symbol,period,retry,identity]);
 return <details id="price-history" className="company-profile price-history" onToggle={e=>setOpen(e.currentTarget.open)}><summary>{t('Price history')}</summary>
  <div className="price-actions"><div role="group" aria-label={t('Price history')}>{periods.map(([value,label])=><button key={value} aria-pressed={period===value} onClick={()=>setPeriod(value)}>{t(label)}</button>)}</div>
   <button onClick={()=>{setStockError(false);nativeCall('open-stocks',{symbol:report.symbol}).catch(()=>setStockError(true));}}>{t('Open in Apple Stocks')} ↗</button></div>
  {stockError&&<small role="status">{t('Stocks could not open this symbol.')}</small>}
  {current?.series?<PricePlot series={current.series} period={period} language={t.language} t={t}/>:current?<p role="status">{t('Price history unavailable.')} <button onClick={()=>setRetry(i=>i+1)}>{t('Retry')}</button></p>:<small role="status">{t('Loading prices…')}</small>}
  <small>{t('Yahoo Finance · prices retrieved when opened, excluding dividends.')}</small>
 </details>;
}
