// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
import reportStyles from 'report-styles';
// Build a dedicated document from the report only, never from the interactive results.
export function printHTML(selector='#company-print'){
 const report=document.querySelector(selector);if(!report)return null;
 const css=reportStyles.replace(/@media print/g,'@media all');
 return '<!doctype html><html lang="'+document.documentElement.lang+'"><meta charset="utf-8"><title>Tickertwister</title><style>'+css+'</style><style>html,body{margin:0!important;padding:0!important;width:794px!important;background:white!important}main{width:794px!important;padding:0!important;margin:0!important}.print-report{width:794px!important}.print-page{box-sizing:border-box;width:794px;height:1123px;padding:36px!important;margin:0!important;break-after:auto!important}.research-note-print{white-space:pre-wrap!important;overflow-wrap:anywhere;font:13px/24px ui-monospace,monospace!important;max-width:100%}.print-page .print-foot{position:absolute;bottom:30px;left:36px;right:36px}</style><main>'+report.outerHTML+'</main></html>';
}
