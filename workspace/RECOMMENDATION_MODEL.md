# Recommendation Model — how it actually works

Phase 16. This document describes the recommendation engine end to end: the two
trained neural networks, what they consume and emit, how their output becomes a
score, what else feeds the ranking, and where the whole thing is honest about
not knowing.

It also records what was wrong with the original implementation that this port
is based on, because two of those defects meant the shipped system could not
have been producing the numbers it displayed.

---

## 1. What this is

Given the stocks you already hold, rank stocks you *don't* hold. Three modes:

| Mode | Question it answers | Needs holdings? |
|---|---|---|
| `similar` | "More of what I already own" | Yes |
| `complementary` | "What would diversify me" | Yes |
| `risk_profile` | "Where do I even start" | **No** — cold start |

Every candidate gets a 0–100 score built from four components. The UI shows the
decomposition on every card, because a ranking you can't interrogate is a
ranking you shouldn't trust.

**This is not advice.** Per CLAUDE.md §13, output is framed as educational,
there is no Buy button, and nothing is persisted about what you were shown.

---

## 2. The two trained models

Two Keras checkpoints came from the model workstream:

```
Qantas_GRU_trained_model_oneday.h5      718,081 params
Qantas_LSTM_trained_model_fivedays.h5   958,325 params
```

Architecture read directly out of the HDF5 `model_config`, not assumed:

### GRU — 1-day horizon

```
InputLayer            (None, 90, 6)
GRU        units=320  tanh   return_sequences=True
Dropout    rate=0.2
GRU        units=240  tanh   return_sequences=False
Dropout    rate=0.2
Dense      units=1    linear
```

### LSTM — 5-day horizon

```
InputLayer            (None, 90, 6)
LSTM       units=320  tanh   return_sequences=True
Dropout    rate=0.2
LSTM       units=240  tanh   return_sequences=False
Dropout    rate=0.2
Dense      units=5    linear
```

Both trained with Adam (lr = 0.001, β₁ = 0.9, β₂ = 0.999) against MSE, saved
under Keras 2.6.0.

### Why two different recurrent cells

Both LSTM and GRU are gated RNNs that exist to fix the vanilla RNN's vanishing
gradient — over a 90-step window, a plain RNN's gradient signal from step 1 has
essentially vanished by step 90, so it cannot learn that something three months
ago matters.

- **GRU** has two gates (update, reset) and no separate cell state. Fewer
  parameters per unit, trains faster, tends to do at least as well on shorter
  sequences and smaller datasets.
- **LSTM** has three gates (input, forget, output) plus a cell state carried
  separately from the hidden state. More capacity to hold information over long
  spans, at the cost of more parameters.

The split here is defensible: the cheap fast cell does the 1-step-ahead job, the
higher-capacity cell does the 5-step-ahead job where more history has to be held
across the prediction horizon. Note that both are *stacked* (two recurrent
layers), so the first layer emits a sequence of hidden states and the second
consumes it — that's what `return_sequences=True` on layer 1 is doing.

### The `Dense(5)` head matters

The LSTM emits **five values, not one** — one normalized close per day of the
horizon. It is a direct multi-horizon regressor, not a single-step model called
five times. The original code read `prediction[0][0]`, i.e. day 1 only, and
labelled it the 5-day prediction.

---

## 3. Input pipeline

Both checkpoints declare `batch_input_shape [None, 90, 6]`:

- **90 timesteps** — 90 trading days, roughly 4½ calendar months.
- **6 features** — this is the giveaway that they were trained on a raw
  `yfinance.download()` frame, whose default column set is exactly:

  ```
  Open, High, Low, Close, Adj Close, Volume
  ```

So one input tensor is a 90-day OHLCV+AdjClose bar window.

### Normalization

```python
# per feature, over the window
scaled[t][f] = (raw[t][f] - min_f) / (max_f - min_f)
```

Min-max to [0, 1], computed **per feature, over the 90-row window**. Flat
features (`max == min`, e.g. a halted stock) map to a constant 0.5 rather than
dividing by zero.

> **Known limitation.** The scaler fitted at training time was not shipped with
> the checkpoints. Per-window min-max is the standard construction for this
> model family and is what's reconstructed here, but it is a reconstruction, not
> a recovery. Absolute price predictions therefore carry more uncertainty than
> the network's own training error implies. This is one of the reasons the model
> is weighted at 25% and not more.

