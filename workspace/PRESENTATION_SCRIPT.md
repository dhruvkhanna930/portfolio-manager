# Investrix — 15-minute presentation script
### Team ChequeMate · Dhruv · Daksh · Tanushree · Tanishq · Ridhima · Srishti

---

## ⚠️ Read this first

**1. Your original timing was 16 minutes in a 15-minute slot.**
2.5 + 2 + 2 + 2.5 + 3.5 + 2.5 = 15 min of speaking, *plus* a 1-minute
conclusion — and that's before six handoffs. The budget below is **14:10
spoken**, which leaves ~50 seconds of real slack. Judges' rooms always lose
time. Do not spend the slack in advance.

**2. Two errors on your slides — fix before presenting.**

| Slide | Problem | Fix |
|---|---|---|
| 1 (cover) | Reads **"TEAM INVESTRIX"** | Should be **"TEAM CHEQUEMATE"** — Investrix is the product, ChequeMate is the team. The knight only makes sense as *ChequeMate*. |
| 3 (architecture) | Transactions card reads **"BUV / SELL / DIVIDEND"** | Typo — should be **BUY**. |

**3. Re-seed before you present.** Your live DB currently has 17 holdings at
₹21,83,341 because of testing. Slide 6 says *15 holdings, ₹1.04L, up 12.88%*.
If Srishti says one number and the screen shows another, you lose credibility
in the first 90 seconds.

```bash
cd backend && source .venv/bin/activate && python seed_demo.py
```

---

## Timing budget

| # | Speaker | Segment | Words | Budget | Running |
|---|---|---|---|---|---|
| 1 | **Srishti** | Slides 1–5, framing | 286 | **2:10** | 2:10 |
| 2 | **Ridhima** | Home · Portfolio · Wallet · Transactions | 200 | **1:35** | 3:45 |
| 3 | **Tanushree** | Stock detail · live BUY of Wipro | 244 | **1:55** | 5:40 |
| 4 | **Tanishq** | SIP simulator · Calculators · AI Suggestions | 271 | **2:05** | 7:45 |
| 5 | **Dhruv** | Analytics — all 5 tabs | 454 | **3:30** | 11:15 |
| 6 | **Daksh** | Recommendation model | 338 | **2:35** | 13:50 |
| 7 | **Srishti** | Close | 83 | **0:40** | **14:30** |

**These are measured, not estimated.** 1,876 spoken words total:

| Delivery pace | Runtime | Margin |
|---|---|---|
| 130 wpm — deliberate, with demo pauses | **14:25** | +35s |
| 145 wpm — brisk, adrenaline | **12:55** | +2:05 |

Nerves make people speed up, so expect the real number between 13 and 14:30.
**Time yourself once against a stopwatch.** If your section runs long, cut
words — don't cut pauses. The pauses are what make it land.

**Dhruv drives the screen for the entire demo.** Every demo section below is
split into `▸ DHRUV DRIVES` (what to click) and `▸ SAYS` (the words). Rehearse
these as pairs — the clicking must lead the sentence by about a second.

---

## Pre-flight checklist

- [ ] `python seed_demo.py` — fresh 15 holdings, ₹1,04,068, +12.88%
- [ ] Backend running: `flask --app app run --port 5000`
- [ ] Frontend running: `npm run dev` → http://localhost:5173
- [ ] **Warm the recommendation cache** — open the Recommendations page once
      and let it finish. First call takes ~10s cold; cached 15 min after.
- [ ] **Warm AI Suggestions** — click Generate once so the review is cached.
- [ ] `GROQ_API_KEY` set in `backend/.env` (the AI page says "not configured"
      without it)
- [ ] Browser at 90% zoom, one clean window, notifications off
- [ ] Wipro searchable in the buy modal (test the live search once)
- [ ] Wallet has cash — a BUY that overdraws is *rejected by design*

> If the wifi dies, everything still works except AI Suggestions and live
> search. Prices are cached locally. Say so if it happens — it's a design
> feature, not an excuse.

---

