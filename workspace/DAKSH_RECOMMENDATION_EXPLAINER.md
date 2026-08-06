# The recommendation engine, explained like you've never trained a model
### Daksh's prep sheet · Investrix · Team ChequeMate

Written for someone with zero machine-learning background. If a judge asks you
something, the plain-English answer is usually the *best* answer — not the most
technical one.

**The one-line version:**
> We look at every Nifty 50 stock you don't already own, score each one out of
> 100 on four separate things — how well it fits you, its recent trend, its
> news tone, and what a neural network predicts about its price — then blend
> those four into a ranking and **show you exactly how each score was made.**

---

# Part 1 — Why this is hard, and what we chose

## "Recommend me a stock" is not one question

This is the insight the whole design rests on, and it's a great thing to open
with.

Three different people asking the same words want three different things:

- *"I like what I own. Give me more of that."*
- *"I'm too concentrated. Give me something different."*
- *"I have nothing yet. Where do I even start?"*

One ranked list cannot answer all three. So we built **three modes**, and let
you pick the question.

## Why we don't just rank by "best stock"

There's no such thing as a best stock independent of who's asking. A high-
growth, high-volatility mid-cap is excellent for a 25-year-old with a 30-year
horizon and terrible for someone retiring in two years. **The portfolio you
already own is context**, and any recommender that ignores it is just a
leaderboard.

---

# Part 2 — Our journey: random forest → GRU/LSTM

Judges like hearing that you tried something, learned why it was wrong, and
moved. Tell it as a story.

## Where we started: Random Forest

**What a random forest is, in plain English:**
> Imagine asking 100 people to guess whether a stock goes up tomorrow. Each
> person gets to ask a few yes/no questions first — "Is the P/E under 20?" "Was
> yesterday green?" "Is volume above average?" — and then votes. You take the
> majority vote.
>
> Each person is a **decision tree**. The crowd of them is a **random forest**.

It's a genuinely good, fast, well-understood model. It ran fine.

## Why we moved away from it

**A random forest has no memory.**

It sees each day as an independent row in a spreadsheet — today's P/E, today's
volume, today's price. It has no notion that yesterday came before today, or
that the last ten days formed a pattern.

But **price movement is nothing but sequence.** "Rose steadily for ten days"
and "crashed then recovered to the same price" produce an identical row in a
spreadsheet and mean completely different things. A model with no memory
literally cannot tell them apart.

That's not a tuning problem. It's the wrong shape of model for the data.

## Where we landed: recurrent networks

**What "recurrent" means, in plain English:**
> A normal network sees one snapshot and answers. A **recurrent** network reads
> a sequence one step at a time, and carries a running summary — a memory —
> forward as it goes.
>
> Like reading a sentence. By the time you reach the last word, you're still
> holding the first one in your head. That carried-forward state is what lets
> it understand *order*.

We use two of them:

| Model | Reads | Predicts | Parameters |
|---|---|---|---|
| **GRU** | 90 days of data | tomorrow's close | **718,081** |
| **LSTM** | 90 days of data | the next **5 days** as a path | **958,325** |

About **1.7 million trained parameters** between them.

## LSTM vs GRU — the honest difference

**LSTM (Long Short-Term Memory)** has three "gates" — small internal switches
that learn what to remember, what to forget, and what to output. It's the older
and more powerful design.

**GRU (Gated Recurrent Unit)** is a streamlined version with two gates instead
of three. Fewer parameters, faster, often just as good on shorter sequences.

**Why we use both:** the GRU handles the 1-day horizon — sharper, but noisier.
The LSTM handles the 5-day path — noisier day-to-day, but it carries more
signal about *direction*. We blend them **40% GRU, 60% LSTM**, giving the
longer view the bigger vote.

## What the model actually eats

Not a single price — a **window**:

```
90 trading days × 6 features  =  the input shape

The 6 features: Open · High · Low · Close · Adjusted Close · Volume
```

