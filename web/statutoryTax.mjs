// SPDX-License-Identifier: AGPL-3.0-only
// Model fallback for a loss or missing TTM tax inputs. Percentages from OECD
// DSD_TAX_CIT@DF_CIT, CIT_C, ST, S13 (combined standard rates, 2025).
// For the US the selected benchmark is the federal rate, excluding state tax.
export const oecdTaxSource='https://www.oecd.org/en/data/datasets/corporate-income-tax-rates-database.html';
const combined = {
  Australia:30, Austria:23, Belgium:25, Canada:25.981152, Chile:27, Colombia:35,
  'Costa Rica':30, Czechia:21, 'Czech Republic':21, Denmark:22, Estonia:22, Finland:20,
  France:36.13, Germany:30.058462, Greece:22, Hungary:9, Iceland:20, Ireland:12.5,
  Israel:23, Italy:27.81, Japan:29.74, 'South Korea':26.4, Latvia:20, Lithuania:16,
  Luxembourg:23.87, Mexico:30, Netherlands:25.8, 'New Zealand':28, Norway:22,
  Poland:19, Portugal:30.5, Slovakia:24, Slovenia:22, Spain:25, Sweden:20.6,
  Switzerland:19.607821, Turkey:25, Türkiye:25, 'United Kingdom':25
};

export function taxReference(country) {
  if (country === 'United States') return {rate:.21,source:'IRS · 21%',url:'https://www.irs.gov/publications/p542'};
  if (Object.hasOwn(combined,country)) return {rate:combined[country]/100,source:'OECD · 2025',url:oecdTaxSource};
  return {rate:.25,source:null,url:null};
}
