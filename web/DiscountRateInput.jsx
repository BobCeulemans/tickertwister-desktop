// SPDX-License-Identifier: AGPL-3.0-only
import {useState} from 'react';

// Keep the unrounded model rate until the user actually changes this field.
export default function DiscountRateInput({value, onChange, ...props}){
 const [draft,setDraft]=useState(null);
 const numeric=Number(value);
 const shown=value!==''&&Number.isFinite(numeric)&&draft!==value ? Number(numeric.toFixed(2)) : value;
 return <input {...props} value={shown} onChange={event=>{
  setDraft(event.target.value);
  onChange(event);
 }} onBlur={()=>setDraft(null)}/>;
}
