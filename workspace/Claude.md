# Portfolio Manager — Project Context (CLAUDE.md)

This file is the single source of truth for the project. Place it at the **repo root**
(or at the root of `backend/` and `frontend/` if you split into two repos — copy it to
both). Claude Code reads it automatically at the start of every session. Do not delete
sections; extend them as decisions are made.

---

## 0. Changelog — what was fixed vs. the original spec, and why

The original design doc was ~90% solid (the 3-layer architecture and the DB schema
were good instincts) but had gaps that would have caused real problems mid-build.
Fixed here so Claude Code never has to guess:

1. **Chart library "Recharts (or Chart.js)" → Recharts, decided.** An "or" in a spec
   is a landmine for an agent — it'll pick differently in different sessions.
2. **"yfinance for prices" applied to Mutual Funds → wrong.** yfinance has no
   reliable NAV data for Indian mutual fund schemes. Swapped to **mfapi.in** (free,
   no key, AMFI-sourced) for MF NAV and history. yfinance is now scoped to
   **stocks only**.
3. **Bonds had no real data source at all.** There is no free live API for Indian
   retail bond pricing. Bonds are now explicitly **manual-price** assets (see §4, §5).
   This was silently assumed symmetric with stocks/MF in the original doc — it isn't.
4. **News API was mentioned but never designed.** Added a real provider choice, a
   cache table, and explicit "never store full article bodies" rule (copyright +
   DB bloat).
5. **Live-fetching full price history on every chart request** (original §7.8) would
   get rate-limited fast — yfinance's unofficial endpoints throttle aggressively in
   2026, and mfapi.in explicitly asks callers to cache. Added a `price_history` cache
   table populated by a sync job instead of fetching live on every page load.
