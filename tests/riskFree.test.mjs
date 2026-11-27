import test from 'node:test';
import assert from 'node:assert/strict';
import {riskFreeObservation,treasuryReference,validBenchmark} from '../web/riskFree.mjs';
const report={currency:'EUR',quote:{currency:'GBp'},fetchedAt:'2026-11-27T09:00:00Z',riskFreeRates:{
 EUR:{date:'2026-11-26',currency:'EUR',sourceID:'bund',yield:3.25},
 GBP:{date:'2026-11-24',currency:'GBP',sourceID:'gilt',yield:5.1531}
}};
test('quote and cash flow benchmarks stay separate, including penny quotes',()=>{
 assert.equal(riskFreeObservation(report).currency,'GBP');
 assert.equal(riskFreeObservation(report,'cashFlow').currency,'EUR');
 assert.equal(riskFreeObservation({...report,currency:'JPY'},'cashFlow'),null);
});
test('stale yields, future observations, invalid dates and crossed provider identity are excluded',()=>{
 const obs=report.riskFreeRates.EUR;
 assert.equal(validBenchmark('CHF',{...obs,currency:'CHF'}),false);
 assert.equal(validBenchmark('EUR',{...obs,date:'2026-02-31'}),false);
 for(const date of ['2026-11-19','2026-11-28'])assert.equal(riskFreeObservation({...report,riskFreeRates:{EUR:{...obs,date}}},'cashFlow'),null);
 assert.equal(new URL(treasuryReference({...obs,url:'https://example.invalid'}).url).hostname,'www.bundesbank.de');
});
test('old euro reports never reuse their historic US yield, while dollar dossiers still open offline',()=>{
 const legacy={...report,quoteCurrency:'EUR',quote:null,riskFreeRates:undefined,treasury:{yield:4.8,date:'2026-11-26'}};
 assert.equal(riskFreeObservation(legacy,'cashFlow'),null);
 assert.equal(riskFreeObservation({...legacy,currency:'USD'},'cashFlow').yield,4.8);
});
