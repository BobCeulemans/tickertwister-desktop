// SPDX-License-Identifier: AGPL-3.0-only
import {finite, cagr} from './finance.mjs';
import {sectorModel, reportedSectorModel, directEquityModel} from './valuationSector.mjs';
import {marketValue} from './presentation.mjs';
import {waccAccounts} from './waccAccounts.mjs';
import {taxReference} from './statutoryTax.mjs';
import {comparablePrice, dividendInStatementCurrency, fxRate} from './currency.mjs';

const million = 1e6;
const projectionYears = 10;
export const currentEarningsMethod = 'sector-revenue-v2';
const text = value => finite(value) ? String(Number(value.toPrecision(12))) : '';
const percentInput = value => finite(value) ? String(Number(value.toFixed(4))) : '';
const numeric = value => (typeof value === 'number' || typeof value === 'string' && value.trim()) ? Number(value) : NaN;

export {riskFreeObservation, treasuryReference} from './riskFree.mjs';
import {riskFreeObservation} from './riskFree.mjs';

export function currentTreasury(report) {
  return riskFreeObservation(report,'cashFlow') !== null;
}

export function minimumDiscountRate(report) {
  return Math.max(6, riskFreeObservation(report,'cashFlow')?.yield ?? 0);
}

// Original Yahoo tables are also retained in earlier saved analyses. Match fiscal
// dates explicitly because the statements can have different column orders.
function savedStatementValue(table, name, end) {
  const column = table?.dates?.indexOf(end) ?? -1;
  if (column < 0) return null;
  const values = table.rows?.find(row => row[0] === name)?.[1];
  return finite(values?.[column]) ? values[column] : null;
}

export function historicalOwnerEarnings(report, sector=sectorModel(report)) {
  const equityProxy = sector === 'bank' || sector === 'insurance';
  const cashFlows = report.originalTables?.find(table => table.title === 'Kasstromen');
  const years = [...(report.years || [])].sort((a,b) => a.end.localeCompare(b.end));
  return years.map(year => {
    const {income: netIncome} = year;
    const depreciation = finite(year.da) ? year.da : null;
    const capex = finite(year.capex) ? Math.abs(year.capex) : null;
    const workingCapitalCashEffect = year.workingCapitalCashEffect ??
      savedStatementValue(cashFlows, 'ChangeInWorkingCapital', year.end);
    const maintenanceCapex = finite(capex) && finite(depreciation) && depreciation >= 0
      ? Math.min(capex, depreciation) : null;
    // Missing source cells stay missing. Zero assumptions apply only to components in this model.
    const assumedZero = [];
    const investment = sector === 'financial' ? capex : maintenanceCapex;
    if (!equityProxy && depreciation === null) assumedZero.push('Depreciation & amortisation');
    if (!equityProxy && investment === null) assumedZero.push(sector === 'financial' ? 'Capital expenditure' : 'Maintenance capex estimate');
    if (sector === 'other' && !finite(workingCapitalCashEffect)) assumedZero.push('Working capital cash effect');
    let ownerEarnings = null;
    if (finite(netIncome)) {
      if (equityProxy) ownerEarnings = netIncome;
      else if ((depreciation ?? 0) >= 0) ownerEarnings = netIncome + (depreciation ?? 0) - (investment ?? 0)
        + (sector === 'other' && finite(workingCapitalCashEffect) ? workingCapitalCashEffect : 0);
    }
    return {end: year.end, revenue:year.revenue, netIncome, depreciation, capex, maintenanceCapex, workingCapitalCashEffect, ownerEarnings, assumedZero};
  });
}

function growthHistory(rows, key) {
  const sample = rows.filter(row => finite(row[key]));
  const ends = sample.length > 1 ? [sample[0], sample.at(-1)] : [];
  return {growth:cagr(ends,key), period:ends.length ? ends.map(row=>row.end.slice(0,4)).join('–') : null, ends};
}

