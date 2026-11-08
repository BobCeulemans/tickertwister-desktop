// SPDX-License-Identifier: AGPL-3.0-only
// Presentation only: do not recompute points or infer pass/fail for individual years.
export function evidenceLines(text,hasHistory=false){return String(text||'').split('\n').map(s=>s.trim()).filter(Boolean).filter(s=>!(hasHistory&&/^[↳↪→]?\s*\d{4}-\d{2}-\d{2}.*:/.test(s))).map(s=>({status:/^[✅✓]/u.test(s)?'pass':/^[⛔🚫❌]/u.test(s)?'fail':null,text:s.replace(/^[✅✓⛔🚫❌↳↪→]\s*/u,'').trim()}));}