### Inverting the output

The network emits normalized levels, so they are pushed back through the close
column's scale:

```python
price = normalized * (close_max - close_min) + close_min
```

---

## 4. From a predicted price to a 0–100 score

This is the step the original got conceptually wrong, so it's worth being
explicit.

The raw network output is a **normalized price level in [0, 1]**. The original
multiplied it by 100 and called it a score. That number answers "where in its
recent 90-day range does the model think this lands?" — a stock pinned at its
range high scores ~100 whether or not it is predicted to *rise*. It is a
position-in-range statistic wearing a prediction's clothes.

What a recommendation actually needs is the **expected return relative to
today**:

```python
expected_return_pct = (predicted_price / last_close - 1) * 100
```

That's then mapped onto 0–100 with a saturating curve:

```python
score = 50 * (1 + tanh(expected_return_pct / 3.0))
```

- 0% expected return → exactly **50** (neutral)
- +3% → **88.1**
- −3% → **11.9**
- symmetric: `score(+x) + score(−x) == 100`
- bounded: an implausible +400% (usually a bad data row) cannot dominate the
  blend, but still ranks above +5%

`tanh` rather than a hard clamp so the difference between +1% and +2% still
moves the needle, which a clamp at ±5% would flatten.

The two horizons are then combined:

```
model_score = 0.4 * score_1day + 0.6 * score_5day
```

weighting the longer horizon higher because the 1-day signal is noisier. If only
one checkpoint loads, that one is used at full weight.

---

## 5. The other three components

The network is one of four signals, all normalized to 0–100 before anything is
blended.

| Component | Weight | Source | How |
|---|---|---|---|
| **fit** | 0.40 | yfinance `.info`, cached in `asset_metrics` | mode-specific, see §6 |
| **momentum** | 0.20 | our own `price_history` | 90-day total return through the same `tanh` map (scale 12%) |
| **sentiment** | 0.15 | our own `news_cache.sentiment` | POSITIVE=100, NEUTRAL=50, NEGATIVE=0, averaged over 30 days, min 2 articles |
| **ml** | 0.25 | LSTM + GRU | §3–§4 |

Weights are anchored on the original's stated intent (fundamentals 0.40, trained
models 0.25); its combined 0.35 "AI score" was internally `0.4 * sentiment +
0.6 * forecast`, so that's split back out into 0.15 and 0.20.

**Sentiment uses our own news cache**, not a fresh transformer. The original
pulled in DistilBERT (~250MB, plus torch) to classify headlines at request time.
Our news provider already returns a sentiment label and we already cache it per
asset (§5.1), so recomputing it would be paying a large dependency to derive
data we are storing anyway.

---

## 6. The three modes

### `similar` — cosine similarity to your portfolio centroid

Style vector per stock:

```
[ pe_ratio, beta, dividend_yield, profit_margin, return_on_equity ]
```

Deliberately style, not size — so a mid-cap and a large-cap running the same
playbook can match.

1. Clamp each feature to a plausible range. yfinance will occasionally hand back
   a P/E of 40,000 for a company emerging from a loss year; unclamped, one such
   row dominates the standardization and flattens every other stock to
   near-identical scores.
2. **Z-score each dimension across candidates and holdings together.** Raw
   values aren't comparable magnitudes — a P/E of 25 against a beta of 1.1 —
   and cosine on raw features would be ~entirely a P/E ranking. Standardizing
   the two groups separately would put them in different spaces and make the
   centroid meaningless.
3. Take the **centroid** of your holdings' standardized vectors.
4. `cosine(candidate, centroid)`, mapped from [−1, 1] onto 0–100.

A stock with fewer than 3 of the 5 features available is rejected rather than
imputed — below that, "similarity" is mostly measuring our own fill-in values.

### `complementary` — continuous diversification gap

```python
gap   = 1 - (portfolio value fraction already in this sector)
score = 50 + 30*gap + 12*beta_relief + min(8, dividend_yield*2)
```

Sector exposure is **value-weighted** — holding one huge IT position and four
tiny ones is an IT concentration problem, and a count-based view would call that
well diversified.

`beta_relief` is proportional: `(portfolio_beta − candidate_beta) / portfolio_beta`,
so a stock that meaningfully lowers portfolio beta scores above one that barely
does.