# 1 · SRISHTI — Opening & slides
### 2:05 · Slides 1 → 5

### Slide 1 — Cover *(~30s)*

> Good morning. We're **Team ChequeMate**, and this is **Investrix** — a
> portfolio platform for Indian stocks, mutual funds and bonds.
>
> One sentence explains every decision we made:
>
> **"Store what the user does. Fetch what the market is. Calculate the rest."**
>
> Three categories, three rules. Your transactions are sacred. Market prices
> are disposable and rebuilt on a schedule. Everything in between — profit,
> risk, allocation — is *calculated fresh every time*, never stored, so it
> can't drift from the truth.

### Slide 2 — Every number is earned *(~30s)*

> Here's what that buys you. In Investrix, **you cannot type a holding.**
> There is no field anywhere to edit a quantity or a balance.
>
> You place one transaction. That single record atomically writes two things —
> your holding, and your cash ledger. Your wallet balance isn't stored at all;
> it's the sum of the ledger, computed on read. So the two can never disagree.
>
> And a buy that would overdraw your wallet is **rejected**, not silently
> clamped. That's how a real brokerage behaves.

### Slides 3, 4, 5 — Fast preview *(~35s)*

*Move quickly — these get demonstrated properly later.*

> Architecture. Three engines — CRUD, calculation, AI — over two data layers.
> Note the one dashed arrow: **external APIs write only to our cache, never to
> your data.** If yfinance returns garbage tomorrow, your transaction history
> can't be corrupted by it.
>
> On top, two things we'll show live: a **recommendation engine** scoring
> candidates on four weighted components, including two neural networks we run
> ourselves — and a **calculation engine** with nine advanced analytics.
>
> Every number in both is really fetched or really calculated. Where no free
> data source exists — FD rates, inflation — we label it an assumption rather
> than faking it.

### Handoff *(~10s)*

> That's the philosophy. Eleven minutes to prove it, live. **Ridhima** —
> the front door.

---

# 2 · RIDHIMA — Home, Portfolio, Wallet, Transactions
### 1:50

**▸ DHRUV DRIVES:** Home page, already loaded.

> This is the dashboard. Fifteen holdings — ten stocks, five mutual funds —
> ₹1,04,000 invested, currently up 12.88%.
>
> Note the market movers. **Gainers and losers, both.** We seeded this
> deliberately: a demo where everything is green tells you nothing about
> whether the app works. Reliance is up 18% overall but *down* 2.5% today —
> those are two different questions and we answer both.

**▸ DHRUV DRIVES:** → Portfolio page. Scroll the table once.

> The portfolio table. Every row here is derived — quantity, average price,
> profit and loss, weight in the portfolio. None of it was typed. Red and
> green are real: Infosys is down 9%, the SBI balanced fund down 12%.

**▸ DHRUV DRIVES:** → Wallet page.

> The wallet. This balance is not a stored field — it's the sum of every entry
> below it. Deposits credit, buys debit, dividends credit. Recompute it from
> scratch at any moment and you get the same answer, because there's only ever
> one source of truth.

**▸ DHRUV DRIVES:** → Transactions page.

> And the ledger behind all of it. Every buy, sell and dividend, with real
> dates. This isn't a log — it's the *input*. Delete this table and the
> portfolio ceases to exist. Keep it and everything else rebuilds itself.

### Handoff

> **Tanushree** will take you into a single stock — and buy one, live.

---

# 3 · TANUSHREE — Stock detail & live BUY
### 2:00

**▸ DHRUV DRIVES:** Portfolio → click **RELIANCE** (or any holding).

> This is a single asset page. The chart is a real candlestick chart —
> crosshair, OHLC tooltip, and period buttons from one day out to all time.
>
> Behind those buttons is a decision worth mentioning: we don't call the
> market on every click. When an asset is first added we do **one** deep
> historical pull and cache it. Every period button after that reads from our
> own database. It's faster, and it means we're not rate-limited mid-demo.

**▸ DHRUV DRIVES:** Scroll to fundamentals.