6. **No frontend project structure** (backend had one, frontend didn't). Added one,
   including a data-fetching strategy — the original doc never said how the React
   app talks to the API day-to-day (added React Query).
7. **No design system** — the original layout was pure ASCII wireframe with no
   color, type, or motion spec, but the brief asks for a modern black-theme UI with
   animation. Added §8 to close that gap so every phase inherits the same look
   instead of retrofitting styling at the end.
8. **Currency inconsistency** — schema defaulted `currency` to `'USD'`, mockups used
   `$`, but every data source (mfapi.in, NSE via yfinance, Groww/Zerodha as visual
   references) is India-first. Base currency is now **INR (₹)**. Non-INR holdings
   (e.g. a US stock via yfinance) are a valid edge case, not the default — see §4.
9. **No home for the intelligence/recommendation layer** in the phase list. Added it
   explicitly as the **last** phase — see §12 — per your instruction, with guardrails
   in §13 so it doesn't accidentally read as real financial advice.
10. **Flasgger vs flask-smorest** left open — decided **flask-smorest**, since it's
    built on Marshmallow and the original folder structure already has a
    `schemas/ # marshmallow + swagger` directory. flask-smorest gives you both from
    one schema definition instead of hand-written swagger decorators.

### 0.1 — v2 update (scoped in after Prompt 5 was built)

Once holdings CRUD + analytics were actually running, it became clear the MVP
simplification (direct-edit holdings, a small fixed seed catalog) doesn't read as a
*real* portfolio app. These land right at the natural seam before transactions (old
Phase 6) — nothing already built gets thrown away, Phase 6 just grew:

11. **Holdings were directly editable (quantity/avg_buy_price via PUT).** Real
    brokerage/investment apps never let you do this — a holding is a *result* of
    buying and selling, not a row you hand-edit. `POST`/`PUT /api/portfolio` are
    removed; holdings are now created, grown, shrunk, and deleted automatically by
    `/api/transactions` (BUY creates/increases, SELL decreases/removes at zero). See
    §5.2, §7.
12. **No wallet/cash concept.** Every real portfolio app has a cash balance you fund
    before you can buy. Added `wallet_ledger` (§5.2) — balance is `SUM(amount)`,
    never a separately-stored mutable field, consistent with the doc's own golden
    rule in §1. BUY debits it, SELL/DIVIDEND credit it; a BUY that would overdraw it
    is rejected.
13. **Asset catalog was a small fixed seed list.** Fine for early dev, but "like
    Groww" means picking from a real universe of thousands of stocks/MF schemes,
    not 15 pre-loaded rows. Added a live search + on-demand creation flow (§4.1) —
    Phase 2's seed data becomes a *starter* set, not the ceiling.
14. **Chart set was too thin for "many interactive charts."** Recharts alone doesn't
    do candlesticks well. Added **lightweight-charts** (TradingView's own
    open-source charting lib) for price/candlestick charts specifically, plus named
    comparison-overlay, sparkline, and allocation-treemap components — see §8.5, §9.

### 0.2 — v2.1 update (historical depth + calculators)

15. **Period buttons (1D/1W/1M/6M/1Y/3Y/5Y/ALL) needed a real data strategy, not
    just a UI row.** Added §4.2 mapping each period to what's actually fetchable
    from yfinance/mfapi.in, plus a one-time backfill-on-resolve so charts read from
    `price_history` instead of live-calling on every view.
16. **Added a Calculators feature** (new Phase 9, §6.11–§6.13, §7) — a Groww-style
    "what would I have made" toolset: a Historical Returns Calculator (lumpsum
    backtest at a real past price), and a SIP Calculator with both a projected mode
    (assumed rate) and a historical-backtest mode (real monthly prices), plus a
    Step-up/Top-up SIP variant. These are stateless read-only calculations — they
    reuse `price_history` and `pyxirr`, they don't add new source-of-truth tables.
    Roadmap renumbered from here: old Phase 9 (Watchlist/SIPs/tags/search) → 10,
    old 10 (News) → 11, old 11 (Home) → 12, Recommendation layer stays **last**,
    now Phase 13.

Everything below reflects these fixes already applied — treat this document as final,
not as a diff.

---

## 1. Product Vision

A single-user portfolio tracker for Stocks, Mutual Funds, and Bonds — visually and
behaviorally in the spirit of Groww / Zerodha Kite, but a **dark, modern trading-app
aesthetic** (near-black surfaces, green/red gain-loss color language, animated
counters and charts) rather than literally cloning either product's branding.

**Explicit non-goals** (say this to Claude Code if it ever drifts):
- No authentication / multi-user support. Single user, no login.
- No real order execution, no real money movement, no broker integration.
- No real-time tick-by-tick streaming. End-of-day / periodic sync is enough.
- No ML/AI recommendation engine until every other phase is done (§12, §13).

**Golden rule (kept from original doc):**
> Store what the user does. Fetch what the market is. Calculate the rest.

---

## 2. Tech Stack (decided — no open choices remain)

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11+ / Flask | REST-only API, no server-rendered templates → Flask's minimalism fits better than Django here; team is small enough that Django's extra structure isn't paying for itself. |
| API docs / validation | flask-smorest (Marshmallow-based) | One schema → validation + serialization + OpenAPI docs. Resolves the Flasgger/flask-smorest ambiguity in the original doc. |
| ORM / migrations | SQLAlchemy + Flask-Migrate (Alembic) | Standard, matches original model folder structure. |
| DB | PostgreSQL (prod), SQLite (local dev) | As originally specified. |
| Scheduling | APScheduler (in-process) | Periodic price/NAV sync without adding infra (Celery+Redis is overkill for a single-user app). |
| Caching | Flask-Caching (SimpleCache locally; can swap to Redis later) | For news + hot price reads. |
| Frontend | React 18 + Vite | Original doc said React; Vite over CRA for speed. |
| Styling | Tailwind CSS + CSS variables for theme tokens | See §8. |
| Charts | **Recharts** + **lightweight-charts** (v2, candlesticks only) | Recharts for donut/bar/area/sparkline/KPI-adjacent charts. Added TradingView's open-source `lightweight-charts` specifically for the Asset Detail price/candlestick chart — Recharts has no real candlestick support and this is the one place it matters. Free (Apache-2.0), needs a small attribution notice/link to tradingview.com on the page — see §8.5. |
| Motion | Framer Motion | Page transitions, card hover states, animated modals. |
| Server state | @tanstack/react-query | Caching, refetching, loading/error states for every API call — the original doc never specified this and it's the backbone of a data-heavy dashboard. |
| Forms | react-hook-form + zod | Add/Edit holding, transaction, SIP forms. |
| Icons | lucide-react | Clean, consistent, matches a fintech-dark aesthetic. |
| Toasts | sonner (or react-hot-toast) | Non-blocking feedback on CRUD actions. |
| XIRR/XNPV | **pyxirr** (Rust-backed) | Correct handling of irregular real dates — `numpy_financial.irr` assumes evenly spaced periods and will silently give wrong answers for real buy/sell dates. This replaces the original doc's "scipy.optimize or numpy_financial" suggestion with a single correct, fast choice. |
| Stock data | yfinance | Stocks only (NSE via `.NS` suffix, BSE via `.BO`). Unofficial/scraped — build for graceful degradation (see §4). |
| MF data | mfapi.in | Free, no key, AMFI-sourced NAV + history. Indian schemes only. |
| Bond data | None (manual entry) | See §4. |
| News | Marketaux (primary) or NewsData.io (fallback) | Finance-tagged free tiers exist on both; pick one, keep the service layer swappable. |

---

## 3. Architecture (3-layer, unchanged in shape, news added)

```
┌──────────────────────────────────────────────────────────────┐
│  REACT FRONTEND (Tailwind, Recharts, Framer Motion, RQ)      │
└───────────────────────────┬──────────────────────────────────┘
                             │ REST / JSON
┌───────────────────────────▼──────────────────────────────────┐
│  FLASK BACKEND                                                │
│   routes → services → models                                  │
│   - portfolio_service   (CRUD: holdings, transactions, sips)  │
│   - analytics_service   (P/L, allocation, XIRR)  ← CALCULATE  │
│   - price_service       (yfinance + mfapi.in + manual, cache) │
│   - news_service        (Marketaux/NewsData.io, cache)        │
└───────┬───────────────────────────────┬──────────────────────┘
        │                               │
┌───────▼─────────┐            ┌────────▼────────────┐
│  YOUR DATABASE   │            │  EXTERNAL APIs       │
│  1. USER DATA    │            │  yfinance (stocks)   │
│  2. CACHE        │◄───sync────│  mfapi.in (MF NAV)   │
│  (disposable)    │            │  Marketaux (news)    │
└──────────────────┘            └───────────────────────┘
```

**Three data layers (unchanged principle):**
1. **USER DATA** (source of truth) → `holdings`, `transactions`, `sips`, `watchlist`, `tags`
2. **CACHE** (disposable, rebuildable) → `asset_metadata`, `price_snapshot`,
   `price_history`, `asset_metrics`, `news_cache`, `fund_houses`, `fund_managers`,
   `*_details`
3. **LIVE API** (never stored beyond the cache tables above) → deep fundamentals,
   long "about" text, similar-asset lookups

---

## 4. External Data Sources — corrected matrix

| Data | Stocks | Mutual Funds | Bonds | Notes |
|---|---|---|---|---|
| Latest price/NAV | yfinance (`.NS`/`.BO`) | mfapi.in `/mf/{code}/latest` | **Manual entry** by user | No free live Indian bond API exists. Don't build one — ask the user to update the price, timestamp it. |
| Price history (for charts) | yfinance `.history()` | mfapi.in `/mf/{code}` (full NAV history) | Flat line from last manual entries, or none | Cache into `price_history`, don't re-fetch full history per page load. |
| Fundamentals | yfinance `.info` | mfapi.in `meta` block (fund house, category, ISIN) | User-entered fields only (coupon, maturity, face value, issuer, rating) | |
| Trending/movers | Computed from your own cached `price_snapshot` day-change | Same | N/A | Cheaper and more reliable than hitting a "trending" endpoint that doesn't reliably exist for India anyway. |
| News | Marketaux/NewsData.io, filtered by ticker/company name | Filtered by fund house / scheme name | General market/bond-market news only | Cache headlines+links only, never full article bodies (copyright). |
| FX (if a non-INR asset is added, e.g. a US stock) | `yfinance.Ticker("USDINR=X")` | N/A | N/A | Base currency for portfolio totals is **INR**. Treat multi-currency as an edge case, not the default path — don't build a full FX engine unless it's actually needed. |

**Resilience rules for `price_service` (important — build this in from day 1, not
retrofitted):**
- Every external call is wrapped with retry + exponential backoff (2–3 attempts).
- On failure, fall back to the last cached `price_snapshot` row and mark the response
  `"stale": true` with the `as_of` timestamp — **never show an error where a slightly
  old number would do**, especially since yfinance's unofficial endpoints do get
  throttled or blocked without warning.
- Batch sync runs on a schedule (APScheduler, e.g. every 30–60 min during market hours,
  once daily off-hours) rather than fetching on every single page load.
- Respect mfapi.in's own request from its docs to cache and not hammer it.

### 4.1 Asset universe: dynamic vs curated (v2)

Stocks and mutual funds are **not** limited to whatever's seeded in the DB — the
catalog grows on demand:

- **Stock search:** `yf.Search(query)` (yfinance's own wrapper around Yahoo's
  unofficial autocomplete endpoint) → filter results to `.NS`/`.BO` symbols. This
  is unofficial/scraped like everything else in yfinance, so cache results briefly
  (a few minutes) and keep a small bundled CSV of ~200–500 well-known NSE symbols
  as an offline fallback so search doesn't go dead mid-demo if Yahoo throttles it.
- **MF search:** mfapi.in's own `/mf/search?q=` — already covers all ~16,000+
  schemes, no fallback needed, it's a real search endpoint, not scraped.
- **Bonds stay curated.** There's no live search API for Indian retail bonds (see
  table above). Keep bonds as a manually-maintained list the user adds to by hand —
  that's a permanent, legitimate difference from stocks/MF, not a gap to close later.
