// SPDX-License-Identifier: AGPL-3.0-only
// Classification follows the business activity saved with each Yahoo snapshot.
export function reportedSectorModel(report) {
  const industry = String(report?.industry || '').trim().toLowerCase();
  const sector = String(report?.sector || '').trim().toLowerCase();
  if (/\bbanks?\b|\bbanking\b|\bthrifts?\b/.test(industry) || /^(banks?|banking)$/.test(sector)) return 'bank';
  const insurance = /insuranc|reinsur|insurer/.test(industry) || /insurance/.test(sector);
  if (insurance && !/broker|agenc/.test(industry)) return 'insurance';
  if (insurance || /^(financials?|financial services)$/.test(sector) || /credit services|payment (processing|processors?|services)|transaction (processing|services)/.test(industry)) return 'financial';
  return 'other';
}

export function sectorModel(report) {
  // American Express is a US bank holding company with deposit-funded lending.
  // Yahoo groups it with payment networks under Credit Services (2025 Form 10-K,
  // SEC CIK 4962). Confirm issuer identity when a snapshot has no SEC identifier.
  if (Number(report?.cik) === 4962 || (report?.symbol === 'AXP' &&
      /^American Express(?: Company| Co\.?)?$/i.test(report.name || ''))) return 'bank';
  return reportedSectorModel(report);
}

export function directEquityModel(report) {
  const sector = sectorModel(report);
  return sector === 'bank' || sector === 'insurance';
}
