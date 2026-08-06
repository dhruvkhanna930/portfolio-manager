# Analytics, explained like you've never seen a stock chart
### Dhruv's prep sheet · Investrix · Team ChequeMate

Everything here is written for someone who knows nothing about finance. If a
judge asks you something, the plain-English answer is usually the *best* answer
— not the most technical one.

**The one-line version of this whole page:**
> We take the boring records of what you bought and what prices did, and turn
> them into answers to questions people actually have: *Am I taking too much
> risk? Am I doing better than just buying the index? What could this be worth
> in a year? Am I actually diversified, or do I just own fifteen versions of
> the same bet?*

---

# Part 1 — The ideas behind everything

Read this once and the rest of the page becomes obvious.

### Return vs. risk are two different questions

Everyone asks "how much did I make?" Almost nobody asks "how bumpy was the
ride, and was the bumpiness worth it?"

Two portfolios both end the year up 12%. One climbed steadily. The other
doubled, crashed, and clawed back. **Same return, completely different
experience** — and completely different chance of the same thing working next
year. Every risk metric on our Risk tab exists to measure that second thing.

### A "daily return" is the atom

Everything is built from one tiny number:

> If a stock closed at ₹100 yesterday and ₹101 today, its daily return is +1%.

That's it. Volatility, beta, Sharpe, Monte Carlo — all of it is just different
arithmetic on a long list of those little percentages. When someone asks "where
does this number come from?", the honest answer is almost always *"from the
daily returns we computed from cached closing prices."*

### Why "annualised" keeps appearing

Daily numbers are tiny and hard to read — "0.8% daily volatility" means
nothing to a human. So we scale them up to a yearly figure, which people have
intuition for. The scaling factor is **√252**, because there are about **252
trading days** in a year (365 minus weekends and holidays).

You will see 252 everywhere in our code. That's why.

---

# Part 2 — Tab by tab

## TAB 1 · Overview

### Portfolio Health Score

**In plain English:** one number out of 100 telling you whether your portfolio
is sensibly built. Not whether it's *making money* — whether it's *well
constructed*. A portfolio can be up 30% and still be badly built.

**How to read it:**
| Score | Band | Means |
|---|---|---|
| 75–100 | Strong | Well spread, sensible cash, not wild |
| 50–74 | Moderate | Fine, with something to fix |
| 0–49 | Needs attention | Usually over-concentrated |

**How we compute it** — four ingredients, weights visible on screen:

```
Health = 0.30 × diversification
       + 0.25 × cash reserve
       + 0.25 × (100 − volatility)
       + 0.20 × sector balance
```

**Why the weights are shown:** most apps give you a score and hide the recipe.
If we hid it, you couldn't argue with it. Showing it means you can look at a
64 and say "that's the cash component dragging me down, and I'm fine with
that."

**The clever bit worth mentioning:** if a component *can't* be measured — a
brand-new portfolio has no price history, so no volatility — we **drop it and
re-weight the others** so they still add to 100%. The lazy alternative is
scoring it zero, which would unfairly crush a new user's score for the crime
of being new.

---

### Diversification score (Shannon entropy)

**In plain English:** are your eggs actually spread across baskets, or is 80%
of your money in one stock?

**The intuition:** imagine ten holdings. If each is 10% of your money, that's
perfectly even — score **100**. If one is 91% and the other nine are 1% each,
you effectively own one stock — score near **0**.

**Where "entropy" comes from:** it's a measure borrowed from information
theory that quantifies "how spread out" a distribution is. We normalise it
against `ln(n)` — the score for a perfectly even split of *n* holdings — so
that 100 always means "as even as possible for the number of things you own."

**Why not just count holdings?** Because owning 15 stocks where one is 90% of
your money is not diversification. Counting says 15. Entropy says 12. Entropy
is right.

---

### HHI (Herfindahl-Hirschman Index)

**In plain English:** the same question from the opposite direction — how
*concentrated* are you?

Square each holding's percentage weight, add them up. One holding at 100% gives
the maximum. Many small holdings give a tiny number.

**Fun fact worth dropping if it fits:** this is the same index competition
regulators use to decide whether a market has become a monopoly. We're asking
the identical question about your portfolio.

---

### Market Mood Score

**In plain English:** is the market broadly cheerful or nervous right now? A
0–100 weather report.

```
Mood = 0.40 × breadth      (what % of the Nifty basket is up today)
     + 0.35 × momentum     (5-day average vs 20-day average)
     + 0.25 × calm         (inverse of recent volatility)
```

Bands: **80+ Very Bullish · 60+ Bullish · 40+ Neutral · 20+ Bearish · below
that Very Bearish.**

**The honest bit that judges like:** we deliberately did *not* call this a
"Fear & Greed Index." That's a specific, proprietary, differently-computed
thing. Ours is our own formula on our own data, and the disclaimer on screen
says exactly that. Copying a famous name onto a different calculation would be
a small lie.