- **Resolve-on-select:** when the user picks a search result not already in
  `asset_metadata`, create it (+ its type-specific `*_details` row + an initial
  `price_snapshot`/`price_history` row) in that moment, then continue into the
  normal BUY flow with the new `asset_id`. See `POST /api/assets/resolve` in §7.
- **Home's "market movers" still doesn't need the whole universe.** Sync a small
  fixed basket (e.g. Nifty 50 constituents) on the regular price-sync schedule
  regardless of what the user actually holds, purely to power a market-wide
  gainers/losers section — see `market_index_constituents` in §5.1. Don't sync
  thousands of tickers just to compute "top movers."

### 4.2 Historical price periods & backfill (v2)

Match Groww-style period buttons to real data behavior — don't fake granularity
that isn't actually there. This applies to the **per-asset** Asset Detail chart
(§7, §8.5). The **portfolio-level** performance chart (§6.8) intentionally skips
intraday — aggregating live intraday across many holdings isn't worth the
complexity, and "today's move" is already on the KPI card — so it only offers
1W/1M/6M/1Y/3Y/5Y/ALL.

| UI period | Stocks (yfinance) | Mutual Funds (mfapi.in) | Served from |
|---|---|---|---|
| 1D | Live intraday call, 5m interval, cached ~5 min | N/A — MF doesn't trade intraday; show latest NAV vs. prev close only (2 points), don't fake a curve | Live, not `price_history` |
| 1W | Last 7 calendar days | Last 7 calendar days | `price_history` cache |
| 1M | Last 1 month | Last 1 month | `price_history` cache |
| 6M | Last 6 months | Last 6 months | `price_history` cache |
| 1Y | Last 1 year | Last 1 year | `price_history` cache |
| 3Y | Last 3 years (consider weekly downsampling for render performance) | Last 3 years | `price_history` cache |
| 5Y | Last 5 years (weekly downsampling) | Last 5 years | `price_history` cache |
| Since inception / ALL | Full available history (monthly downsampling for very long ranges) | Full available history — mfapi.in returns it complete, in one call | `price_history` cache |

**Backfill once, on resolve — not live-fetch-per-view.** When an asset is first
added via `POST /api/assets/resolve` (§4.1), do one deep historical pull and store
all of it in `price_history` in that same request, so every period button above
just queries the cache:
- Stocks: `Ticker(symbol).history(period="max", interval="1d")` — a single call.
- MF: `mfapi.in/mf/{code}` already returns the complete NAV history in one call.
- Bonds: no backfill possible — `price_history` rows only appear when the user
  manually updates the price (one row per manual update).

This backfill is also what makes the Calculators (§6.11–§6.13, §12 Phase 9) work —
they need real historical prices at arbitrary past dates, not just "latest."

---

## 5. Database Schema (PostgreSQL — corrected, single source of truth)

### 5.1 Reference / cache layer