> Fundamentals. And there's an honest split here that we're deliberate about.
>
> Some of these we **fetch** — market cap, P/E, sector, beta — those come from
> the market data API. Others we **compute ourselves** from cached price
> history: volatility, our own beta against the Nifty, the risk metrics.
>
> We label which is which. A number you fetched and a number you calculated
> carry different confidence, and pretending otherwise is how dashboards start
> lying to people.

**▸ DHRUV DRIVES:** Scroll to news section.

> News for this specific asset. We cache headlines and links only — never
> article bodies. That's a copyright decision, not a technical one.

**▸ DHRUV DRIVES:** Open buy modal → search **"Wipro"** → select → quantity → confirm.

> Now let's buy something live. Searching Wipro — this is searching the *whole
> NSE*, not a fixed list we seeded.
>
> I'll buy ten shares. Watch three things happen from this one action.

**▸ DHRUV DRIVES:** Confirm. Then flick to Wallet, then Portfolio.

> The wallet just went down. The holding just appeared. The transaction is in
> the ledger. **One action, three consistent records, no page reload.** That's
> the slide-two promise, executed.

### Handoff

> **Tanishq** — over to you.

---

# 4 · TANISHQ — SIP, Calculators, AI Suggestions
### 2:10

> Everything so far is table stakes. Any team can build CRUD.
>
> **The next three things are where we stopped building a CRUD app** — the
> tools I'm about to show, the analytics Dhruv walks through, and the
> recommendation engine Daksh finishes on. Those three are our MVP.

**▸ DHRUV DRIVES:** → Calculators → SIP Calculator.

> The SIP simulator. Most calculators ask for an assumed return and compound
> it forward. Ours does that — and something better.

**▸ DHRUV DRIVES:** Switch to **historical backtest** mode. Pick a fund, run it.

> **Historical backtest.** No assumed rate at all. Real monthly NAVs from our
> cached history, units bought at the actual price on each date, and what
> you'd genuinely hold today.
>
> The return is XIRR, on the real irregular dates. That matters — the standard
> IRR function assumes evenly spaced periods and gives a quietly wrong answer
> on real investment dates.

**▸ DHRUV DRIVES:** → Historical Returns tab. Run one.

> Same engine, different question — "what if I'd invested a lump sum then."
> Real price, real past date.

**▸ DHRUV DRIVES:** → Analytics menu → **AI Suggestions**. Show the cached review.

> And AI Suggestions — a language model writes a plain-English review.
>
> What makes it different from every other "AI-powered" feature you'll see
> today: **the model does no arithmetic and never sees your holdings.** We
> compute a 32-field fact sheet and hand it that. Its only job is turning our
> numbers into sentences.

**▸ DHRUV DRIVES:** Expand the fact sheet panel, then point at the grounding banner.

> Then we check its work. Every rupee and percent figure is matched back
> against that sheet. Anything that doesn't reconcile is flagged instead of
> rendering as fact.
>
> Not theoretical — it caught the model writing a number **ten times too
> large**, mis-grouping Indian commas and turning twenty-one lakh into two
> crore. Caught automatically, because we assumed it would be wrong eventually
> and built for that.

### Handoff

> **Dhruv** — the analytics engine.

---

# 5 · DHRUV — Advanced Analytics, all 5 tabs
### 3:15 · ~39 seconds per tab — pick one hero per tab, don't read the screen

**▸ Navigate:** Analytics → Overview

### Tab 1 — Overview *(~40s)*

> Five tabs. In order.
>
> **Overview** opens on the Portfolio Health Score. A single number out of a
> hundred — but not a black box: four components with **visible weights**.
> Thirty percent diversification, twenty-five cash, twenty-five volatility,
> twenty sector balance.
>
> Diversification is Shannon entropy of your holding weights, normalised so a
> perfectly even split scores 100. Beside it, the Herfindahl index for
> concentration.
>
> And if a component can't be measured — a new portfolio has no volatility
> history — we **drop it and renormalise**, rather than scoring it zero and
> unfairly tanking your total.
>
> Next to it, Market Mood: breadth, momentum and volatility. We deliberately
> did *not* call this a Fear and Greed Index. It's our formula, on our data.