---

### Portfolio DNA (radar chart)

**In plain English:** the *shape* of what you own, at a glance — how your money
splits across sectors and asset classes. The radar shows the shape; the list
beside it gives exact percentages, because a radar chart is good at "is this
lopsided?" and bad at "is that 22% or 26%?"

---

## TAB 2 · Risk

### Volatility

**In plain English:** how bumpy the ride is. High volatility means big swings
in both directions.

**How to read it:** ~15% is calm for equities. ~25% is normal. 40%+ is a wild
ride. Our portfolio sits around 20%.

**Important:** volatility is *not* the same as losing money. A stock that
doubles in a month is extremely volatile. Volatility measures **uncertainty**,
not direction.

---

### Beta

**In plain English:** how much you move when the market moves.

| Beta | Means |
|---|---|
| 1.0 | You move exactly with the Nifty |
| 1.5 | Market up 10% → you tend up 15%. And down 10% → down 15% |
| 0.5 | You move half as much — steadier, but you lag in a rally |
| Negative | You tend to move *opposite* the market (rare) |

**The catch:** beta only describes the past relationship, and it's measured
against one index. A stock can have a low beta and still be extremely risky in
ways the index simply doesn't capture.

---

### Sharpe ratio

**In plain English:** *"was the bumpiness worth it?"*

You could put money in a fixed deposit and earn ~6.5% with zero drama. Sharpe
asks: how much **extra** did you earn above that, per unit of bumpiness you
endured?

```
Sharpe = (your annual return − 6.5%) ÷ your volatility
```

| Sharpe | Verdict |
|---|---|
| Above 1 | Genuinely good |
| 0 to 1 | You beat the FD, but not by much per unit of stress |
| **Negative** | **You'd have done better in a fixed deposit** |

**Judges may notice our Sharpe is negative on the demo data.** Don't hide
from that — it's the correct answer for a portfolio whose recent window
underperformed a 6.5% risk-free rate. The metric working correctly and
delivering unflattering news is *evidence it isn't decorative.*

**Why 6.5%?** It's a reasonable Indian risk-free rate (roughly a govt bond /
FD). It's a configurable input, not a hardcoded truth.

---

### Sortino ratio

**In plain English:** Sharpe, but fairer.

Sharpe punishes *all* volatility — including upside. But nobody complains
about a surprise 5% gain. Sortino only counts **downside** volatility, so it
answers "how much return did I get per unit of *bad* surprise?"

Sortino is almost always higher than Sharpe. If it's dramatically higher, your
portfolio's swings are mostly upward — which is a nice problem.

---

### Maximum drawdown

**In plain English:** the worst peak-to-trough fall. *"If I'd bought at the
very worst moment, how much would I have watched disappear before it
recovered?"*

**Why it matters more than volatility to real humans:** volatility is
abstract. A 35% drawdown is the number that makes people panic-sell at the
bottom. It's the emotional-tolerance metric.

---

### Value at Risk (VaR 95)

**In plain English:** *"on a bad day, how bad?"*

We take every daily return in the period, line them up worst to best, and read
off the 5th percentile. If VaR₉₅ is −2.3%, then on the worst 1-in-20 days,
you'd expect to lose **at least** 2.3%.

**The trap to be honest about:** VaR tells you the *threshold*, not the worst
case. On that bad 1-in-20 day you could lose 2.3% or 15% — VaR doesn't
distinguish. It's a floor for bad days, not a ceiling on disaster.

---

### Calmar ratio

**In plain English:** return divided by your worst drawdown. *"Did the eventual
gain justify the scariest moment?"* Higher is better.

---

### Tracking error

**In plain English:** how far you drift from the index. Near zero means you're
basically an index fund. Large means you've made genuinely different bets — for
better or worse.

---

### Risk vs Return scatter

**In plain English:** the single most useful chart we have.

- **Left/right** = risk (volatility). Further right = bumpier.
- **Up/down** = return. Higher = better.
- **Bubble size** = how much money you have in it.

**How to read it in one sentence:** you want bubbles **up and to the left** —
high return for low risk. A big bubble **down and to the right** is your
problem child: lots of money, lots of risk, poor return.

**The honesty note:** bubble size is *position value*, not a risk measure.
We say so on screen so nobody misreads a big bubble as "big risk."

---

### Correlation matrix

**In plain English:** do the things you own move *together*?

| Correlation | Means |
|---|---|
| +1.0 | Move in perfect lockstep |
| 0 | Unrelated |
| −1.0 | Perfect opposites |

**Why this is the most underrated panel in the app:** you can own fifteen
different stocks and still own **one bet**. If you hold TCS, Infosys, Wipro and
HCL, that's four tickers and one bet on Indian IT. When IT falls, all four
fall together, and your "diversification" evaporates exactly when you needed
it.