```sql
CREATE TABLE asset_metadata (
    asset_id       BIGSERIAL PRIMARY KEY,
    symbol         VARCHAR(30)  NOT NULL,       -- ticker (stocks), scheme code (MF), ISIN (bond)
    isin           VARCHAR(12)  UNIQUE,
    asset_type     VARCHAR(15)  NOT NULL
                   CHECK (asset_type IN ('STOCK','MUTUAL_FUND','BOND')),
    name           VARCHAR(255) NOT NULL,
    logo_url       VARCHAR(500),
    currency       CHAR(3)      NOT NULL DEFAULT 'INR',
    price_source   VARCHAR(10)  NOT NULL DEFAULT 'LIVE'
                   CHECK (price_source IN ('LIVE','MANUAL')),   -- BONDS = 'MANUAL' always
    last_synced_at TIMESTAMP,
    UNIQUE (symbol, asset_type)
);

CREATE TABLE fund_houses (
    fund_house_id BIGSERIAL PRIMARY KEY,
    name          VARCHAR(150) NOT NULL UNIQUE,
    logo_url      VARCHAR(500),
    website       VARCHAR(255)
);

CREATE TABLE fund_managers (
    manager_id BIGSERIAL PRIMARY KEY,
    name       VARCHAR(150) NOT NULL,
    bio        TEXT
);

CREATE TABLE stock_details (
    asset_id BIGINT PRIMARY KEY REFERENCES asset_metadata(asset_id) ON DELETE CASCADE,
    exchange VARCHAR(20),      -- 'NSE' / 'BSE'
    sector   VARCHAR(100),
    industry VARCHAR(100),
    country  VARCHAR(60)
);

CREATE TABLE mutual_fund_details (
    asset_id      BIGINT PRIMARY KEY REFERENCES asset_metadata(asset_id) ON DELETE CASCADE,
    fund_house_id BIGINT REFERENCES fund_houses(fund_house_id),
    category      VARCHAR(80),
    sub_category  VARCHAR(80),
    plan_type     VARCHAR(10) CHECK (plan_type IN ('DIRECT','REGULAR')),
    option_type   VARCHAR(10) CHECK (option_type IN ('GROWTH','IDCW')),
    expense_ratio NUMERIC(5,2),
    aum           NUMERIC(18,2),
    risk_level    VARCHAR(20),
    benchmark     VARCHAR(120)
);

CREATE TABLE fund_manager_assignments (
    asset_id   BIGINT REFERENCES mutual_fund_details(asset_id) ON DELETE CASCADE,
    manager_id BIGINT REFERENCES fund_managers(manager_id) ON DELETE CASCADE,
    since_date DATE,
    PRIMARY KEY (asset_id, manager_id)
);

CREATE TABLE bond_details (
    asset_id          BIGINT PRIMARY KEY REFERENCES asset_metadata(asset_id) ON DELETE CASCADE,
    issuer            VARCHAR(150),
    coupon_rate       NUMERIC(6,3),
    face_value        NUMERIC(14,2),
    maturity_date     DATE,
    credit_rating     VARCHAR(10),
    payment_frequency VARCHAR(15)
);

CREATE TABLE price_snapshot (
    asset_id       BIGINT PRIMARY KEY REFERENCES asset_metadata(asset_id) ON DELETE CASCADE,
    price          NUMERIC(18,4) NOT NULL,
    prev_close     NUMERIC(18,4),
    day_change     NUMERIC(18,4),
    day_change_pct NUMERIC(8,4),
    is_stale       BOOLEAN DEFAULT FALSE,        -- true if last sync failed and this is a fallback value
    as_of          TIMESTAMP NOT NULL
);

-- NEW: cache of daily closes, so chart/performance endpoints never hit the live
-- API on every request. Populated by the sync job, not on-demand.
CREATE TABLE price_history (
    asset_id    BIGINT NOT NULL REFERENCES asset_metadata(asset_id) ON DELETE CASCADE,
    price_date  DATE NOT NULL,
    close_price NUMERIC(18,4) NOT NULL,
    source      VARCHAR(20),                    -- 'yfinance' | 'mfapi' | 'manual'
    fetched_at  TIMESTAMP DEFAULT now(),
    PRIMARY KEY (asset_id, price_date)
);

CREATE TABLE asset_metrics (
    asset_id     BIGINT REFERENCES asset_metadata(asset_id) ON DELETE CASCADE,
    metric_key   VARCHAR(40) NOT NULL,     -- 'alpha','beta','sharpe','pe','xirr_3y','ytm'
    period       VARCHAR(10),              -- '1Y','3Y','5Y' or NULL
    metric_value NUMERIC(18,6),
    as_of        TIMESTAMP,
    PRIMARY KEY (asset_id, metric_key, period)
);

-- NEW: news cache. Headlines + links ONLY — never full article bodies.
CREATE TABLE news_cache (
    news_id       BIGSERIAL PRIMARY KEY,
    asset_id      BIGINT REFERENCES asset_metadata(asset_id) ON DELETE CASCADE, -- NULL = general market news
    headline      VARCHAR(500) NOT NULL,
    source_name   VARCHAR(120),
    url           VARCHAR(700) NOT NULL,
    published_at  TIMESTAMP,
    sentiment     VARCHAR(10),             -- 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' if provider supplies it
    thumbnail_url VARCHAR(700),
    fetched_at    TIMESTAMP DEFAULT now(),
    UNIQUE (url)
);
CREATE INDEX idx_news_asset      ON news_cache(asset_id);
CREATE INDEX idx_news_published  ON news_cache(published_at);

-- NEW (v2): a small curated basket (e.g. Nifty 50) kept in sync regardless of
-- whether the user holds these — purely to power Home's market-wide movers.
CREATE TABLE market_index_constituents (
    asset_id   BIGINT REFERENCES asset_metadata(asset_id) ON DELETE CASCADE,
    index_name VARCHAR(30) NOT NULL,   -- 'NIFTY50', etc. — supports more than one later
    PRIMARY KEY (asset_id, index_name)
);
```

### 5.2 User (source-of-truth) layer — v2: holdings are now fully derived