Every number is squashed to a 0–1 range within that window (**min–max
normalisation**) because networks learn badly on raw numbers where one column
is ₹3,000 and another is 2 million shares. After it predicts, we invert the
squashing to get back to rupees.

---

# Part 3 — The three modes (the "three corners")

**▸ Demo tip:** click each tab as you name it.

## 1. Similar — "more of what I already like"

**In plain English:** we work out the average financial character of your
holdings, then find stocks closest to that.

**How:** each stock becomes a list of five numbers —

```
P/E ratio · beta · dividend yield · profit margin · return on equity
```

We compare candidates to your portfolio's average using **cosine similarity**.

**Cosine similarity, in plain English:**
> Forget the maths. It measures whether two things point in the *same
> direction*, ignoring how big they are.

**Why "ignoring how big" is the whole trick:** we z-score every feature first
(rescale so each sits on a comparable scale). That means a ₹5,000-crore
company and a ₹5-lakh-crore company with the same financial *character* —
similar margins, similar valuation, similar payout — score as similar.

**It compares style, not size.** That's the sentence to say.

## 2. Complementary — "fix my blind spot"

**In plain English:** the opposite. It looks at what you're *missing*.

- Scores the **sector gap** — if you're 45% technology, other tech stocks score
  badly here and pharma or FMCG scores well
- Rewards **lower beta** than your portfolio average — a steadying influence
- Small **dividend bonus**

The gap is **value-weighted**, so it reflects where your *money* is, not how
many tickers you happen to own.

**A real bug we fixed here, worth telling:** early on, HCLTECH ranked #3 as a
"diversifier" for a portfolio that was already 45% technology. The cause was
that our seed data labelled the sector "IT" while the market API returned
"Technology" — two names for one sector, so the system thought IT was a gap.
We built an alias map to collapse them. **After the fix HCLTECH dropped from
#3 to #6.** Finding that required actually reading the output against a real
portfolio instead of trusting that it worked.

## 3. Risk profile — "I'm new, where do I start?"

**In plain English:** a readable rule table, from conservative to aggressive.
No holdings needed at all.

This solves **cold-start** — the classic recommender problem where a brand-new
user with no history gets nothing useful.

Roughly what the rules reward:

| Profile | Looks for |
|---|---|
| **Conservative** | P/E under 15, beta under 0.8, dividend above 2% |
| **Balanced** | P/E under 30, beta under 1.3, margin above 10% |
| **Assertive** | P/E 15–50, beta 1.0–1.8, margin above 15% |
| **Aggressive** | P/E above 20, beta above 1.2, ROE above 15% |

**Why rules and not ML here?** Because it must work with **zero** data about
the user. There's nothing to learn from. And a readable table is something you
can inspect and disagree with — which is better than an unexplainable model for
someone's first ever investment decision.

---

# Part 4 — The blend

Every candidate gets four independent scores out of 100:

| Component | Weight | What it measures |
|---|---|---|
| **Fit** | **40%** | How well it matches your chosen mode |
| **Momentum** | **20%** | Recent 30-day trend vs the prior 60 days |
| **Sentiment** | **15%** | Tone of cached news headlines |
| **ML forecast** | **25%** | What the GRU + LSTM predict |

```
final score = Σ(weight × score) ÷ Σ(weights)   — over components that have data
```

## The "renormalise" bit — say this one out loud

If a stock has no news coverage, we **drop the sentiment component and
redistribute its weight** across the other three.

**The lazy alternative** is filling the gap with a neutral 50. That sounds
harmless and is actually corrosive: it silently drags every poorly-covered
stock toward the middle of the ranking, and you can never tell whether a 50
meant "genuinely average" or "we had no idea."

A missing signal should **widen your uncertainty, not fake a measurement.**

## Turning a prediction into a score

The model outputs a predicted price. We convert to expected return, then map to
0–100 with a **tanh** curve:

```
score = 50 × (1 + tanh(expected_return ÷ scale))
```

**Why tanh and not a straight line:** it's sensitive in the middle and
saturating at the edges. The difference between +1% and +2% still moves the
needle, but a +40% prediction — almost certainly a data glitch — can't hijack
the entire ranking.

**A calibration bug we found and fixed:** we originally used the same scale for
the model and the momentum fallback. But momentum measures *trend acceleration
over months* (swings of tens of percent), while a 1-day prediction swings by
ones. Using one scale pinned almost every stock to 0 or 100. We now use
**scale 3 for model returns and 15 for momentum**, and the scores spread
properly.

## Confidence label

| Label | When |
|---|---|
| **High** | ≥85% of the blend had real data, *and* the ML model ran |
| **Medium** | ≥60% coverage |
| **Low** | below that |

It tells you how much of the score was actually backed by data rather than
inferred from a thin slice.

---

# Part 5 — The engineering story (your best moment)

**The problem:**
The trained models are Keras 2.6 `.h5` checkpoints. Two independent blockers:

1. **TensorFlow publishes no wheels for Python 3.14.** `pip install tensorflow`
   returns *"no matching distribution"*.
2. **Keras 3 refuses the file format.** TF ≥ 2.16 ships Keras 3, which won't
   load a Keras 2.6 HDF5 layout at all.

So using TensorFlow meant pinning a legacy version **and** downgrading the
whole interpreter, for one component worth 25% of one feature.

**What we did instead:**
Read the trained weight tensors straight out of the HDF5 file with `h5py`, and
**reimplemented both forward passes in NumPy ourselves.**

- These are the **real trained weights** — nothing approximated
- ~**30 milliseconds** per stock
- **1 MB** dependency instead of ~500 MB
- Works on any modern Python

**The detail that proves we understood it:** the GRU uses `reset_after=False`
with `hard_sigmoid` gates — the older pre-cuDNN formulation, where the reset
gate multiplies the hidden state *before* the recurrent matrix multiply. Get
that backwards and you get numbers that look completely plausible and are
silently wrong. We read the setting out of the checkpoint config rather than
assuming, and verified our recovered parameter counts match the file exactly:
718,081 and 958,325.

---

# Part 6 — Being honest about limits

**Lead with this before a judge finds it.** Volunteering your own weakness is
the strongest move you have.

- The checkpoints were **trained on a single airline's price history** and
  applied to Indian equities **without retraining**. They are not a market
  oracle.
- That is precisely **why the model is capped at 25%** and never decides
  anything alone.
- The training scaler wasn't shipped with the checkpoints, so we reconstruct
  the standard per-window normalisation. Absolute price predictions carry more
  uncertainty than the model's own training error would suggest.
- We frame everything as **educational**, never advice. The app never says buy
  or sell.

---

# Part 7 — Questions you'll get

## The basics

**Q: What's the difference between LSTM and GRU, simply?**
Both read sequences and carry memory. LSTM has three internal gates deciding
what to remember, forget and output. GRU is a streamlined two-gate version —
fewer parameters, faster, often just as good. We use GRU for the 1-day
prediction and LSTM for the 5-day path.

**Q: What's a "parameter"?**
A number the model learned during training. Ours have about 1.7 million between
them. More parameters means more capacity to capture patterns — and more
capacity to memorise noise.

**Q: What does the model actually see?**
90 trading days of six values each — open, high, low, close, adjusted close,
volume — all scaled to 0–1 within that window.

**Q: Why 90 days?**
That's what the checkpoints declare as their input shape. We read it from the
file rather than choosing it. Feeding a different shape would error on every
call.

**Q: What does it predict?**
The GRU predicts tomorrow's closing price. The LSTM predicts five days as a
path. We convert both into expected *returns* versus today's close, because a
predicted price level on its own doesn't tell you whether to be interested.

---

## Methodology

