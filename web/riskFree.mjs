// Fixed provider links also apply to offline snapshots; never follow a URL supplied by a dossier.
const sources = {
  bund: ['EUR', 'Deutsche Bundesbank · Bund 10Y', 'https://www.bundesbank.de/en/statistics/overview-of-the-statistical-series/-/3-yields-of-current-federal-securities-914558'],
  gilt: ['GBP', 'Bank of England · Gilt 10Y (IUDMNPY)', 'https://www.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?SeriesCodes=IUDMNPY&title=IUDMNPY'],
  snb: ['CHF', 'SNB · Swiss Confederation 10Y', 'https://www.snb.ch/en/srv/current_interest_exchange_rates'],
  jgb: ['JPY', 'Ministry of Finance Japan · JGB 10Y', 'https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/index.htm'],
  boc: ['CAD', 'Bank of Canada · Government benchmark 10Y', 'https://www.bankofcanada.ca/rates/interest-rates/canadian-bonds/'],
  tnx: ['USD', 'Yahoo Finance · ^TNX', 'https://finance.yahoo.com/quote/%5ETNX/'],
  fred: ['USD', 'FRED · DGS10', 'https://fred.stlouisfed.org/series/DGS10'],
  treasury: ['USD', 'U.S. Treasury · 10-Year CMT', 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=']
};

export const majorCurrency = code => ({GBp:'GBP', GBX:'GBP', ZAc:'ZAR', ILA:'ILS'})[code] ?? code;
export function validBenchmark(currency, obs) {
  return !!obs && obs.currency === currency && Object.hasOwn(sources, obs.sourceID) && sources[obs.sourceID][0] === currency &&
    Number.isFinite(obs.yield) && obs.yield > -100 && obs.yield < 100 && typeof obs.date === 'string' &&
    /^\d{4}-\d\d-\d\d$/.test(obs.date) && Number.isFinite(Date.parse(obs.date)) &&
    new Date(obs.date).toISOString().startsWith(obs.date);
}
export function treasuryReference(obs) {
  if (!obs) return null;
  const source = obs.sourceID ?? 'fred';
  if (!Object.hasOwn(sources, source)) return null;
  const [, label, base] = sources[source];
  if (source !== 'treasury') return {label, url:base};
  if (!/^\d{4}-\d\d-\d\d$/.test(obs.date)) return null;
  return {label, url:base + obs.date.slice(0,7).replace('-','')};
}

export function riskFreeObservation(report={}, basis='quote') {
  const currency = majorCurrency(basis === 'cashFlow' ? report.currency : report.quote?.currency ?? report.quoteCurrency ?? report.currency);
  const dated = o => {
    if (!validBenchmark(currency, o)) return false;
    const age = Date.parse(report.fetchedAt?.slice(0,10)) - Date.parse(o.date);
    return age >= 0 && age <= 7 * 86400000;
  };
  const clean = item => item?.sourceID === 'tnx' ? {...item, yield:Number(item.yield.toFixed(6))} : item;
  if (report.riskFreeRates != null) {
    const item = report.riskFreeRates[currency];
    return dated(item) ? clean(item) : null;
  }
  if (currency !== 'USD') return null;
  // Before Preview 6 both stored yields were always US yields, including in EUR dossiers.
  const candidates = [];
  if (report.waccTreasury) candidates.push({...report.waccTreasury, currency:'USD', sourceID:'tnx'});
  if (report.treasury) candidates.push({...report.treasury, currency:'USD', sourceID:report.treasury.sourceID ?? 'fred'});
  return clean(candidates.filter(dated).sort((a,b)=>b.date.localeCompare(a.date))[0]) ?? null;
}