> This was originally three binary bumps (`+25` new sector, `+15` lower beta,
> `+10` pays a dividend). Because they were flags, every unheld sector scored
> identically and a dozen candidates tied at the ceiling — at which point final
> ordering fell out of whatever order SQLite returned rows in. Verified before
> and after: six candidates went from `100.0, 100.0, 100.0, 100.0, 100.0, 100.0`
> to `100.0, 100.0, 99.6, 92.9, 89.8, 87.5`.

### `risk_profile` — explicit rule table, cold start

Four appetites (conservative / balanced / assertive / aggressive), each a
readable threshold table over P/E, beta, dividend yield, profit margin, ROE.
Base 50, bonuses to a cap of 100.

Kept as an explicit rule table rather than a learned model precisely because a
user should be able to read the thresholds and disagree with them. Needs no
holdings, so it works on an empty portfolio.

---

## 7. Blending

```python
usable   = [(value, weight) for each component that has data]
score    = Σ(value * weight) / Σ(weight)
coverage = Σ(weight)
```

**Missing components are dropped and the remaining weights renormalized — not
imputed at 50.** Imputing would pull every score toward the middle and make a
stock with *no* news look identical to one with genuinely neutral news. Those
are different states and the score should not conflate them.

`coverage` is surfaced as a confidence label:

| coverage | + trained model live | label |
|---|---|---|
| ≥ 0.85 | yes | high |
| ≥ 0.60 | — | medium |
| < 0.60 | — | low |

---

## 8. Request flow

```
GET /api/recommendations?mode=similar&limit=8
   │
   ├─ candidate universe ← all STOCK rows in asset_metadata
   │     (Nifty50 seed §4.1 + anything you resolved)
   │
   ├─ EXCLUDE everything you already hold          ◄── see §9, defect 1
   │
   ├─ fundamentals for candidates + holdings
   │     cache-first from asset_metrics (period='FUND', 24h TTL)
   │     miss → yfinance .info → write back
   │
   ├─ fit score per candidate  (mode-specific, §6)
   │
   ├─ SHORTLIST to ~2×limit by fit
   │     the ML step costs a 6-month OHLCV download per symbol;
   │     running it over ~50 candidates would be ~50 round-trips per page load
   │
   ├─ for each shortlisted candidate:
   │     momentum  ← price_history      (local)
   │     sentiment ← news_cache         (local)
   │     ml        ← GRU + LSTM         (network, or momentum fallback)
   │
   ├─ blend → final_score, coverage, confidence
   ├─ build reasons (top 3 factors ≥65 or ≤35)
   └─ sort desc, take limit
```

Restricted to `STOCK`. Every signal here is equity-shaped — beta, P/E, OHLCV
windows — so mutual funds and bonds are out of scope rather than scored with
fields that don't apply to them.

---

## 9. What was wrong in the original, and what changed

The original (`stock_recommendation_system/`, Django) had four defects. Two were
severe enough that the displayed numbers could not have been what they claimed.

### Defect 1 — "similar stocks" returned stocks you already own

```python
# original recommendations.py, ~L313
for i, symbol in enumerate(valid_symbols):        # valid_symbols = YOUR holdings
    for j, compare_symbol in enumerate(valid_symbols):
        if i != j:
            recommendation_scores[symbol] += similarity_matrix[i][j]
sorted_recommendations = sorted(...)[:num_recommendations]
```

It never looked at a candidate universe. It ranked your own holdings by how
similar they were to each other and returned those as recommendations.

**Fixed:** candidates are the universe *minus* your holdings, scored against the
centroid of your holdings.

### Defect 2 — the trained models never ran

The checkpoints declare `(None, 90, 6)`. The original built:

```python
def prepare_sequence_data(self, ticker, lookback=60):
    ...
    return sequence.reshape(1, lookback, 1)      # (1, 60, 1) or (1, 30, 1)
```

A 1-feature, 30- or 60-step window into a 6-feature, 90-step model raises a
shape error on **every single call**. That error was caught:

```python
except Exception as e:
    print(f"Error predicting 1-day return for {ticker}: {str(e)}")
    return 50.0
```

…and replaced with the neutral constant. Combined with the fact that Keras 3
won't load the 2.6-era HDF5 layout at all (the original's own loader prints
`⚠ LSTM model skipped (TensorFlow compatibility)`), **every "trained model
score" the system ever displayed was the hardcoded 50.0.** The 25% model weight
was contributing a constant.

