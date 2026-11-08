# Financial method and limits

The original Python analysis is preserved in `engine/analysis_rules.py` and adapted by `engine/tickertwister.py`; `engine/engine.py` normalizes Yahoo data for the desktop UI. The original 39 sections include base and trend rules. Effective score = earned available weighted points / available weighted maximum × 100. Missing criteria are excluded, and coverage is a count rather than weighted coverage. User weighting scales a criterion’s contribution without changing its underlying point fraction.

The migration uses explicit yfinance methods and normalized statement aliases, handles missing/invalid denominators, and exposes actual annual dates rather than implying that seven years are always available. The historical scoring model uses at most four annual statements. Additional comparison history is limited to the observations actually returned; five years is a maximum, not guaranteed availability. Original-source notices remain intact.

Current/TTM values, annual histories, long-window averages and user assumptions are distinct. Read the period labels and formulas. Financial firms and unusual accounting structures may need sector-specific models. A high score does not prove a durable competitive advantage or predict returns.

Valuation tools are scenarios: FCFE = operating cash flow − capital expenditure + net borrowing. FCFE-based equity models do not subtract debt a second time. User-adjusted growth, rates and terminal assumptions can materially change the result. Currency/ADR comparisons require explicit compatible units; presentation-language changes never convert currency. Do not treat an unavailable value as zero.

AI-AIC receives the active saved company score/weights, criteria, ratios and history, with a visible input preview. User valuation assumptions and share-price targets are excluded from its quality-focused assessment. The conclusion is a research triage, not a personalized recommendation or trade instruction. Audit the statements and business risks independently.