The diagonal is always 1.0 (everything correlates perfectly with itself) — the
value is entirely in the **off-diagonal** pairs you *thought* were different.

---

## TAB 3 · Performance

### Benchmark comparison

**In plain English:** would you have done better just buying the index and
going to sleep?

We plot you against **Nifty 50, Sensex and gold**, all real fetched data.

**The "rebased to 100" trick:** the Nifty is at ~23,000 and your portfolio is
₹1 lakh. Plotting both raw would be unreadable. So we set *everything* to 100
at the start of the period and track growth from there. Now a line at 112
means "up 12%", whatever it started at, and all lines are directly comparable.

**Time-weighted — the important subtlety.** If you deposit ₹50,000, your
portfolio value jumps. That is **not performance**, it's you adding money. A
naive chart would show a spike and flatter you. We use a *time-weighted*
return, which strips out deposits and withdrawals so the line only reflects how
your investments actually performed. That's what makes it fair to compare
against an index.

**FD and inflation lines:** these are **labelled assumptions** (default 7% and
6%), user-editable, and marked as such on screen. There is no free API for
"the" FD rate — it varies by bank and tenure. We'd rather label an assumption
than fake a data feed.

---

### Portfolio statistics

Plain facts about how you've actually behaved:

- **Win rate** — what fraction of your holdings are in profit. *We exclude
  unpriced holdings*, because a holding we couldn't price sits at exactly zero
  P/L and would sneak in as a fake break-even.
- **Average holding period** — are you an investor or a day trader?
- **Turnover** — how much you've sold relative to portfolio size. High turnover
  means lots of churn, which usually means lots of fees.
- **Best / worst performer**, largest single realised gain and loss.

---

## TAB 4 · Projections

### Monte Carlo — the crown jewel

**In plain English:** we can't predict next year. But we can ask *"if the
future rhymes with the past, what's the realistic range?"*

**How it works, as a story:**
> Write every daily return your portfolio has had on a separate slip of paper.
> Put them in a hat. Draw one, note it, **put it back**. Draw again. Do this
> 252 times — that's one imaginary year.
>
> Now do that whole thing **1,000 times.**
>
> You get 1,000 possible futures. Sort them. The middle one is your median
> case; the 10th and 90th percentiles give you a realistic band.

That's the fan chart on screen — a spread of outcomes that widens with time,
because the further out you look, the less you know.

**Why "put it back" (with replacement) matters:** it lets any day follow any
other day, generating combinations you haven't literally lived through, while
keeping the *character* of your actual returns.

**The thing that makes ours better than most:** we do **not** assume a normal
distribution (the bell curve). Real markets have fat tails — extreme days
happen far more often than a bell curve predicts. By resampling *your actual
history*, the crashes stay in the hat.

**How to read it honestly:** it is **not a prediction**. It's a range built
from what your portfolio has already genuinely done. If the last year was
unusually calm, the fan will be unrealistically narrow.

Defaults: 1,000 simulations, 252 days. Range: 100–2,000 sims, up to ~10 years.

---

### Rebalancing simulator

**In plain English:** a what-if machine. *"What if I moved to 20% in each of
five things — would I be less risky?"*

You give it hypothetical weights, and it recomputes your risk and health at
those weights using the same historical returns.

**Say this out loud:** nothing is saved, no trade is placed, your portfolio is
untouched. It's a calculation, not a rebalance.

---

### Goals

**In plain English:** name a target — "₹5,00,000 for a car" — and track
progress as `current value ÷ target`.

**Deliberately limited:** goals are *not* linked to specific holdings, and we
don't track your salary, loans or net worth. That's a different product. We
chose the small honest version over the sprawling one.

---

## TAB 5 · Activity

**Cash flow** — where money moved: deposits in, buys out, dividends back in.

**Timeline** — everything you've done, in order.

**The point to close on:** this tab is the *input* that every other tab was
derived from. Delete it and the whole app has nothing to say. That's the golden
rule made visible.

---

# Part 3 — Questions you'll get

## The basics

**Q: What is volatility, in one sentence?**
How much the price bounces around. High volatility = big swings in both
directions. It measures uncertainty, not losses.

**Q: What's a good Sharpe ratio?**
Above 1 is genuinely good. Zero to one means you beat the FD but not
impressively. Negative means you'd literally have been better off in a fixed
deposit.

**Q: Our Sharpe is negative. Isn't that bad?**
It's an accurate answer, and that's the point. For this period, the return
didn't beat a 6.5% risk-free rate. A metric that only ever produces flattering
numbers isn't measuring anything.

**Q: What's the difference between volatility and drawdown?**
Volatility is the average bumpiness over the whole period. Drawdown is the
single worst fall from a peak. Volatility is statistical; drawdown is
emotional — it's the number that makes people sell at the bottom.

