# Setup — run this locally

Two processes: a Flask API on `:5000` and a Vite dev server on `:5173`. The
frontend calls the backend over REST, so **both must be running**.

Everything below is copy-pasteable from the repo root (`workspace/`).

---

## 1. Prerequisites

| | Version | Notes |
|---|---|---|
| Python | 3.11 or newer | Developed on 3.14. No TensorFlow is required — see [§7](#7-why-there-is-no-tensorflow). |
| Node.js | 18 or newer | Tested on 23.6.1. |
| SQLite | bundled with Python | Postgres optional, see [§6](#6-environment-variables). |

Check what you have:

```bash
python3 --version
node -v
```

---

## 2. Backend

```bash
cd backend

# virtualenv lives at backend/.venv and is gitignored
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create the env file:

```bash
cp .env.example .env
```

The app **runs without any API keys** — news and AI Suggestions degrade to a
labelled "not configured" state rather than erroring. Fill them in only if you
want those two features live. See [§6](#6-environment-variables).

---

## 3. Seed the demo data

This is the important step. A fresh database has no prices, so every chart,
risk metric and analytics page comes up empty.

```bash
# from backend/, with the venv active
python seed_demo.py
```

**There is no separate database setup step.** No `createdb`, no
`flask db upgrade`, no migration command — `seed_demo.py` calls `create_all()`
itself, so it builds the schema and populates it in one go against an empty
directory. (A `migrations/` folder exists for schema evolution in prod; you do
not need it to run locally.)

On a brand-new clone you will see one line before the seed output:

```
No database found -- skipping the Nifty50 constituent seed.
Run `python seed_demo.py` to create and populate it.
```

That is expected and harmless — the app tries to top up its market-movers
basket at startup, before the database exists. The seed then creates
everything. It does not appear on subsequent runs.

`seed_demo.py` drops and recreates every table, then writes the exact dataset
the demo runs on:

```
holdings         15          10 stocks + 5 mutual funds
invested         Rs 92,190
current value    Rs 104,068
unrealised P/L   Rs 11,878   (+12.88%)

price history    2,265 rows  150 daily bars per asset
benchmark bars   453 rows    NIFTY50 · SENSEX · GOLD
transactions     16          15 buys + 1 dividend
```

Plus 4 monthly SIPs and a ₹200,000 opening wallet deposit.

**It is deterministic.** `random.seed(42)` at the top means everyone who runs
it gets an identical database and identical screenshots. Change `SEED` in
`seed_demo.py` if you want a different-looking portfolio.

### Two seed scripts, two jobs

| Script | Seeds | Use when |
|---|---|---|
| `seed_demo.py` | Priced holdings, 150 days of history, benchmarks, wallet, SIPs | **Demoing.** This is the one you want. |
| `seed.py` | Reference catalog — bonds, fund houses, fund managers, tags | You specifically need bond or fund-house records. Writes **no prices**, so analytics stay empty. |

Run one or the other, not both — each clears the tables it owns.

They differ in one way that matters: `seed_demo.py` calls `create_all()`, so it
works against an empty file. `seed.py` only deletes rows and assumes the tables
already exist, so run `seed_demo.py` (or your migrations) first if `dev.db` is
missing.

### What the seeded portfolio deliberately contains

The data is shaped to exercise the UI, not to flatter it:

- **Winners and losers.** 10 up, 5 down. Axis Bluechip `+32.05%`,
  SBI Magnum `−12.28%`. A demo where everything is green proves nothing.
- **Overall P/L and today's move are independent.** RELIANCE is up 18.4%
  overall but down 2.5% today, so Home's movers and the Portfolio table tell
  genuinely different stories.
- **Per-asset volatility from 0.12 to 0.30**, so the risk/return scatter
  spreads out instead of clustering into a blob.
- **150 bars per asset, not 90.** `risk_service.MIN_OBSERVATIONS` is 30, and
  the 1Y window plus weekend gaps eats into that. At 90 calendar days some
  holdings silently dropped out of the scatter.

---

## 4. Run

Two terminals.

**Terminal 1 — API:**

```bash
cd backend
source .venv/bin/activate
flask --app app run --port 5000
```

**Terminal 2 — frontend:**

```bash
cd frontend
npm install        # first run only
npm run dev
```

Open **http://localhost:5173**.

| | |
|---|---|
| App | http://localhost:5173 |
| API | http://127.0.0.1:5000 |
| Swagger / OpenAPI docs | http://127.0.0.1:5000/docs |

---

## 5. Verify it worked

```bash
curl -s http://127.0.0.1:5000/api/portfolio/summary
```

Expect `"holdings_count": 15`. Then walk the UI:

- [ ] **Home** — KPI cards populated; movers show both gainers *and* losers
- [ ] **Portfolio** — 15 rows, mixed red and green P/L
- [ ] **Transactions** — 16 entries
- [ ] **Analytics → Risk vs Return** — **15 bubbles, none excluded**
- [ ] **Analytics → Benchmarks** — 6 lines: Portfolio, NIFTY50, SENSEX, GOLD,
      FD, Inflation
- [ ] **Analytics → Recommendation Model** — banner reads
      *"trained network live"*, not *"momentum fallback"*
- [ ] **Analytics → AI Suggestions** — enabled only if `GROQ_API_KEY` is set

Run the test suite:

```bash
cd backend && python -m pytest tests/ -q
# 84 passed
```

---

## 6. Environment variables

All optional. `backend/.env` is gitignored — never commit a real key.

| Variable | Default | What it does |
|---|---|---|
| `DATABASE_URL` | SQLite at `backend/dev.db` | Set to a Postgres URL for prod. |
| `GROQ_API_KEY` | *(unset)* | Enables **AI Suggestions**. Free key from [console.groq.com/keys](https://console.groq.com/keys). Without it the page renders a "not configured" panel. |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Override if Groq's free-tier lineup shifts. |
| `NEWS_API_KEY` | *(unset)* | Enables the News page and the sentiment component of recommendations. |
| `NEWS_API_PROVIDER` | `marketaux` | `marketaux` or `newsdata`. |
| `PRICE_SYNC_INTERVAL_MIN` | `30` | APScheduler price-sync cadence. |
| `MODEL_DIR` | auto-resolved | Where the `.h5` checkpoints live. Only set if you moved them. |

yfinance and mfapi.in need no keys.

---

## 7. Why there is no TensorFlow

The recommendation model runs two trained networks — a GRU (718,081 params,
1-day horizon) and an LSTM (958,325 params, 5-day) — and **neither needs
TensorFlow installed.**

`services/keras_h5_runtime.py` reads the trained weight tensors straight out of
the HDF5 checkpoints with `h5py` and reimplements both forward passes in NumPy.
These are the real trained weights; nothing is approximated.

This was not a stylistic choice. TensorFlow publishes no wheels for Python
3.14, and TF ≥ 2.16 ships Keras 3, which refuses the Keras 2.6 HDF5 layout
outright — so using it would mean pinning a legacy TF *and* downgrading the
interpreter, for one component worth 25% of the recommendation blend.

Practical upshot: `pip install -r requirements.txt` pulls **h5py (~1 MB)**
instead of TensorFlow (~500 MB), and the install works on any modern Python.

---

## 8. Troubleshooting

**CORS errors in the browser console, `403 Forbidden`**
The frontend is running but the backend isn't — or you're running an older
backend process from before CORS was configured. Kill and restart it:

```bash
pkill -f "flask --app app"
cd backend && flask --app app run --port 5000
```

**Charts and analytics are empty, but holdings show**
You ran `seed.py` instead of `seed_demo.py`. `seed.py` writes no prices.

**"Risk vs Return" shows only 1–2 bubbles**
Not enough price history — each holding needs ≥30 daily observations.
Re-run `python seed_demo.py`, which writes 150 bars per asset.

**Recommendations banner says "momentum fallback"**
The `.h5` checkpoints weren't found. They live in
`stock_recommendation_system/models/` at the repo root; point `MODEL_DIR` at
them if you've moved things. The app still works — it degrades to a trend
estimate from cached prices and drops the ML component from the blend rather
than filling it with a neutral placeholder.

**AI Suggestions says "not configured"**
`GROQ_API_KEY` isn't set in `backend/.env`. Restart the backend after adding it —
env vars are read at startup.

**`Address already in use` on :5000**
```bash
lsof -ti:5000 | xargs kill -9
```

**Changes to backend code aren't taking effect**
Flask's reloader doesn't always catch new blueprints or service modules.
Restart the process.

---

## 9. Project layout

```
workspace/
├── backend/
│   ├── app.py                  app factory, blueprint registration
│   ├── config.py               env-driven config
│   ├── seed_demo.py            ← demo portfolio (run this)
│   ├── seed.py                 reference catalog only
│   ├── models/                 SQLAlchemy models (schema in CLAUDE.md §5)
│   ├── routes/                 54 REST endpoints
│   ├── schemas/                Marshmallow → OpenAPI
│   ├── services/               25 modules — all business logic
│   ├── jobs/price_sync.py      APScheduler job
│   └── tests/                  84 tests
├── frontend/
│   └── src/{pages,components,hooks,api}/
├── CLAUDE.md                   architecture decisions and schema
├── RECOMMENDATION_MODEL.md     how the GRU/LSTM models work end to end
└── SETUP.md                    this file
```

---

## 10. Resetting

```bash
cd backend
rm -f dev.db
python seed_demo.py
```

`seed_demo.py` drops every table itself, so deleting `dev.db` is only needed if
the schema changed underneath you.