function earningsGrowthBand(rows, sector, revenuePolicy) {
  const earnings = growthHistory(rows, 'ownerEarnings');
  const income = growthHistory(rows, 'netIncome');
  const revenue = growthHistory(rows, 'revenue');
  // All inputs to the blend must cover the same fiscal endpoints.
  const useRevenue = revenuePolicy && sector !== 'other';
  const available = useRevenue ? [revenue, income, earnings] : [earnings, income, revenue];
  const anchor = available.find(series => finite(series.growth));
  const ends = anchor?.ends || [];
  const oe = cagr(ends, 'ownerEarnings'), ni = cagr(ends, 'netIncome'), sales = cagr(ends, 'revenue');
  const signals = [ni, sales].filter(finite);
  if (sector !== 'bank' && sector !== 'insurance' && finite(oe)) signals.push(oe);
  const diverges = !useRevenue && [oe,ni,sales].every(finite) && (oe < Math.min(ni,sales)-.10 || oe > Math.max(ni,sales)+.10);
  let suggested, method;
  if (useRevenue) {
    suggested = anchor?.growth ?? null;
    method = anchor === revenue ? 'Revenue growth before caps' :
      anchor === income ? 'Net income growth fallback' : 'Owner earnings growth fallback';
  } else {
    const mean = signals.length ? signals.reduce((a,b)=>a+b,0) / signals.length : null;
    suggested = diverges ? ni : mean;
    method = diverges ? 'Net income growth fallback' : 'Growth estimate before caps';
  }
  const limit = cap => finite(suggested) ? percentInput(Math.max(-20, Math.min(cap, suggested*100))) : '';
  return {historical:earnings.growth, period:earnings.period, incomeGrowth:income.growth, incomePeriod:income.period,
    revenueGrowth:revenue.growth, revenuePeriod:revenue.period, suggested, suggestedPeriod:anchor?.period||null,
    method, diverges, comparable:{oe, ni, sales}, strict:limit(10), moderate:limit(12)};
}

export function historicalGrowthBand(report) {
  const sector = sectorModel(report);
  return earningsGrowthBand(historicalOwnerEarnings(report,sector),sector,true);
}

function startingEarnings(rows) {
  const latest = rows.at(-1)?.ownerEarnings ?? null;
  const lastThree = rows.slice(-3);
  const consistent = lastThree.length === 3 && lastThree.every((row,index) => {
    if (!finite(row.ownerEarnings)) return false;
    if (!index) return true;
    const days = (Date.parse(row.end)-Date.parse(lastThree[index-1].end))/864e5;
    return days >= 330 && days <= 400;
  });
  const average = consistent ? lastThree.reduce((sum,row)=>sum+row.ownerEarnings,0)/3 : null;
  const normalized = finite(average) && Math.abs(latest-average) > .30*Math.abs(average);
  return {average, normalized, starting:normalized ? average : latest};
}

// Reconstruct the default offered when a dossier was saved so personal edits survive a model update.
export function previousEarningsDefaults(report, method) {
  const sector = method === 'sector-blend-v1' ? reportedSectorModel(report) : 'other';
  const rows = historicalOwnerEarnings(report,sector);
  if (method === 'sector-blend-v1') {
    const {starting} = startingEarnings(rows);
    return {growth:earningsGrowthBand(rows,sector,false).strict,
      ownerEarnings:text(finite(starting) ? starting/million : null)};
  }
  const last = rows.at(-1)?.ownerEarnings;
  const cagr = growthHistory(rows,'ownerEarnings').growth;
  return {ownerEarnings:text(finite(last) ? last/million : null),
    growth:finite(cagr) ? percentInput(Math.max(-20,Math.min(10,cagr*100))) : ''};
}

export function historicalOwnerEarningsGrowth(report) {
  return historicalGrowthBand(report).historical;
}

// Both prices use the same earnings, rate, perpetual growth, debt and shares as the active DCF.
export function valuationGrowthBand(report,inputs) {
  const band = historicalGrowthBand(report);
  if (band.suggested === null) return {...band, strictValue:null, moderateValue:null};
  const priceAt = growth => calculateValuation(report,{...inputs,growth}).perShare ?? null;
  const strictValue = priceAt(band.strict);
  return {...band, strictValue, moderateValue:band.strict===band.moderate ? strictValue : priceAt(band.moderate)};
}