### Tab 2 — Risk *(~45s)*

**▸ Navigate:** → Risk

> **Risk.** Eight measures, all computed by us from daily returns —
> volatility annualised over 252 trading days, beta against the Nifty,
> Sharpe, Sortino, max drawdown, Value at Risk, Calmar, tracking error.
>
> One detail worth pointing at: we require a **minimum of thirty
> observations**. Below that we exclude the holding and say so, rather than
> computing a Sharpe ratio from six days of data with a straight face.
>
> This scatter is risk against return — every bubble a holding, size is
> position value.
>
> And the correlation matrix answers what a pie chart can't: *are the things
> I own actually different?* You can hold fifteen assets and still own one
> bet. The value is in the off-diagonal pairs you thought were diversified.

### Tab 3 — Performance *(~35s)*

**▸ Navigate:** → Performance

> **Performance** — your portfolio against Nifty 50, Sensex and gold. All
> real data, everything rebased to 100 at period start, so you compare
> *growth*, not price levels.
>
> Two honesty notes. The portfolio line is **time-weighted**, so depositing
> money doesn't masquerade as performance. And these two — FD and inflation —
> are **labelled assumptions**, user-editable, because there's no free API for
> "the" FD rate.
>
> Below: win rate, average holding period, turnover, best and worst.

### Tab 4 — Projections *(~40s)*

**▸ Navigate:** → Projections. Run Monte Carlo if it isn't cached.

> **Projections** — my favourite thing we built.
>
> Monte Carlo. A thousand simulations over 252 trading days. But we don't
> assume a normal distribution — we **bootstrap from your own realised
> returns**, resampling your actual history and compounding forward. Output
> is a fan chart of percentile bands.
>
> It isn't a prediction. It's a range, built from what your portfolio has
> already genuinely done.
>
> Beside it, a **rebalancing simulator**: hand it hypothetical weights, it
> recomputes your risk and health at those weights. Nothing written, no trade
> placed — a calculation, not a rebalance. And goals, against a named target.

### Tab 5 — Activity *(~20s)*

**▸ Navigate:** → Activity

> **Activity** closes the loop — cash flow and a full timeline. Which brings
> us back to slide two: this is the input every other tab was derived from.

### Handoff

> **Daksh** — the recommendation engine.

---

# 6 · DAKSH — Recommendation model
### 2:15

**▸ DHRUV DRIVES:** Analytics → Recommendation Model. **Should be cached.**

### The journey *(~35s)*

> We didn't start here. Our first version was a **random forest** — classic
> tabular model, hand-engineered features. It ran. But it treated every day as
> an independent row, with no memory of *sequence* — and price movement is
> nothing but sequence.
>
> So we moved to recurrent networks, built for exactly that: a **GRU** for the
> one-day horizon, an **LSTM** predicting a five-day path. About 1.7 million
> trained parameters.

### The three modes *(~40s)*

> The engine answers three different questions — because "recommend me a
> stock" isn't one question.

**▸ DHRUV DRIVES:** Click each tab as Daksh names it.

> **Similar** — cosine similarity to the centroid of what you already hold, on
> z-scored fundamentals. Z-scoring first means it compares *style*, not size:
> a mid-cap and a large-cap with the same financial character score alike.
>
> **Complementary** — the opposite. It scores the sector *gap*, surfacing what
> you're underexposed to, plus lower beta and a dividend bonus. It pulls
> against your concentration.
>
> **Risk profile** — a rule table from conservative to aggressive. Needs no
> holdings at all, which solves cold-start: a brand-new user still gets a
> sensible list.

### The blend *(~25s)*

**▸ DHRUV DRIVES:** Expand a card's score breakdown.

> Four scores, blended at declared weights — fit 40, momentum 20, sentiment
> 15, model 25 — and every one **decomposed on screen**. You can see exactly
> why a stock ranked where it did.
>
> If a component has no data we **drop it and renormalise**, rather than
> filling it with a neutral fifty. A missing signal should widen uncertainty,
> not quietly pull everything to the middle.