**Q: Why these four components and those weights?**
Fit gets the most (40%) because matching your actual portfolio is the point of
a *recommender* rather than a screener. ML gets 25% — meaningful but never
decisive, given the training limitation. Sentiment gets least (15%) because
headline tone is the noisiest signal we have.

**Q: Are the weights tuned or chosen?**
Chosen, deliberately, and we say so. We don't have the labelled outcome data
you'd need to tune them honestly. Inventing a backtest to justify numbers we
picked by judgement would be worse than admitting we picked them.

**Q: Why cosine similarity instead of plain distance?**
Because distance is dominated by scale. Cosine compares direction, and after
z-scoring it captures *style* — so a mid-cap and a large-cap with the same
financial character look similar, which is what a human means by "similar."

**Q: How do you handle missing data?**
Drop the component and renormalise the remaining weights. Never impute a
neutral 50 — that would silently drag poorly-covered stocks toward the middle
and make a 50 ambiguous between "average" and "unknown."

**Q: How long does it take?**
About 10 seconds for a cold first call — fetching fundamentals for the whole
candidate universe, then running both networks per candidate. Cached for 15
minutes after. The loading screen narrates the real pipeline stages so it
doesn't look frozen.

**Q: Why not use a pre-trained financial model?**
The models came from a teammate's earlier workstream — working with what the
team had built was part of the exercise. And we're explicit that they're
trained on the wrong domain rather than quietly hoping nobody asks.

---

## Skeptical / hard questions

**Q: Does it actually work? What's the accuracy?**
We don't claim predictive accuracy, and we'd be suspicious of anyone who does
after a hackathon. The models were trained on one airline and applied to Indian
equities without retraining. What we *can* defend is that the networks run
correctly on real trained weights — verified parameter counts, verified
directional response — and that the system is honest about how much it's
trusting them: 25%, capped.

**Q: So why include ML at all if you don't trust it?**
Because 25% of a transparent blend is exactly the right amount of trust for a
weak signal. The alternative designs are worse: pretend it's accurate, or drop
it and lose a genuine signal. We show its contribution on every card so you can
see precisely how much it moved the ranking.

**Q: Isn't this just a stock screener with extra steps?**
A screener filters on absolute thresholds — "P/E under 20." This scores
*relative to your portfolio*: the same stock ranks differently depending on
what you own and which question you asked. A screener has no idea who you are.

**Q: Couldn't someone lose money following this?**
Every score is educational and decomposed on screen; the app never says buy or
sell, and nothing places an order. That's a deliberate product decision. We'd
rather show our reasoning and let you disagree than deliver a verdict you
can't inspect.

**Q: What happens if the models fail to load?**
It degrades to a momentum estimate computed from our own cached price history,
and the UI banner says explicitly which path is live. It never presents a
fallback as a model prediction.

**Q: You reimplemented a neural network yourself — how do you know it's right?**
Three checks. Our recovered parameter counts match the checkpoints exactly
(718,081 and 958,325). The networks respond correctly to input direction —
rising inputs produce high outputs, falling inputs low, flat inputs near the
middle. And we read the gate configuration out of the model config rather than
assuming it, because `reset_after=False` versus `True` is precisely the kind of
mistake that produces plausible wrong answers.

**Q: What would you do with another week?**
Retrain on Indian equities — that's the honest weak point and everything else
is downstream of it. Then walk-forward backtesting to actually measure whether
the ranking beats a random pick, which is the evaluation we currently can't
claim.

**Q: Why three modes instead of one good one?**
Because "recommend me a stock" is three different questions depending on
whether you want more of what you have, coverage of what you lack, or a
starting point from nothing. One list answering all three would answer none of
them well.

**Q: How is this different from what Groww shows?**
Consumer apps mostly show popularity or broker research. Ours scores against
*your* portfolio, in three different framings, and decomposes every score on
screen. You can see exactly why something ranked where it did — and disagree
with it.