export function valuationSources(report) {
  const rows = historicalOwnerEarnings(report);
  const latest = rows.at(-1) || {};
  const data = report.valuationData || {};
  const balances = [...(report.quarters || []), ...(report.years || [])].sort((a,b) => b.end.localeCompare(a.end));
  const balance = balances.find(row => finite(row.debt) && finite(row.cash));
  const stored = finite(data.netDebt);
  const netDebt = stored ? data.netDebt : balance ? balance.debt - balance.cash : null;
  const balanceDate = stored ? data.balanceDate : balance?.end;

  // Older normalized 'shares' can refer to ShareIssued including treasury
  // stock. Use reported outstanding shares or an identified ordinary count.
  let shares = report.valuationShares;
  // Legacy SEC dossiers use CommonStockSharesOutstanding for the annual count.
  if ((!finite(shares) || shares <= 0) && report.schema !== 'yahoo39-v1' && report.cik) {
    shares = balances.find(row => finite(row.shares) && row.shares > 0)?.shares;
  }
  if (!(finite(shares) && shares > 0)) {
    const table = report.originalTables?.find(item => item.title === 'Balans');
    for (const end of [...(table?.dates || [])].sort().reverse()) {
      shares = savedStatementValue(table, 'OrdinarySharesNumber', end);
      if (finite(shares) && shares > 0) break;
      const issued = savedStatementValue(table, 'ShareIssued', end);
      const treasury = savedStatementValue(table, 'TreasurySharesNumber', end);
      shares = finite(issued) && finite(treasury) && treasury >= 0 ? issued - treasury : null;
      if (finite(shares) && shares > 0) break;
    }
  }
  return {...data, ...latest, ...startingEarnings(rows), sector:sectorModel(report), ownerEarningsDate: latest.end, netDebt, balanceDate, shares};
}

// Yahoo supplies the quote and market capitalisation in market units. The model
// and the conversion used for its safety margin stay in statement currency.
export function valuationMarket(report) {
  const quote = report.quote;
  const currency = quote?.currency;
  if (!currency) return {currency:null, price:null, capitalisation:null};
  const price = finite(quote.price) && quote.price > 0 ? quote.price : null;
  // A subunit quote (e.g. GBp) does not establish the unit of Yahoo's market cap.
  const majorUnit = /^[A-Z]{3}$/.test(currency) && !['GBX', 'ZAC', 'ILA'].includes(currency);
  const capitalisation = majorUnit ? marketValue(report) : null;
  return {currency, price, capitalisation};
}


// Annualized historical revenue from the dated Yahoo statements, distinct from Yahoo's recent YoY growth.
export function revenueHistory(report) {
  const sample = [...(report.years || [])].filter(y=>finite(y.revenue)).sort((a,b)=>a.end.localeCompare(b.end));
  return {growth:cagr(sample,'revenue'), period:sample.length > 1 ? sample[0].end.slice(0,4)+'–'+sample.at(-1).end.slice(0,4) : null};
}

export function waccEstimate(report, betaInput = '', basis = 'quote') {
  const equityOnly = directEquityModel(report);
  const riskObservation = riskFreeObservation(report,basis);
  const riskFree = riskObservation ? riskObservation.yield / 100 : null;
  const personalBeta = betaInput !== '' && betaInput != null;
  const beta = personalBeta ? numeric(betaInput) : report.beta;
  const premium = .05;
  const equityCost = finite(beta) && riskFree !== null ? riskFree + beta * premium : null;
  const reference = {equityOnly, riskFree, riskObservation, beta:finite(beta)?beta:null, personalBeta, premium, equityCost,
    useYahoo:riskObservation?.sourceID==='tnx'};
  if (equityOnly) return {...reference, rate:equityCost};

  const market = valuationMarket(report);
  const {debt,balanceDate,flows,flowBasis} = waccAccounts(report);
  const fx = market.currency === report.currency ? 1 : fxRate(report);
  const equity = finite(market.capitalisation) && finite(fx) ? market.capitalisation * fx : null;
  const total = finite(equity) && equity > 0 && finite(debt) ? equity + debt : null;
  const equityWeight = debt === 0 ? 1 : total ? equity / total : null;
  const debtWeight = debt === 0 ? 0 : total ? debt / total : null;

  const taxAssumed = !(finite(flows.tax) && finite(flows.pretax) && flows.pretax > 0);
  const taxBenchmark = taxAssumed ? taxReference(report.country) : null;
  const rawTax = taxAssumed ? taxBenchmark.rate : flows.tax / flows.pretax;
  const tax = Math.max(0,Math.min(.35,rawTax));
  const interest = finite(flows.interest) ? Math.abs(flows.interest) : null;
  const debtCostAssumed = debt > 0 && interest === null;
  const rawDebtCost = debt > 0 && interest !== null ? interest / debt : null;
  let debtCost = null;
  if (debt === 0) debtCost = 0;
  else if (debt > 0 && riskFree !== null) {
    debtCost = Math.max(riskFree,Math.min(riskFree + .10,rawDebtCost ?? riskFree + .015));
  }
  // Debt costs are inferred from reporting-currency financials. Spot FX can
  // align capital weights, but it cannot convert a borrowing rate into a foreign currency.
  const sameRateCurrency = basis === 'cashFlow' || !market.currency || market.currency === report.currency;
  const rate = debt === 0 ? equityCost : sameRateCurrency && [equityWeight,debtWeight,equityCost,debtCost].every(finite)
    ? equityWeight * equityCost + debtWeight * debtCost * (1-tax) : null;
  return {...reference, rate:finite(rate)?rate:null, equity, debt, total, equityWeight, debtWeight,
    interest,debtCost,rawDebtCost,debtCostAssumed,tax,rawTax,taxAssumed,taxBenchmark,country:report.country,
    incomeTax:flows.tax,pretax:flows.pretax,flowBasis,fiscalDate:flowBasis?balanceDate:null,balanceDate};
}