**Fixed:** the window builder emits the real (90, 6) OHLCV tensor. Verified
against the shape read out of the checkpoint, and pinned by
`tests/test_recommendation_math.py`.

### Defect 3 — the weights didn't mean what they said

```python
rec['final_score'] = (rec['rule_score']          * 0.40 +   # range ~0–7
                      rec['ai_score']            * 0.35 +   # range 0–100
                      rec['trained_model_score'] * 0.25)    # range 0–100
```

`rule_score` was a *sum of cosine similarities* (~0–7 for 8 holdings) in
`similar` mode and a small integer (0–6) in `complementary` mode, blended
against two 0–100 scores. A 0.40 weight on a component whose maximum is 7
contributes at most 2.8 points out of ~90 — roughly **2% of the result, not
40%**. The stated weights and the effective weights were unrelated numbers.

**Fixed:** every component is normalized to 0–100 before blending. Pinned by
`test_blend_respects_declared_weights` — fit at 100 with everything else at 0
must produce exactly 40.0.

### Defect 4 — wrong market

The universe was hardcoded US megacaps (`AAPL, MSFT, GOOGL, …`), recommending
NASDAQ tickers to a portfolio denominated in rupees, priced off NSE, and
benchmarked against NIFTY50.

**Fixed:** universe is the Nifty50 basket we already sync plus anything in your
own catalogue.

### Defect 5 — two sector vocabularies, found by tracing real data

Not inherited from the original — this one surfaced while tracing an actual
`complementary` ranking against the real portfolio, and it was producing
backwards output.

Sector labels reach us from two sources that don't agree:

| Source | Vocabulary | Examples in this DB |
|---|---|---|
| Nifty50 seed (§4.1) | Indian market convention | `IT`, `FMCG`, `Metals` |
| yfinance on resolve | GICS-style | `Technology`, `Consumer Goods`, `Basic Materials` |

The portfolio here holds TCS, INFY, WIPRO and TATAELXSI — all labelled
`Technology` — for **47.3%** of value, plus TECHM labelled `IT` for 0.5%. Those
are one sector wearing two names, so the diversifier mode saw "you hold 0% of
IT" and ranked **HCLTECH third as a way to diversify a portfolio that was
already ~48% technology.**

**Fixed:** a `_canonical_sector()` alias map collapses both vocabularies before
any gap is computed. Verified on the real portfolio:

```
before:  #3 HCLTECH.NS   IT           99.6     ← recommended as a diversifier
after:   #6 HCLTECH.NS   Technology   85.42    ← correctly demoted
         Technology bucket 47.3% + 0.5% → 47.8% consolidated
```

> **Worth knowing:** this same split vocabulary also affects the existing
> allocation charts and the Health Score's `sector_balance_score` (§14.3), which
> currently see `Technology` and `IT` as two separate sectors and therefore
> *understate* concentration. Left alone here because §13 scopes this phase to
> additive changes and touching `_sector_label` would shift Phase 5/12/14
> output. Flagged as a separate fix.

### Also changed

- **Django → Flask/SQLAlchemy.** `from django.conf import settings` and
  `StockHolding.objects.filter(...)` don't exist here.
- **DistilBERT dropped** in favour of our own cached news sentiment (§5).
- **sklearn dropped.** `StandardScaler` and `cosine_similarity` are ~15 lines of
  arithmetic; the rest of this codebase computes its statistics in pure Python
  (see `risk_service`) and adding a dependency for two functions would break
  that consistency.
- **`_fetch_fundamentals` unit fix.** yfinance returns `dividendYield` already
  as a percent but `profitMargins` and `returnOnEquity` as fractions. Converting
  all three identically is what made a 0.45% yield render as 45% on the asset
  detail page before it was fixed in Phase 15; the same trap is avoided here.

---

## 10. Running the models without TensorFlow

**The trained networks run for real — there is no TensorFlow anywhere in this
app.** `services/keras_h5_runtime.py` reads the weight tensors straight out of
the HDF5 checkpoints with `h5py` and reimplements the forward pass in NumPy.

### Why not just install TensorFlow

Two independent blockers:

1. **The venv is Python 3.14.** TensorFlow publishes no wheels for it —
   `pip install tensorflow` returns *"Could not find a version that satisfies
   the requirement tensorflow (from versions: none)"*. Using it would mean
   rebuilding the environment on an older interpreter.