```sql
CREATE TABLE holdings (
    holding_id    BIGSERIAL PRIMARY KEY,
    asset_id      BIGINT NOT NULL REFERENCES asset_metadata(asset_id),
    quantity      NUMERIC(18,6) NOT NULL CHECK (quantity >= 0),
    avg_buy_price NUMERIC(18,4) NOT NULL,
    first_bought  DATE,
    notes         TEXT,
    created_at    TIMESTAMP DEFAULT now(),
    updated_at    TIMESTAMP DEFAULT now()
);
-- v2: DERIVED CACHE of transactions, not directly editable. No endpoint sets
-- quantity/avg_buy_price directly — a row appears on first BUY, is recalculated
-- by analytics_service on every later BUY/SELL, and is deleted at quantity = 0.
-- `notes` stays freely editable since it isn't a derived field.

CREATE TABLE sips (
    sip_id       BIGSERIAL PRIMARY KEY,
    asset_id     BIGINT NOT NULL REFERENCES asset_metadata(asset_id),
    amount       NUMERIC(14,2) NOT NULL,
    frequency    VARCHAR(15) NOT NULL
                 CHECK (frequency IN ('DAILY','WEEKLY','MONTHLY','QUARTERLY')),
    start_date   DATE NOT NULL,
    end_date     DATE,
    day_of_cycle SMALLINT,
    is_active    BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMP DEFAULT now()
);
-- Note: SIPs are simulated, not executed. There is no bank auto-debit. A SIP row
-- + a "growth projection" calculation is the entire scope — see §12 Phase 10.

CREATE TABLE transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    asset_id       BIGINT NOT NULL REFERENCES asset_metadata(asset_id),
    holding_id     BIGINT REFERENCES holdings(holding_id) ON DELETE SET NULL,
    sip_id         BIGINT REFERENCES sips(sip_id),
    txn_type       VARCHAR(10) NOT NULL CHECK (txn_type IN ('BUY','SELL','DIVIDEND')),
    quantity       NUMERIC(18,6) NOT NULL,
    price          NUMERIC(18,4) NOT NULL,
    fees           NUMERIC(12,4) DEFAULT 0,
    txn_date       DATE NOT NULL,
    created_at     TIMESTAMP DEFAULT now()
);
-- Every BUY/SELL/DIVIDEND writes a matching wallet_ledger row in the same
-- application-level DB transaction — never let the two drift apart.

-- NEW (v2): cash balance. balance = SUM(amount) over this table — never a
-- separately stored mutable field, per the doc's own golden rule (§1).
CREATE TABLE wallet_ledger (
    ledger_id      BIGSERIAL PRIMARY KEY,
    entry_type     VARCHAR(15) NOT NULL
                   CHECK (entry_type IN ('DEPOSIT','WITHDRAWAL','BUY','SELL','DIVIDEND','FEE')),
    amount         NUMERIC(18,2) NOT NULL,     -- signed: + credit / − debit
    transaction_id BIGINT REFERENCES transactions(transaction_id),
    note           VARCHAR(255),
    created_at     TIMESTAMP DEFAULT now()
);

CREATE TABLE watchlist (
    watchlist_id BIGSERIAL PRIMARY KEY,
    asset_id     BIGINT NOT NULL REFERENCES asset_metadata(asset_id),
    added_at     TIMESTAMP DEFAULT now(),
    UNIQUE (asset_id)
);

CREATE TABLE tags (
    tag_id BIGSERIAL PRIMARY KEY,
    name   VARCHAR(50) UNIQUE NOT NULL
);
CREATE TABLE holding_tags (
    holding_id BIGINT REFERENCES holdings(holding_id) ON DELETE CASCADE,
    tag_id     BIGINT REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (holding_id, tag_id)
);
```

### 5.3 Indexes

```sql
CREATE INDEX idx_txn_asset          ON transactions(asset_id);
CREATE INDEX idx_txn_date           ON transactions(txn_date);
CREATE INDEX idx_holdings_asset     ON holdings(asset_id);
CREATE INDEX idx_metrics_key        ON asset_metrics(metric_key);
CREATE INDEX idx_meta_type          ON asset_metadata(asset_type);
CREATE INDEX idx_price_history_date ON price_history(asset_id, price_date);
CREATE INDEX idx_wallet_created     ON wallet_ledger(created_at);
```

### 5.4 Relationships (v2: two additions, rest unchanged)
- `asset_metadata` 1—1 `stock/mutual_fund/bond_details`
- `mutual_fund_details` N—1 `fund_houses`; M—N `fund_managers`
- `asset_metadata` 1—1 `price_snapshot`; 1—N `price_history`; 1—N `asset_metrics`; 1—N `news_cache`
- `asset_metadata` 1—N `holdings`, `transactions`, `sips`, `watchlist`, `market_index_constituents`
- `holdings` 1—N `transactions`; `sips` 1—N `transactions`
- `holdings` M—N `tags`
- `transactions` 1—1 `wallet_ledger` entry (every BUY/SELL/DIVIDEND writes exactly one ledger row)

---

## 6. Calculations (all in `analytics_service`, never stored, unless noted)

### 6.1 Per-holding
```
invested_value    = quantity × avg_buy_price
current_value     = quantity × current_price
profit_loss       = current_value − invested_value
profit_loss_pct    = (profit_loss / invested_value) × 100
day_change_value  = quantity × price_snapshot.day_change
weight_pct        = (current_value / total_portfolio_value) × 100
```

### 6.2 Portfolio totals
```
total_invested = Σ invested_value
total_current  = Σ current_value
total_pl       = total_current − total_invested
total_pl_pct    = (total_pl / total_invested) × 100
day_pl         = Σ day_change_value
```

### 6.3 Allocation (pie/donut)
```
allocation_by_type[t]   = (Σ current_value where asset_type=t) / total_current × 100
allocation_by_sector[s] = (Σ current_value where sector=s)     / total_current × 100
allocation_by_holding    = each holding's weight_pct
```

### 6.4 Weighted average buy price (recalculated on each BUY)
```
new_avg = (old_qty × old_avg + buy_qty × buy_price) / (old_qty + buy_qty)
# SELL reduces quantity, avg_buy_price unchanged; realised P/L booked separately
```

