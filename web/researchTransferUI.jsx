// SPDX-License-Identifier: AGPL-3.0-only
import {useState} from 'react';
import {nativeCall} from './native.mjs';
import {loadArchive,useAIArchive} from './aiArchive.mjs';
import {makeTransfer,parseTransfer,planImport,sameDossier} from './dossierTransfer.mjs';
import {emptyDesk,parseDesk} from './research.mjs';

export const transferErrors={
 INVALID_TRANSFER:'This dossier file could not be read.',
 TRANSFER_DECRYPT:'Check the transfer password and the file.',
 TRANSFER_PASSWORD:'Use two matching passwords of at least 12 characters.',
 TRANSFER_SIZE:'This dossier exceeds the storage limit.',
 TRANSFER_CONFLICT:'An AI record with the same ID has different content. Import stopped.',
 DOSSIER_CHANGED:'The local dossier changed. Reopen it before importing.',
 DOSSIER_FULL:'Maximum 30 companies. Remove a dossier first.',
 ARCHIVE_UNAVAILABLE:'The complete AI archive could not be read. Check the archive before exporting.',
};

export default function ResearchTransfer({desk,committed,selected,full,dirty,busy,setBusy,onImported,t}){
 const archive=useAIArchive();
 const [pending,setPending]=useState(null),[replace,setReplace]=useState(false),[message,setMessage]=useState('');
 function fail(e){setMessage(transferErrors[e.message]||'The transfer could not be completed. Check the file and try again.');}
 async function exportFile(){
  setBusy(true);setMessage('');
  try{
   const latest=await loadArchive();
   if(!latest.loaded||latest.error==='ARCHIVE_PARTIAL'||latest.error==='ARCHIVE_READ_FAILED')throw Error('ARCHIVE_UNAVAILABLE');
   const file=makeTransfer(desk,latest.records,selected,full);
   const result=await nativeCall('research-export',{content:JSON.stringify(file)});
   if(result.saved)setMessage('Encrypted dossier exported.');
  }catch(e){fail(e);}finally{setBusy(false);}
 }
 async function openFile(){
  setBusy(true);setMessage('');setPending(null);setReplace(false);
  try{
   const info=await nativeCall('research-import-open',{});
   if(info.cancelled)return;
   const disk=await nativeCall('research-load',{});
   if(!sameDossier(disk.content?parseDesk(disk.content):emptyDesk(),committed))throw Error('DOSSIER_CHANGED');
   const file=parseTransfer(info.content);
   const plan=planImport(desk,file);
   setPending({file,revision:info.revision,matching:plan.matching,added:plan.added});
  }catch(e){fail(e);}finally{setBusy(false);}
 }
 async function apply(){
  setBusy(true);setMessage('');
  try{
   const plan=planImport(desk,pending.file,replace);
   await nativeCall('research-import-apply',{revision:pending.revision,content:JSON.stringify({dossier:plan.desk,archive:pending.file.archive})});
   onImported(plan.desk);setPending(null);setReplace(false);setMessage('Dossier imported.');
   await loadArchive();
  }catch(e){fail(e);}finally{setBusy(false);}
 }
 return <div className="desk-transfer"><div className="desk-transfer-buttons">
  <button onClick={exportFile} disabled={busy||!!pending||(!selected.length&&!(full&&archive.records.length))}>{t('Export dossier')}{selected.length?' · '+selected.length:''}</button>
  <button onClick={openFile} disabled={busy||dirty||!!pending}>{t('Import dossier')}</button>
 </div>{dirty&&<small>{t('Save your dossier changes before importing.')}</small>}
 {pending&&<section className="desk-import-review"><strong>{t('Import dossier')}</strong><p>{t('New companies')} · {pending.added}　{t('Saved AI analyses')} · {pending.file.archive.length}</p>
 {pending.matching.length>0&&<><p>{t('Existing companies')} · {pending.matching.join(', ')}</p>
 <label><input type="checkbox" checked={replace} onChange={e=>setReplace(e.target.checked)}/>{t('Replace matching companies and their notes with the imported copies')}</label></>}
 <button disabled={busy||dirty} className="primary" onClick={apply}>{t('Confirm import')}</button> <button disabled={busy} onClick={()=>{setPending(null);setMessage('');}}>{t('Cancel')}</button>
 </section>}{message&&<p role="status">{t(message)}</p>}</div>;
}