2. **Keras 3 refuses these files.** TF ≥ 2.16 bundles Keras 3, which won't load
   the Keras 2.6 HDF5 layout. So the working combination is a pinned legacy TF
   *and* a downgraded Python — for one component worth 25% of the blend.

The forward pass for a stacked GRU/LSTM regressor is ~80 lines of matrix
arithmetic. The rest of this codebase already computes its statistics in pure
Python (`risk_service`), so this is consistent with the app rather than an
exception to it.

### What it implements

Read from `model_config`, never assumed — getting either gate formulation wrong
produces plausible-looking numbers that are quietly incorrect:

| | GRU | LSTM |
|---|---|---|
| cell activation | `tanh` | `tanh` |
| gate activation | **`hard_sigmoid`** = `clip(0.2x+0.5, 0, 1)` | `sigmoid` |
| variant | **`reset_after=False`** | `unit_forget_bias=True` |
| gate order in packed kernel | z, r, h | i, f, c, o |

```
GRU (reset_after=False):        LSTM:
  z  = σ(x·Wz + bz + h·Uz)        z = x·W + h·U + b
  r  = σ(x·Wr + br + h·Ur)        i,f,c,o = split(z, 4)
  h~ = tanh(x·Wh + bh             c = σ(f)·c + σ(i)·tanh(c)
           + (r ⊙ h)·Uh)          h = σ(o)·tanh(c)
  h  = z ⊙ h + (1-z) ⊙ h~
```

Note the reset gate multiplies the *hidden state before* the recurrent matmul —
that's what `reset_after=False` means, and it is **not** interchangeable with
the cuDNN `reset_after=True` form. Dropout is a no-op at inference.

### Verified

Parameter counts recovered by the runtime match the checkpoints exactly, and the
networks respond sensibly to input direction:

```
GRU  718,081 params, 1 output      LSTM  958,325 params, 5 outputs

input window     GRU out    LSTM 5-day path
rising ramp       1.0207    [0.915 0.933 0.919 0.923 0.939]
falling ramp      0.0219    [-0.047 -0.039 -0.043 -0.043 -0.043]
flat              0.5098    [0.481 0.481 0.469 0.468 0.470]
```

Live inference on RELIANCE.NS (last close ₹1302.70):

```
1-day  → ₹1296.34   (-0.49%)   score 41.94
5-day  → ₹1274.34   (-2.18%)   score 18.98
path     [1281.43, 1280.25, 1277.77, 1275.94, 1274.34]
```

~30ms per symbol. Status endpoint reports
`runtime: "numpy (keras_h5_runtime)"`.

### The fallback still exists

If the checkpoints are missing or unreadable, `ml_forecast_service` degrades
rather than failing:

1. `model_status()` reports `trained_models_available: false` with the reason.
2. Per-asset scoring falls back to a **momentum estimate from our own cached
   `price_history`** — recent 30-day drift vs. the prior 60-day drift, so a
   stock accelerating upward scores above one merely drifting up. That measures
   trend *acceleration* over months, which swings by tens of percent where a
   1-day predicted return swings by ones, so it gets its own wider `tanh` scale
   (`MOMENTUM_SCALE_PCT = 15.0`). Reusing the 3% scale pinned nearly every stock
   to 0 or 100 — observed on real data before the constant existed.
3. If there isn't enough cached history either, the `ml` component is `null` and
   gets **dropped from the blend**, not filled with 50.
4. The UI banner says which path is live. It never presents a fallback as a
   model prediction.

Only dependency: `h5py` (~1MB), plus NumPy which ships with yfinance.

Model location resolves in this order:

1. `$MODEL_DIR`
2. `<repo>/stock_recommendation_system/models/`  ← current
3. `<repo>/workspace/models/`

The checkpoints are 20MB of binary already tracked at the repo root, so they're
read in place rather than copied into `workspace/`.

---

## 11. Honest limitations

Things a demo should say out loud rather than let a judge discover.

1. **The models were trained on a single Australian airline.** The filenames are
   literal: `Qantas_*`. They are being applied to Indian equities with no
   retraining, no fine-tuning, and no transfer-learning step. There is no reason
   to expect price dynamics learned from one airline's history to generalize to
   HDFC Bank. This is the single biggest reason the model is capped at 25% of
   the blend and labelled "one weak signal".