### The engineering story *(~20s)*

> One thing we're proud of. These are Keras 2.6 checkpoints — TensorFlow
> publishes no wheels for Python 3.14, and modern Keras refuses the format
> outright.
>
> So we read the trained weights straight out of the HDF5 and
> **reimplemented both forward passes in NumPy ourselves.** Real trained
> weights, thirty milliseconds per stock, one megabyte instead of five
> hundred.

### The honest limitation *(~15s)*

> And we'll be straight: these checkpoints were trained on a single airline's
> price history. They are **not** a market oracle. Which is exactly why the
> model is capped at 25% of the blend and never decides anything alone.

### Handoff

> **Srishti** will close.

---

# 7 · SRISHTI — Close
### 0:35

> So — Investrix. Fifty-four endpoints, twenty-six services, eighty-four
> passing tests.
>
> But the number we'd like you to remember is **zero fabricated figures.**
> Everything you saw was really fetched or really calculated. Where we
> couldn't know something, we said so on screen — the labelled assumptions,
> the dropped components, the AI figures flagged as unverified.
>
> Anyone can make a dashboard show a number. The harder problem is making it
> show one you can *check*.
>
> We're Team ChequeMate. Happy to take questions.

---

# Q&A prep

**"Is your recommendation model actually accurate?"**
> No, and we don't claim it is. The checkpoints were trained on a single
> airline's history and applied to Indian equities without retraining. That's
> exactly why it's capped at 25% of the blend and why every score is broken
> down on screen. We'd rather ship a weak signal we're honest about than a
> confident one we can't defend.

**"Why no TensorFlow — isn't that just avoiding the standard tool?"**
> Two hard blockers, not a preference. TensorFlow has no wheels for Python
> 3.14, and TF 2.16+ ships Keras 3 which refuses this HDF5 layout. Using it
> meant pinning legacy TensorFlow *and* downgrading the interpreter, for one
> component worth 25% of one feature. The forward pass is about eighty lines
> of matrix arithmetic, and we validated the parameter counts against the
> checkpoints exactly.

**"What stops the LLM from hallucinating?"**
> Structurally, it can't invent a figure we didn't give it — it never sees
> raw data, only our computed fact sheet. And we verify anyway: every rupee
> and percent figure is reconciled against that sheet, and anything unmatched
> is flagged on screen. It has already caught a real ten-times error live.

**"How is this different from Groww or Zerodha?"**
> We're not competing with execution — there's no broker integration and no
> real money. What we built is the analysis layer: nine advanced computations,
> a transparent health score, and a recommendation engine that shows its
> working. Most consumer apps show you a number. We show you where it came
> from.

**"Why is the data seeded rather than real?"**
> The data pipeline is real — live NSE search, real yfinance and mutual fund
> NAV feeds, and it backfills full price history on first use. We seed a
> deterministic demo portfolio so the numbers are identical for every person
> who runs it, which makes it reproducible. Any of us can clone the repo and
> get this exact screen with one command.

**"What would you build next?"**
> Retrain the price model on Indian equities — that's the honest weak point.
> After that, tax-aware reporting, since Indian capital gains rules are a real
> unsolved pain for retail investors.

---

# If you're running behind

Cut in this order. Never cut Tanishq's MVP framing or Daksh's honest
limitation — those two lines are what separate you from a demo.

| Cut | Saves | Where |
|---|---|---|
| 1 | ~20s | Tanushree's news section — mention in one clause |
| 2 | ~25s | Dhruv's Activity tab — fold into one sentence at the end of Projections |
| 3 | ~20s | Tanishq's Historical Returns tab — SIP backtest makes the same point |
| 4 | ~25s | Daksh's random-forest journey — open straight at GRU/LSTM |
| 5 | ~20s | Dhruv's rebalancing simulator |

**If you're ahead**, the best 30 seconds to spend is Dhruv letting the
correlation matrix breathe — it's the most visually striking thing in the app
and the point about "fifteen assets, one bet" lands with judges.