// A bank or insurer's DCF is an equity model. Its discount rate follows the
// reporting-currency CAPM unless the user enters a personal cost of equity.
export function equityDiscountInput(report,beta) {
  const rate = waccEstimate(report,beta,'cashFlow').equityCost;
  return finite(rate) ? text(rate * 100) : '';
}

// Preserve the ordinary DCF floor when a capital-cost estimate is unavailable
// or below the floor. The discount benchmark must match the projected currency.
export function financialDiscountInput(report,beta='') {
  const estimate = waccEstimate(report,beta,'cashFlow').rate;
  const minimum = minimumDiscountRate(report);
  return finite(estimate) && estimate > 0 && estimate <= 1 ? String(Math.max(minimum,estimate*100)) : String(minimum);
}

export function defaultValuation(report) {
  const data = valuationSources(report);
  const years = [...(report.years || [])].sort((a,b) => a.end.localeCompare(b.end));
  const growth = historicalGrowthBand(report).strict;
  const equityOnly = directEquityModel(report);
  const rate = equityOnly ? equityDiscountInput(report) : data.sector === 'financial' ? financialDiscountInput(report) : minimumDiscountRate(report);
  const dividend = finite(report.dividendPerShare) ? dividendInStatementCurrency(report, report.dividendPerShare) : years.at(-1)?.dps;
  return {
    model: 'dcf', earningsMethod:currentEarningsMethod, ownerEarnings: text(finite(data.starting) ? data.starting / million : null),
    ...(equityOnly ? {personalEquityRate:false} : {}),
    growth,
    rate: String(rate), terminal: '2', waccBeta:'', years: String(projectionYears),
    netDebt: text(!directEquityModel(report) && finite(data.netDebt) ? data.netDebt / million : null),
    shares: finite(data.shares) && data.shares > 0 ? String(data.shares) : '', dividend: text(dividend)
  };
}

