// SPDX-License-Identifier: AGPL-3.0-only
import {periods} from './comparison.mjs';
import {finite} from './finance.mjs';

// Older snapshots keep the raw quarterly comparison rows. Use the same four-quarter
// aggregation as the research desk, ending on the selected balance sheet date.
export function waccAccounts(report) {
  const raw = report.waccAccounts;
  if (raw?.balanceDate) {
    const matched = raw.flowDate === raw.balanceDate && ['TTM','FY=TTM'].includes(raw.flowBasis);
    return {debt:finite(raw.debt) && raw.debt >= 0 ? raw.debt : null, balanceDate:raw.balanceDate,
      flows:matched ? raw : {}, flowBasis:matched ? raw.flowBasis : null};
  }
  const candidates = [...(report.quarters || []), ...(report.years || [])].map(row => ({
    end:row.end, debt:finite(row.debt) ? row.debt :
      finite(row.longDebtAndLeases) && finite(row.currentDebtAndLeases) ? row.longDebtAndLeases + row.currentDebtAndLeases : null
  }));
  const data = report.valuationData;
  if (data?.balanceDate) candidates.push({end:data.balanceDate, debt:data.grossDebt});
  const balance = candidates.filter(row=>row.end && finite(row.debt) && row.debt >= 0)
    .sort((a,b)=>b.end.localeCompare(a.end))[0];
  if (!balance) return {debt:null, balanceDate:null, flows:{}, flowBasis:null};
  const balanceDate = balance.end;
  const usable = (report.quarters || []).filter(row=>/^\d{4}-Q[1-4]$/.test(row.periodKey));
  const quarter = usable.find(row=>row.end===balanceDate);
  const ttm = quarter && periods({quarters:usable}).get('TTM:'+quarter.periodKey);
  const annual = (report.years || []).find(row=>row.end===balanceDate);
  // The annual statement at the same year end is itself a trailing twelve-month period.
  const flows = {};
  for (const key of ['interest','tax','pretax']) flows[key] = ttm?.[key] ?? annual?.[key] ?? null;
  return {debt:balance.debt, balanceDate, flows, flowBasis:ttm ? 'TTM' : annual ? 'FY=TTM' : null};
}