### 6.5 Realised vs unrealised P/L
```
realised_pl   = Σ over SELLs of (sell_price − avg_buy_price) × sold_qty
unrealised_pl = current profit_loss on remaining quantity
```

### 6.6 XIRR (personal, money-weighted return) — use `pyxirr`, not `numpy_financial`
```python
from datetime import date
from pyxirr import xirr

# BUY  -> negative cashflow (money out)
# SELL / DIVIDEND -> positive cashflow (money in)
# today's current_value -> positive cashflow at t = today
cashflows = [(date(2023, 1, 15), -50000), (date(2023, 7, 1), -30000), (date.today(), 92000)]
result = xirr(cashflows)   # correct with real, irregular dates — no equal-spacing assumption
```
`numpy_financial.irr` assumes evenly spaced periods and will quietly give the
**wrong number** for real buy/sell dates. Don't use it for this.

### 6.7 CAGR (time-weighted, simple)
```
CAGR = (end_value / start_value)^(1 / years) − 1
```

### 6.8 Portfolio value over time (performance chart)
```
For each date D in range:
   value(D) = Σ over holdings [ units_held_on(D) × price_history[asset, D] ]
# units_held_on(D) derived from transactions up to D
# price_history is the CACHED table (§5.1) — never a live external call per request
```

### 6.9 Bond-specific
```
current_yield = (coupon_rate × face_value) / current_price × 100
# current_price here is the user's last MANUAL entry, not a live feed
# YTM: solve numerically the same way as XIRR if you want it — optional, low priority
```

### 6.10 Wallet balance (v2)
```
wallet_balance = Σ wallet_ledger.amount
# BUY      -> amount = −(quantity × price + fees)
# SELL     -> amount = +(quantity × price − fees)
# DIVIDEND -> amount = +dividend_amount
# DEPOSIT / WITHDRAWAL -> user-entered, +/− respectively
# A BUY that would take wallet_balance negative is REJECTED by the API, not clamped.
```

### 6.11 Historical Returns Calculator — "what if I had invested" (v2, Phase 9)
```
units_bought        = amount / price_history[asset, invest_date]   # nearest trading day if exact date missing
current_value       = units_bought × latest_price
absolute_return     = current_value − amount
absolute_return_pct = (absolute_return / amount) × 100
years_held          = (today − invest_date).days / 365
CAGR                = (current_value / amount)^(1 / years_held) − 1
# Single cashflow in, one cashflow out at today -> CAGR and XIRR are equivalent here,
# no need to invoke pyxirr for this one.
```

### 6.12 SIP Calculator — two modes (v2, Phase 9)
```
# Mode A: Projected — assumed annual return, standard forward SIP formula
FV = P × [ ((1 + r)^n − 1) / r ] × (1 + r)
# P = monthly amount, r = assumed monthly rate (annual_rate / 12), n = number of months
# Step-up variant (§6.13): re-apply this formula segment-by-segment across each
# 12-month block with P increased by step_up_pct, then compound forward — no
# closed form needed, a straightforward month-by-month loop is clearer and just
# as fast at this scale.

# Mode B: Historical backtest — uses REAL price_history, no assumed rate
for each month m from start_date to end_date:
    units_bought[m]  = monthly_amount[m] / price_history[asset, purchase_date(m)]
    # monthly_amount[m] = base_amount, or base_amount compounded by step_up_pct
    #                     every 12 months if step-up is enabled (§6.13)
total_units     = Σ units_bought[m]
total_invested  = Σ monthly_amount[m]
current_value   = total_units × latest_price
# Return: feed the real (date, −monthly_amount) cashflows + (today, +current_value)
# into pyxirr.xirr() — same function as §6.6, reused here rather than reinvented.
```

### 6.13 Step-up / Top-up SIP Calculator (v2, Phase 9)
Not a separate engine — it's `step_up_pct` applied to §6.12 (either mode): the
monthly contribution increases by `step_up_pct` every 12 months. Called out as its
own named calculator in the UI (a real, commonly-offered tool) even though it
shares the same backend function with a non-zero `step_up_pct` parameter — don't
build a second calculation engine for it.

---

## 7. REST API Specification

### Core (MVP endpoints)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/portfolio` | List holdings (+ calculated fields) |
| GET | `/api/portfolio/{id}` | One holding |
| ~~POST/PUT/DELETE `/api/portfolio`~~ | — | **Removed in v2.** Holdings are derived from transactions — see below. |
| GET | `/api/health` | Health check |