2. **No published accuracy for the applied domain.** The original ships
   `evaluate_trained_model()` which computes MAE/RMSE/MAPE/direction-accuracy —
   but on normalized values, so MAE is in normalized units and not comparable
   across stocks. No baseline is reported either, and for next-day price the
   naive "tomorrow = today" baseline is very strong. A direction accuracy of 52%
   would be near-worthless and would look fine in isolation.

3. **The training scaler wasn't shipped** (§3).

4. **Sentiment is only as good as the provider's labels.** We use the label the
   news API returns; we don't verify it.

5. **`similar` mode needs ≥3 fundamentals per stock.** Thinly-covered stocks are
   excluded rather than imputed, so the candidate pool can be smaller than the
   universe.

6. **Momentum coverage is uneven.** `price_history` is backfilled on resolve
   (§4.2), so held assets have deep history while index-seeded candidates may
   have little. That's why `confidence` is usually `low`/`medium` for
   candidates — it's reporting a real data gap, not hedging.

7. **No backtest of the recommendations themselves.** Nothing here has been
   evaluated for whether the ranking would have produced returns. It ranks by
   stated criteria; it does not claim those criteria make money.

---

## 12. API

### `GET /api/recommendations`

| Param | Type | Default | Notes |
|---|---|---|---|
| `mode` | enum | `similar` | `similar` \| `complementary` \| `risk_profile` |
| `risk_profile` | enum | `balanced` | only used by `risk_profile` mode |
| `limit` | int | 8 | 1–25 |
| `use_ml` | bool | `true` | `false` skips the model component entirely |

```jsonc
{
  "mode": "similar",
  "recommendations": [
    {
      "asset_id": 31,
      "symbol": "HCLTECH.NS",
      "name": "HCL Technologies Ltd",
      "sector": "IT",
      "final_score": 90.69,
      "components": { "fit": 90.69, "momentum": null, "sentiment": null, "ml": null },
      "weights_applied": { "fit": 0.4 },
      "coverage": 0.4,
      "confidence": "low",
      "reasons": [
        { "factor": "fundamentals resemble your holdings",
          "direction": "supports", "score": 90.69 }
      ],
      "fundamentals": { "pe_ratio": 24.1, "beta": 0.78, "dividend_yield": 3.4, "...": null },
      "ml_detail": { "source": "unavailable", "score": 50.0 }
    }
  ],
  "candidates_considered": 46,
  "holdings_compared": 8,
  "weights": { "fit": 0.4, "momentum": 0.2, "sentiment": 0.15, "ml": 0.25 },
  "model": { "trained_models_available": false, "reason": "TensorFlow is not installed" },
  "disclaimer": "Educational information only — not investment advice…"
}
```

### `GET /api/recommendations/model`

Which prediction path is live. Cheap, no network.

### `GET /api/recommendations/forecast/<asset_id>`

Raw model output for one asset — both horizons, the predicted 5-day path,
implied returns, and which source produced them. For inspection.

---

## 13. Files

```
workspace/backend/
  services/ml_forecast_service.py       LSTM/GRU wrapper, TF-optional
  services/recommendation_service.py    scoring, modes, blending
  routes/recommendations.py             3 endpoints
  schemas/recommendation.py             marshmallow + OpenAPI
  tests/test_recommendation_math.py     28 tests, no DB/network/TF

workspace/frontend/src/
  pages/Recommendations.jsx                     the page
  components/recommendations/RecommendationCard.jsx
  components/recommendations/ScoreBreakdown.jsx stacked contribution bar
  hooks/useRecommendations.js
```

Reached at **Analytics → Recommendation Model**, or `⌘K` → "Recommendation
Model".

---

## 14. Guardrail compliance (CLAUDE.md §13)

| Rule | How |
|---|---|
| Rule-based, not ML-first | 75% of the blend is rules over real fundamentals/price/news; the network is 25% and degrades to nothing |
| Educational framing, not advice | "Recommendation model", disclaimer on the response *and* the page, no Buy/Sell affordance, links to detail pages only |
| Additive — no refactor of §5–§7 | New service/route/schema/page. Zero changes to existing endpoints or tables; the fundamentals cache reuses `asset_metrics` as it already exists |
| Nothing fabricated (§14) | Every input is a real yfinance field or computed from our own cache. Missing data is `null` and drops out of the blend — never a filled-in placeholder |
