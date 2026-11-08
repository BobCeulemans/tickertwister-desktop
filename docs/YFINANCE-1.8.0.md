# Yahoo adapter upgrade: yfinance 0.2.66 → 1.8.0

Validated locally on 8 November 2026 for Tickertwister Desktop 1.0.3 (Apple Silicon, Python 3.14).

## Dependency scope

The previous environment and v1.0.2 source/installers were retained. A separate environment installed the existing exact dependency pins, changing yfinance to 1.8.0 and adding its dependency lxml 6.1.3. `pip check` passes. The yfinance and lxml license notices are included. The full installed environment is checked against the pinned requirements before packaging.

## Accounting names and dates

`pretty=False` remains explicit for income statements, balance sheets and cash flow, both annual and quarterly. `engine/engine.py:MAP` retains all 56 application fields and their statement/name bindings. `engine/tickertwister.py:ALIASES` retains the 31 legacy name mappings. A frozen contract records these mappings for regression tests.

Tests use distinct synthetic numbers for every row, statement and date, with misleading same-name rows in other statements. Rows and columns are shuffled independently. Tests cover alternative names, accounting signs, missing net income/net borrowing, dates, all 39 score contributions, EPS history and FCFE valuation.

The tests exposed a pre-existing EPS dependency on source-column order. EPS now reads the date-aligned frame used by the other criteria; the calculation and point-allocation rule are unchanged. Duplicate names or dates are excluded and produce a data warning rather than being silently merged or arbitrarily selected.

The optional `LongTermDebtCurrent` item was absent from the requested Yahoo field set in both versions. It remains missing when unavailable; it is deliberately not substituted with `CurrentDebt`, a different accounting concept.

## Live comparison

| Company | Statement currency | Quote currency | Annual / quarterly periods | Available criteria | Score /100 |
|---|---|---|---|---|---|
| AAPL | USD | USD | 4 / 5 | 36 / 39 | 70.86 |
| MSFT | USD | USD | 4 / 5 | 38 / 39 | 83.72 |
| ASML.AS | EUR | EUR | 4 / 5 | 38 / 39 | 82.13 |
| SONY | JPY | USD | 4 / 5 | 33 / 39 | 51.10 |

Both versions produced identical annual and quarterly mapped values, all original annual statement rows and all 39 criterion contributions for these snapshots. All 2,016 mapped field/date bindings (56 × 9 × 4) were checked against their source statement, including missing values. SONY keeps separate JPY accounts, USD quotes and explicit FX/ADR handling.

Identical captured inputs were also replayed offline through the previous and upgraded environments, alongside a synthetic baseline: scores, criteria, histories, annual/quarterly values and valuations matched exactly. The original analysis-rules file and frontend weighting/valuation formula modules are unchanged.

## Reproduction

```sh
python -m pytest engine/test_engine.py engine/test_data_contract.py tests/test_source.py tests/test_notarize.py
npm test
npm run check:locales
npm run check:release
```

CI is deterministic and never calls Yahoo or OpenAI. Live snapshots are local validation evidence, not bundled fixtures or user data. A four-company sample cannot establish compatibility for every Yahoo ticker. Missing or revised upstream data must remain distinguishable from zero; future provider changes can legitimately alter availability or scores. No investment recommendation is implied by these test scores.

Upstream: [release 1.8.0](https://github.com/ranaroussi/yfinance/releases/tag/1.8.0), [versioned source](https://github.com/ranaroussi/yfinance/tree/1.8.0).