### Analytics, market, calculators
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/portfolio/summary` | Totals, P/L, day P/L, XIRR |
| GET | `/api/portfolio/allocation?by=type\|sector\|holding` | Pie/donut data |
| GET | `/api/portfolio/performance?period=1W\|1M\|6M\|1Y\|3Y\|5Y\|ALL` | Value-over-time series (from `price_history`; no intraday — see §4.2) |
| GET | `/api/prices/{asset_id}` | Current price/NAV (from cache; `is_stale` flag if fallback) |
| POST | `/api/prices/sync` | Manually trigger a price/NAV sync (also runs on schedule) |
| PUT | `/api/prices/{asset_id}/manual` | Manual price update (bonds; also usable for anything if live sync fails) |
| GET | `/api/prices/{asset_id}/history?period=1D\|1W\|1M\|6M\|1Y\|3Y\|5Y\|ALL` | Chart data — `1D` is a live intraday call (stocks only), everything else from `price_history` (§4.2) |
| GET | `/api/market/movers?scope=portfolio\|index` | **(v2)** `portfolio` = your holdings' day-change; `index` = the curated `market_index_constituents` basket |
| GET | `/api/assets/{asset_id}` | Detail (fundamentals, about) |
| GET | `/api/assets/{asset_id}/similar` | Similar assets (same type + sector/category, simple rule — not ML) |
| GET | `/api/assets/search/live?q=&type=` | **(v2)** Dynamic universe search — `yf.Search` for stocks, mfapi.in `/mf/search` for MF |
| POST | `/api/assets/resolve` | **(v2)** Given a live-search pick, create (or fetch) its `asset_metadata` + details + a full historical backfill into `price_history` (§4.2); returns `asset_id` for the BUY that follows |
| GET/POST | `/api/transactions` | History / **the only way to BUY, SELL, or record a DIVIDEND** — drives holdings + wallet automatically (v2) |
| GET/POST/DELETE | `/api/sips` | SIP plans (simulated, no auto-debit) |
| GET/POST/DELETE | `/api/watchlist` | Bookmarks |
| GET | `/api/search?q=` | Search your *own* `asset_metadata` (already-added assets) — distinct from `/assets/search/live` above |
| GET | `/api/news?asset_id=&limit=` | News feed, general if no `asset_id` |
| GET | `/api/wallet` | **(v2)** Balance + ledger history |
| POST | `/api/wallet/deposit`, `/api/wallet/withdraw` | **(v2)** Add/remove cash (simulated, no real payment) |
| POST | `/api/calculators/historical-returns` | **(v2, Phase 9)** "What if I had invested" lumpsum backtest — §6.11 |
| POST | `/api/calculators/sip` | **(v2, Phase 9)** SIP calculator — `mode=projected\|historical`, optional `step_up_pct` — §6.12, §6.13. Read-only, computes and returns, nothing persisted. |

### Standard error format (unchanged)
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "quantity must be > 0" } }
```

---

## 8. Design System (new — the visual brief in concrete tokens)

**Direction:** modern dark fintech UI — inspired by the *conventions* of apps like
Zerodha Kite's dark mode, TradingView, and Groww's layout patterns (card-based KPIs,
donut allocation, segment tabs), not a literal skin of any one brand's exact logo or
trade dress.

### 8.1 Color tokens (CSS variables — put in `frontend/src/styles/theme.css`)
```css
:root {
  --bg:              #0A0B0F;   /* app background — near-black, not pure #000 */
  --surface:         #12141A;   /* cards, table rows, modals */
  --surface-hover:   #1A1D24;
  --border:           #22252C;
  --text-primary:    #F5F6FA;
  --text-secondary:  #9298A5;
  --text-muted:      #5C6270;
  --accent:          #22D3A6;   /* brand accent — buttons, links, active tab */
  --accent-hover:    #1CBF95;
  --positive:        #16C784;   /* gains — green ticks, up arrows */
  --negative:        #F6465D;   /* losses — red ticks, down arrows */
  --warning:         #F0B90B;
  --radius:          12px;
}
```

### 8.2 Typography
- UI font: **Inter** (or "General Sans" if the team wants something less default).
- Numeric columns (price, P/L, quantity): `font-variant-numeric: tabular-nums;` — this
  is what makes a financial table look professional instead of jittery as numbers
  update.
- Headline weight 600–700, body 400–500. Don't go below 13px for table data on desktop.

### 8.3 Motion principles
- Page/route transitions: fade + 8px slide via Framer Motion, ~200ms.
- KPI numbers animate on load/update (count-up), not just snap to the new value.
- Cards lift slightly (`translateY(-2px)` + subtle shadow) on hover.
- Skeleton pulse loaders for every async panel — never a blank white flash on a dark
  background, it reads as broken.
- Donut/line chart transitions use Recharts' built-in animation, don't disable it.
- Keep motion subtle and fast (150–250ms) — a *trading* app should feel snappy, not
  playful.

### 8.4 Component inventory (build once in Phase 1, reuse everywhere)
`Button`, `Card`, `Modal`, `Input`, `Select`, `Badge` (for gain/loss pills), `Skeleton`,
`Toast`, `Tabs` (segment tabs), `KpiCard` (animated counter + arrow), `DataTable`
(sortable, colour-coded P/L column), `EmptyState`.

### 8.5 Chart library split (v2)
- **Recharts:** allocation donut, sector bar, SIP growth projection, portfolio
  performance area chart, sparklines in table rows.
- **lightweight-charts:** the Asset Detail candlestick/price chart specifically —
  it's the one place a real trading-app chart (crosshair, OHLC tooltip, volume
  histogram, pan/zoom) matters, and Recharts isn't built for it. Add the small
  attribution notice + link to tradingview.com the license requires, in the page
  footer or near the chart — one-time, not a big deal for a college project.
- **Comparison overlay** (asset vs. a benchmark like Nifty 50, or asset vs. asset):
  a Recharts line chart with two series is enough, no need for lightweight-charts.
- **Allocation treemap** (Phase 12 richness): Recharts has a built-in Treemap —
  use it for "allocation by holding" once there are more holdings than a donut can
  read cleanly (roughly >6-8 slices).

---

## 9. Frontend Project Structure (new — original doc had none)

