# Financial method and limits

The original Python analysis is preserved in `engine/analysis_rules.py` and adapted by `engine/tickertwister.py`; `engine/engine.py` normalizes Yahoo data for the desktop UI. The original 39 sections include base and trend rules. Effective score = earned available weighted points / available weighted maximum × 100. Missing criteria are excluded, and coverage is a count rather than weighted coverage. User weighting scales a criterion’s contribution without changing its underlying point fraction.

The migration uses explicit yfinance methods and normalized statement aliases, handles missing/invalid denominators, and exposes actual annual dates rather than implying that seven years are always available. The historical scoring model uses at most four annual statements. Additional comparison history is limited to the observations actually returned; five years is a maximum, not guaranteed availability. Original-source notices remain intact.

Current/TTM values, annual histories, long-window averages and user assumptions are distinct. Read the period labels and formulas. Financial firms and unusual accounting structures may need sector-specific models. A high score does not prove a durable competitive advantage or predict returns.

Valuation tools are scenarios: FCFE = operating cash flow − capital expenditure + net borrowing. FCFE-based equity models do not subtract debt a second time. User-adjusted growth, rates and terminal assumptions can materially change the result. Currency/ADR comparisons require explicit compatible units; presentation-language changes never convert currency. Do not treat an unavailable value as zero.

AI-AIC receives the active saved company score/weights, criteria, ratios and history, with a visible input preview. User valuation assumptions and share-price targets are excluded from its quality-focused assessment. The conclusion is a research triage, not a personalized recommendation or trade instruction. Audit the statements and business risks independently.

## Main-model starting growth (v1.0.2)

The FCFE multiple model and Valuation Lab use the same CAGR over the full available annual history, ordered by fiscal end date: `(latest FCFE / earliest FCFE) ** (365.25 / elapsed_days) - 1`. Both endpoints must be finite and positive, with at least two distinct fiscal dates. A declining positive cash flow yields negative growth; there is no upper cap. For legacy SEC snapshots only, the existing FCF proxy is retained.

Uncalculable CAGR starts at **0% as an explicit editable assumption**, not a measured value. Yahoo revenue growth is no longer substituted into the main model. Starting growth is displayed to two decimals; the historical calculation uses unrounded amounts and actual elapsed time. A new analysis or Restore defaults applies this rule. Saved user model inputs are preserved when reopening a snapshot. Quality-score rules and weights are unchanged. Historical growth is not a forecast; a small or exceptional starting cash flow can still produce a high CAGR.
