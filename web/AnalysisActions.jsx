// SPDX-License-Identifier: AGPL-3.0-only
import {useRef,useState} from 'react';
import {MacIcon} from './MacShell.jsx';
export default function AnalysisActions({t,notes,onNotes,onPin}) {
 const [saving,setSaving]=useState(false),[message,setMessage]=useState('');
 const inFlight=useRef(false);
 async function pin(){
  if(inFlight.current)return;
  inFlight.current=true;setSaving(true);setMessage('');
  try{await onPin();setMessage('Saved to research dossier');}
  catch(error){
   const messages={DOSSIER_FULL:'The research dossier already has 30 companies.',DOSSIER_NOT_READY:'The dossier is unavailable or busy. Try again.',DOSSIER_DIRTY:'Save or undo the pending removal in the dossier first.'};
   setMessage(messages[error.message]||'The file could not be saved.');
  }finally{inFlight.current=false;setSaving(false);}
 }
 return <div className="analysis-notes-actions">
  <div className="pin-action"><button className="primary" data-action="desk-pin" onClick={pin} disabled={saving}><MacIcon name="save"/>{t(saving?'Saving…':'Save to research dossier')}</button>{message&&<span role="status">{t(message)}</span>}</div>
  <details className="analysis-notes"><summary>{window.__ttNoteSymbol ? <span aria-hidden="true" className="native-note-icon" style={{maskImage:'url('+window.__ttNoteSymbol+')'}}/> : <MacIcon name="note"/>}<span>{t('Quick notes')}</span>{notes&&<i aria-label={t('Contains notes')} title={t('Contains notes')}>•</i>}</summary>
  <label><span>{t('Notes for this analysis')}</span><textarea rows={4} maxLength={12000} value={notes} onChange={e=>{onNotes(e.target.value);setMessage('');}}/></label>
  <p>{t('Save the analysis or add it to your dossier to keep these notes.')}</p>
  </details>
 </div>;
}