```
frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── package.json
├── src/
│   ├── main.jsx
│   ├── App.jsx                    # React Router setup
│   ├── api/
│   │   ├── client.js               # axios instance, base URL, error interceptor
│   │   ├── portfolio.js
│   │   ├── transactions.js
│   │   ├── prices.js
│   │   ├── news.js
│   │   ├── search.js
│   │   └── calculators.js           # (v2, Phase 9)
│   ├── hooks/                       # useHoldings, usePrices, useDebouncedSearch...
│   ├── components/
│   │   ├── ui/                      # Button, Card, Modal, Skeleton, Toast, Badge, Tabs
│   │   ├── layout/                  # Navbar, PageShell
│   │   ├── charts/                  # PerformanceChart, AllocationDonut, SectorBar,
│   │   │                            # CandlestickChart (lightweight-charts), ComparisonChart,
│   │   │                            # Sparkline, AllocationTreemap                       (v2)
│   │   ├── search/                  # LiveAssetSearch — hits /assets/search/live, feeds Buy modal (v2)
│   │   ├── wallet/                  # WalletBalance, DepositModal, WithdrawModal          (v2)
│   │   ├── calculators/             # HistoricalReturnsForm, SipCalculatorForm (projected/
│   │   │                            # historical toggle), StepUpSipForm, ResultSummary   (v2)
│   │   └── portfolio/               # HoldingsTable, BuyModal, SellModal, KpiCard
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Portfolio.jsx
│   │   ├── AssetDetail.jsx
│   │   ├── Stocks.jsx / MutualFunds.jsx / Bonds.jsx
│   │   ├── Transactions.jsx
│   │   ├── News.jsx                 # (v2) dedicated news page, not just an Asset Detail tab
│   │   └── Calculators.jsx          # (v2, Phase 9) tabs: Historical Returns / SIP / Step-up SIP
│   ├── styles/
│   │   └── theme.css                # §8.1 tokens
│   └── utils/                       # currency/percent/date formatters
```

**Data-fetching strategy:** @tanstack/react-query for every server call — gives you
caching, background refetch, and loading/error states for free instead of hand-rolled
`useEffect` + `useState` on every page. No separate global state manager is needed for
server data; only use local state/Context for pure UI state (e.g. modal open/closed).

---

## 10. Backend Project Structure (kept from original, lightly extended)

```
backend/
├── app.py                 # app factory
├── config.py
├── requirements.txt
├── models/                 # SQLAlchemy models (§5)
├── routes/
│   ├── portfolio.py
│   ├── transactions.py
│   ├── prices.py
│   ├── market.py
│   ├── sips.py
│   ├── watchlist.py
│   ├── news.py              # NEW
│   └── search.py            # NEW
├── services/
│   ├── portfolio_service.py
│   ├── analytics_service.py    # §6 — all calculations, uses pyxirr
│   ├── price_service.py        # yfinance (stocks) + mfapi.in (MF) + manual (bonds), retry/fallback
│   └── news_service.py         # NEW — Marketaux/NewsData.io + cache
├── jobs/
│   └── price_sync.py           # NEW — APScheduler job
├── schemas/                # marshmallow + flask-smorest-generated OpenAPI
└── tests/
```

---

## 11. Engineering Conventions

- **Env vars** (`.env`, never committed): `DATABASE_URL`, `NEWS_API_KEY`,
  `NEWS_API_PROVIDER` (`marketaux` | `newsdata`), `FLASK_ENV`, `PRICE_SYNC_INTERVAL_MIN`.
  yfinance and mfapi.in need no keys.
- **Git**: feature branches `phase-N-short-name`, PR into `main`, one PR per phase
  from §12 so review stays scoped.
- **Commits**: conventional-ish — `feat:`, `fix:`, `chore:`, `docs:`.
- **Testing**: pytest for `analytics_service` (calculations are the highest-risk code
  in this app — test XIRR, weighted-avg, allocation math directly with known inputs).
  Frontend: component tests optional given team size/timeline; prioritize backend
  calculation tests.
- **Error format**: use the shape in §7 everywhere, including validation errors from
  Marshmallow schemas.

---

## 12. Build Roadmap (detail/prompts live in `PROMPT_SEQUENCE.md`)

| Phase | Scope | Depends on |
|---|---|---|
| 0 | Repo scaffolding (Flask app factory, React+Vite+Tailwind) | — |
| 1 | Design system + component library (dark theme, no real data yet) | 0 |
| 2 | DB schema, models, migrations, seed data | 0 |
| 3 | Holdings CRUD (MVP) + Swagger + Portfolio table page | 1, 2 |
| 4 | Price/NAV sync service (yfinance, mfapi.in, manual for bonds) + resilience | 2 |
| 5 | Analytics engine (P/L, allocation) + KPI cards + donut chart | 3, 4 |
| 6 | **(v2, expanded)** Wallet + dynamic asset search/resolve + historical backfill-on-resolve + transaction-only holdings (BUY/SELL replace direct edit) + realised/unrealised P/L + weighted avg | 3, 4 |
| 7 | Performance chart (portfolio value over time, §6.8, no intraday — see §4.2) | 4, 6 |
| 8 | Segment pages + Asset Detail page **(candlestick via lightweight-charts, full §4.2 periods incl. live 1D, comparison overlay)** | 3, 4, 6 |
| **9** | **(v2, new)** Calculators — Historical Returns, SIP (projected + historical backtest), Step-up SIP — §6.11–§6.13 | 4, 6, 7 |
| 10 | Watchlist, SIPs with explicit Lumpsum/SIP choice, tags, global search | 3, 6 |
| 11 | News integration (dedicated News page + Asset Detail tab, both) | 2 |
| 12 | Home dashboard (portfolio movers + curated-index movers, sparklines, treemap) + full polish pass | 5, 7, 8, 11 |
| **13** | **Recommendation / intelligence layer — LAST, do not build earlier** | everything above |

---

## 13. Guardrails for Phase 13 (Recommendation / Intelligence layer)

This phase is intentionally last and intentionally the most constrained:

- Start **rule-based**, not ML: diversification/concentration score, sector
  overexposure flags, "you're 70% in one sector" nudges, simple rebalancing-vs-target
  suggestions. This is enough to feel intelligent without needing a model or training
  data you don't have.
- Every insight the UI surfaces must read as **educational/informational**, not as
  personalized financial advice — label the panel something like "Portfolio Insights"
  with a one-line disclaimer, not "Recommendations: Buy/Sell."
- Don't let this phase touch the schema, calculations, or API contracts from earlier
  phases — it should be additive (new read-only endpoints + a new UI panel), not a
  refactor of §5–§7.