**Q: Beta of 1.2 means what?**
When the Nifty moves 10%, this tends to move 12% — in both directions.

**Q: What does a correlation of 0.9 mean?**
Those two holdings move almost identically. You think you own two things; you
effectively own one.

**Q: Why is the diagonal of the correlation matrix always 1?**
Everything correlates perfectly with itself. It carries no information — all
the value is off the diagonal.

---

## Methodology

**Q: Where does the data come from?**
Stock prices from yfinance, mutual fund NAVs from mfapi.in. We cache daily
closes in our own database and compute everything from that cache. Charts never
hit the live API — that would get us rate-limited immediately.

**Q: Why 252?**
Trading days in a year — 365 minus weekends and market holidays. It's the
standard convention for annualising daily figures.

**Q: Why is the risk-free rate 6.5%?**
It's a reasonable Indian government-bond / FD rate. It's an input, not a
hardcoded truth — you can change it.

**Q: Why do you need 30 observations minimum?**
Because a Sharpe ratio computed from six days of data is noise wearing a
statistic's clothing. Below 30 daily returns we exclude the holding and *say
we excluded it*, rather than printing a confident-looking wrong number.

**Q: Do you store these calculated numbers?**
No — everything is computed per request. If we stored them, they could drift
out of sync with the transactions and prices they came from. The only things
we store are what you did, and what the market did.

**Q: Isn't this just textbook formulas anyone could copy?**
The formulas are standard, deliberately — we didn't invent our own definition
of Sharpe, because a non-standard Sharpe would be useless. The engineering is
in everything around them: caching price history so it's fast, handling missing
data honestly, minimum-observation thresholds, dropping unmeasurable components
and renormalising, and never storing a derived number where it could drift.

**Q: How do I know your maths is right?**
There are 84 automated tests, and the calculation logic is the most heavily
tested part of the codebase — because it's the highest-risk code in the app. We
also deliberately chose `pyxirr` over `numpy_financial` for XIRR: the numpy one
assumes evenly spaced periods and returns a quietly wrong answer on real
irregular investment dates.

---

## Interpretation

**Q: My health score is 64. What do I actually do?**
Look at which component is dragging. The panel breaks it into all four. If
sector balance is low, you're concentrated in one industry. If cash reserve is
low, you're fully invested with no buffer. The score points at a cause, not
just a grade.

**Q: I own 15 stocks. Am I diversified?**
Check the correlation matrix, not the count. Fifteen IT stocks is one bet.
That's precisely the question that panel exists to answer.

**Q: Should I sell my worst performer?**
We don't answer that — deliberately. Everything here is framed as
informational, not advice. We show you what's true; the decision is yours.

**Q: The Monte Carlo says I could have ₹80k or ₹1.5L. That's a huge range.**
Yes — and that's the honest answer. Anyone giving you a single confident number
for next year is making it up. The width of the fan *is* the information.

---

## Skeptical / hard questions

**Q: How is this different from what Groww or Zerodha already show?**
Consumer apps show you returns and allocation. They generally don't show risk-
adjusted metrics, correlation, Monte Carlo, or a transparent composite score.
And where they do show a score, the recipe is hidden. Ours is on screen with
its weights.

**Q: Isn't Monte Carlo just random numbers?**
It's random *sampling from your real returns*, which is different. We're not
inventing numbers — we're reshuffling the ones your portfolio actually
produced, to see what other orderings would have looked like.

**Q: What if my portfolio is brand new with no history?**
Then several metrics genuinely can't be computed, and we say so rather than
guessing. The health score drops the volatility component and renormalises the
other three. The risk tab excludes holdings under 30 observations and lists
them as excluded.

**Q: Your demo data is seeded. Is any of this real?**
The pipeline is entirely real — live NSE search, real yfinance and NAV feeds,
full history backfill on first use. We seed a *deterministic* demo portfolio so
every person who clones the repo sees identical numbers, which makes it
reproducible. One command reproduces this exact screen.

**Q: Why not just use a library like PyPortfolioOpt?**
We wanted to understand and be able to defend every number. Also the rest of
the app computes its statistics in plain Python, so this is consistent with
how it already works. We deliberately did *not* attempt full efficient-frontier
optimisation — that's easy to get subtly wrong and we'd rather ship less that's
correct.

**Q: What's the weakest part of the analytics?**
Everything is backward-looking. Volatility, beta, correlation — all describe
what already happened. Correlations in particular tend to spike toward 1 during
a crash, which is exactly when diversification is supposed to help. We'd rather
state that than pretend these are forecasts.

**Q: Could someone lose money trusting these numbers?**
The numbers are descriptive, not prescriptive — and every panel carries that
framing on screen. We never say buy or sell. That's a deliberate product
decision, not a limitation we ran out of time to fix.