export function calculateValuation(report, inputs, method = 'dcf') {
  const equityOnly = directEquityModel(report);
  const autoEquity = equityOnly && !inputs.personalEquityRate;
  const rate = autoEquity ? waccEstimate(report,inputs.waccBeta,'cashFlow').equityCost : numeric(inputs.rate) / 100;
  const terminal = numeric(inputs.terminal) / 100;
  const growth = numeric(inputs.growth) / 100;
  const shares = numeric(inputs.shares);
  const price = comparablePrice(report);
  const currency = report.currency;
  const fail = error => ({error, price, shares, currency});
  if (autoEquity && !finite(rate)) return fail('Enter a personal cost of equity or supply a current currency-matched yield and beta.');
  if (equityOnly && !finite(rate)) return fail('Enter a personal cost of equity.');
  if (!finite(rate) || (!equityOnly && rate < minimumDiscountRate(report) / 100)) {
    return fail('Enter a discount rate at or above the model minimum.');
  }
  if (!finite(terminal) || rate <= 0 || rate > 1 || terminal <= -1 || terminal > .1 || rate <= terminal) {
    return fail('Use a positive discount rate above perpetual growth (above −100% and at most 10%).');
  }
  if (!Number.isSafeInteger(shares) || shares <= 0) {
    return fail('Enter the number of outstanding shares in Sources and assumptions.');
  }
  let base, projectionPV = 0, terminalValue, terminalPV, total, enterpriseValue = null, equityValue, perShare;
  const rows = [];
  const netDebt = method === 'dcf' && !equityOnly ? numeric(inputs.netDebt) * million : null;
  if (method === 'gordon') {
    base = numeric(inputs.dividend);
    if (!finite(base) || base <= 0) return fail('Enter a positive annual dividend per share to use Gordon Growth.');
    perShare = base * (1 + terminal) / (rate - terminal);
    equityValue = total = terminalValue = terminalPV = perShare * shares;
  } else {
    base = numeric(inputs.ownerEarnings) * million;
    if (!finite(base) || base <= 0) return fail('Enter positive starting Owner Earnings.');
    if (!finite(growth) || growth <= -1 || growth > 2) return fail('Enter annual Owner Earnings growth above −100% and at most 200%.');
    if (!equityOnly && !finite(netDebt)) return fail('Enter net debt in Sources and assumptions. Use zero only when verified.');
    for (let year = 1; year <= projectionYears; year++) {
      const flow = base * (1 + growth) ** year;
      const pv = flow / (1 + rate) ** year;
      rows.push({year, flow, pv});
      projectionPV += pv;
    }
    terminalValue = rows.at(-1).flow * (1 + terminal) / (rate - terminal);
    terminalPV = terminalValue / (1 + rate) ** projectionYears;
    total = projectionPV + terminalPV;
    enterpriseValue = equityOnly ? null : total;
    equityValue = equityOnly ? total : enterpriseValue - netDebt;
    perShare = equityValue / shares;
  }
  if (![total, equityValue, perShare, terminalPV, terminalValue].every(finite)) {
    return fail('These assumptions produce a value outside the supported range.');
  }
  return {price, shares, currency, base, rate, growth, terminal, years: projectionYears, rows, projectionPV, terminalValue,
    terminalPV, total, enterpriseValue, equityValue, directEquity:equityOnly, netDebt, perShare, terminalWeight: terminalPV / total,
    margin: finite(price) && perShare > 0 ? 1 - price / perShare : null,
    upside: finite(price) && price > 0 ? perShare / price - 1 : null,
    dividendNext: method === 'gordon' ? base * (1 + terminal) : null};
}

export function valuationScenarios(inputs, report, equityOnly = directEquityModel(report)) {
  const minimum = minimumDiscountRate(report);
  const rate = numeric(inputs.rate);
  const equityRate = equityOnly && !inputs.personalEquityRate ? equityDiscountInput(report,inputs.waccBeta) : inputs.rate;
  return [-1, 0, 1].map((direction, index) => ({
    ...inputs, name: ['Bear', 'Base', 'Bull'][index],
    growth: percentInput(numeric(inputs.growth) + direction * 5),
    rate: equityOnly ? equityRate : direction === 0 || !finite(rate) || rate < minimum ? inputs.rate : text(Math.max(minimum, rate - direction * 2)),
    ownerEarnings: text(numeric(inputs.ownerEarnings) * (1 + direction * .15))
  }));
}

export function valuationSensitivity(report, inputs) {
  const base = calculateValuation(report, inputs);
  if (base.error) return null;
  const minimum = minimumDiscountRate(report);
  const rates = directEquityModel(report) ? [inputs.personalEquityRate ? numeric(inputs.rate) : Number(equityDiscountInput(report,inputs.waccBeta))] : [-2, -1, 0, 1, 2].map(offset => numeric(inputs.rate) + offset)
    .filter(rate => rate >= minimum && rate <= 100);
  const growths = [-4, -2, 0, 2, 4].map(offset => numeric(inputs.growth) + offset);
  return {rates, growths, rows: growths.map(growth => ({growth,
    cells: rates.map(rate => calculateValuation(report, {...inputs, growth, rate}))}))};
}

export function reverseGrowth(report, inputs, target) {
  if (!finite(target) || target <= 0) return null;
  let lo = -.99, hi = 2;
  const value = growth => calculateValuation(report, {...inputs, growth: growth * 100});
  const lower = value(lo), upper = value(hi);
  if (lower.error || upper.error || target < lower.perShare || target > upper.perShare) return null;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (value(mid).perShare < target) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}
