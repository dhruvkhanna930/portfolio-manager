# New Portfolio Management System

A Django-based portfolio management application that lets users track stock holdings, understand portfolio risk/diversification, and get AI-driven stock recommendations personalized to their existing positions and risk profile.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [AI Recommendation Engine](#ai-recommendation-engine)
- [Data Model](#data-model)
- [Testing](#testing)
- [Key Dependencies](#key-dependencies)

## Features

- **Authentication** – Sign up / log in via `django-allauth`
- **Holdings Tracking** – Add stock holdings and track shares, average cost, and investment amount per position
- **Live Pricing** – Refresh holding values on demand from AlphaVantage
- **Portfolio Insights** – Sector breakdown, concentration ratio, a diversification score, and rule-based rebalancing tips tailored to the user's risk profile
- **Risk Profiling** – A guided questionnaire (age, income, investment horizon, loss tolerance, etc.) that classifies a user into a risk category used elsewhere in the app
- **AI-Powered Recommendations** – Personalized suggestions blending fundamentals-based similarity with two ML signals (see below), replacing the app's original static, hard-coded recommendation lists
- **News Feed** – Market news pulled from NewsAPI
- **Backtesting** – Early-stage hook for strategy backtesting (currently experimental)

## Architecture

Django monolith with three apps sharing one project, server-rendered templates, and a couple of external market-data/news APIs:

```
Browser (Django templates + static JS)
        │
        ▼
 home / dashboard / riskprofile  (Django apps)
        │
        ├── AlphaVantage API  (fundamentals & prices)
        ├── yfinance           (price history & news headlines)
        ├── NewsAPI            (market news feed)
        └── SQLite/PostgreSQL  (via Django ORM)
```

## Project Structure

```
backend/
├── portfolio_management_system/   # Django project settings, root urls, wsgi/asgi
├── home/                           # Landing page + django-allauth wiring
├── dashboard/                      # Holdings, portfolio insights, recommendations
│   ├── models.py                   # Portfolio, StockHolding
│   ├── views.py                    # Dashboard, holdings, recommendations, backtesting endpoints
│   ├── recommendations.py          # Similarity + AI recommendation engine
│   └── portfolio_summary.py        # Sector/diversification analysis
├── riskprofile/                    # Risk questionnaire + RiskProfile model
├── static/                         # CSS/JS/images per app
├── manage.py
└── requirements.txt
frontend/                           # Templates served by Django
```

## Requirements

- Python 3.8+
- Django 4.2 (< 5.0)
- AlphaVantage API key ([free tier](https://www.alphavantage.co/support/#api-key))
- NewsAPI key ([free tier](https://newsapi.org/register))

> Some AI features (sentiment analysis, LSTM forecasting) additionally depend on `transformers`, `torch`, and `tensorflow`. These are heavy installs — see [AI Recommendation Engine](#ai-recommendation-engine) for the fallback behavior if you'd rather skip them.

## Getting Started

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit `http://localhost:8000`, create an account, and log in.

## Environment Variables

Create a `.env` file in `backend/`:

```env
ALPHAVANTAGE_KEY=your_alphavantage_key_here
NEWSAPI_KEY=your_newsapi_key_here
```

## API Endpoints

All routes below are relative to the site root and require an authenticated session unless noted.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/dashboard` | Main dashboard view |
| GET | `/profile` | User profile page |
| GET | `/company-list` | List of companies available for search/holding |
| POST | `/add-holding` | Add a stock holding to the user's portfolio |
| GET | `/update-prices` | Refresh live prices for current holdings |
| GET | `/get-financials` | Fetch fundamental data for a symbol |
| GET | `/portfolio-summary` | Aggregate portfolio totals |
| GET | `/get-portfolio-insights` | Sector breakdown, concentration & diversification score, tips |
| GET | `/get-recommendations` | Personalized similar + complementary stock recommendations |
| GET | `/backtesting` | Experimental backtesting hook |
| GET | `/risk-profile` | Risk profiling questionnaire |
| — | `/accounts/*` | Login/signup/logout via `django-allauth` |

## AI Recommendation Engine

The recommendation system (`dashboard/recommendations.py`) evolved from static, hard-coded Short/Mid/Long-term stock lists into a dynamic pipeline personalized per user:

1. **Fundamentals & Similarity**
   - Pulls fundamentals (P/E ratio, Beta, dividend yield, profit margin, ROE) per holding from AlphaVantage
   - Normalizes features with `StandardScaler` and ranks candidate stocks by cosine similarity to the user's current portfolio
2. **News Sentiment (`NewsAnalyzer`)**
   - Fetches recent headlines per ticker via `yfinance`
   - Scores sentiment with a HuggingFace `transformers` pipeline (DistilBERT fine-tuned on SST-2); if `transformers` isn't installed, falls back to a neutral score
3. **Return Forecasting (`StockForecastingModel`)**
   - If TensorFlow/Keras is available, trains a small LSTM on recent price history to score momentum; otherwise falls back to a simple trend/momentum heuristic
4. **Blended Score**
   - Combines the rule-based similarity score with the AI model scores (`blend_scores`) to rank both **similar stocks** (same profile as current holdings) and **complementary stocks** (diversification into underrepresented sectors, weighted toward lower Beta / higher dividend yield)
5. **Delivery**
   - Served from `/get-recommendations`, loaded on-demand from the dashboard's Recommendations tab

```
Portfolio → Fundamentals + News + Price History
          → Similarity Score / Sentiment Score / Forecast Score
          → Blended Ranking
          → Similar & Complementary Recommendations
```

## Data Model

- **Portfolio** — one per user; tracks `total_investment`, recalculated from its holdings
- **StockHolding** — belongs to a portfolio; stores symbol, name, sector, and a `buying_value` list of `(price, quantity)` lots, from which `investment_amount` and `number_of_shares` are derived on save
- **RiskProfile** — one per user; captures answers to the risk questionnaire (age, income band, investment horizon, loss tolerance, etc.) and a resulting `category`

## Testing

```bash
cd backend
python manage.py test
```

## Key Dependencies

| Package | Purpose |
| --- | --- |
| `django`, `django-allauth` | Web framework and authentication |
| `alpha_vantage` | Fundamentals and pricing data |
| `yfinance` | Price history and news headlines |
| `pandas`, `numpy` | Data wrangling for recommendations and insights |
| `scikit-learn` | Feature scaling and cosine similarity |
| `transformers`, `torch` | News sentiment analysis (optional, falls back gracefully) |
| `tensorflow` | LSTM return forecasting (optional, falls back gracefully) |
| `PyPortfolioOpt`, `scipy` | Portfolio optimization primitives |
| `requests` | HTTP calls to external APIs |
