// SPDX-License-Identifier: AGPL-3.0-only
import {useEffect,useRef,useState} from 'react';
import {nativeCall} from './native.mjs';
import {loadAnalysis} from './data.mjs';
import {collectTickerList,parseTickerList,isYahooTicker} from './tickerBatch.mjs';

export function useTickerBatch(onLoaded) {
 const [batch,setBatch]=useState(null);
 const controller=useRef(null),handler=useRef(onLoaded);
 handler.current=onLoaded;
 useEffect(()=>()=>{controller.current?.abort();controller.current=null;},[]);
 async function start(symbols){
  if(!symbols.length||controller.current)return;
  const session=new AbortController();
  controller.current=session;
  const latest=()=>controller.current===session;
  setBatch({running:true,stopping:false,current:'',total:symbols.length,completed:0,failures:[]});
  try{
   await collectTickerList(symbols,{
    load:loadAnalysis,signal:session.signal,
    onStart:symbol=>{if(latest())setBatch(b=>({...b,current:symbol}));},
    onResult:(symbol,report)=>{
     if(!latest())return;
     handler.current(report);
     setBatch(b=>({...b,completed:b.completed+1}));
    },
    onFailure:(symbol,reason)=>{
     if(latest())setBatch(b=>({...b,completed:b.completed+1,failures:[...b.failures,{symbol,reason}]}));
    },
   });
  }finally{
   if(latest()){
    controller.current=null;
    setBatch(b=>({...b,running:false,current:''}));
   }
  }
 }
 function stop(){
  controller.current?.abort();
  setBatch(b=>b&&({...b,stopping:true}));
 }
 return {batch,start,stop,dismiss:()=>{if(!controller.current)setBatch(null);}};
}

export function TickerBatchForm({t,onStart,running}){
 const [text,setText]=useState(''),[fileError,setFileError]=useState(''),[reading,setReading]=useState(false);
 async function importText(){
  setReading(true);setFileError('');
  try{
   const file=await nativeCall('open-ticker-list',{});
   if(!file.cancelled && typeof file.text==='string')setText(file.text);
  }catch{setFileError('Choose a UTF-8 text file of up to 128 KB.');}
  finally{setReading(false);}
 }
 return <details className="ticker-batch-form"><summary>{t('Analyse a ticker list')}</summary>
  <form onSubmit={event=>{event.preventDefault();onStart(parseTickerList(text));}}>
   <label>{t('Tickers separated by spaces, commas or new lines')}<textarea value={text} onChange={event=>setText(event.target.value)} placeholder="AAPL, LOTB.BR, VEEV" spellCheck="false" rows={3} maxLength={131072}/></label>
   <div className="batch-buttons"><button type="button" disabled={reading} onClick={importText}>{t('Import .txt…')}</button>
   <button className="primary" disabled={reading||running||!text.trim()}>{t('Analyse list')}</button></div>
   {fileError&&<p className="error" role="alert">{t(fileError)}</p>}
  </form></details>;
}

export function TickerBatchStatus({queue,t,errors}){
 const {batch,start,stop,dismiss}=queue;
 if(!batch)return null;
 const retry=batch.failures.filter(f=>isYahooTicker(f.symbol));
 return <section className="ticker-batch-status" aria-label={t('Ticker list')}>
  <div className="batch-progress"><span role="status">{t('Ticker list')} · {batch.completed} / {batch.total}
   {batch.current&&' · '+batch.current}{batch.stopping&&' · '+t(batch.running?'Stopping after this ticker':'Stopped')}</span>
   {batch.running?<button type="button" disabled={batch.stopping} onClick={stop}>{t('Stop after this ticker')}</button>:
   <button type="button" onClick={dismiss} aria-label={t('Close')} title={t('Close')}>×</button>}</div>
  {!!batch.failures.length&&<details><summary>{t('Failed tickers')} · {batch.failures.length}</summary>
   <ul>{batch.failures.map(({symbol,reason})=><li key={symbol}><b>{symbol}</b> · {errors[reason]||errors.DATA_UNAVAILABLE}</li>)}</ul>
   {!batch.running&&retry.length>0&&<button type="button" onClick={()=>start(retry.map(f=>f.symbol))}>{t('Retry failed tickers')}</button>}</details>}
 </section>;
}
