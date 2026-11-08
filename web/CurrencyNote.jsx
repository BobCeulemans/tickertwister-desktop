import {comparablePrice,fxRate,quotedModelValue} from './currency.mjs';
import {dateLabel} from './presentation.mjs';
export default function CurrencyNote({report,value,t,number}){
 if(!report.quote||report.quote.currency===report.currency)return null;
 const p=comparablePrice(report),v=quotedModelValue(report,value);
 return <p className="currency-note">{p!==null?<>{t("Converted price")}: {number(p)} {report.currency}{v!==null&&<> · {t("Model value in quote currency")}: {number(v)} {report.quote.currency}</>}<br/>1 {report.quote.currency} = {number(fxRate(report),4)} {report.currency} · Yahoo FX {dateLabel(report.fx.at,t.language)} · {report.quoteBasis.ordinaryPerQuote}:1 {t("ordinary shares per quoted security")}. {t("Snapshot; no historical currency restatement.")}</>:t("Currency or share basis differs. Refresh the analysis; without a recent FX rate and confirmed share ratio the margin remains unavailable.")}</p>;
}
