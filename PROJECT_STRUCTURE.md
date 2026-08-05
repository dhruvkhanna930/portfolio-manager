# Project Structure - Clean Organization

## ✅ Correct Project Layout

```
portfolio-manager/
│
├── NewPortfoioManagementSystem/
│   ├── backend/                          ← Django Backend (Main App)
│   │   ├── portfolio_management_system/  ← Django Project Settings
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   └── wsgi.py
│   │   │
│   │   ├── dashboard/                    ← Stock Portfolio App
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── recommendations.py        ← NEW: Recommendation engine
│   │   │   ├── trained_models.py         ← NEW: ML model integration
│   │   │   ├── portfolio_summary.py
│   │   │   └── migrations/
│   │   │
│   │   ├── riskprofile/                  ← Risk Assessment App
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── migrations/
│   │   │
│   │   ├── home/                         ← Authentication & Home
│   │   │   ├── models.py
│   │   │   ├── views.py
│   │   │   └── migrations/
│   │   │
│   │   ├── static/                       ← Static Files (CSS, JS, Images)
│   │   │   ├── dashboard/
│   │   │   │   ├── css/
│   │   │   │   ├── js/
│   │   │   │   ├── images/
│   │   │   │   └── fonts/
│   │   │   ├── riskprofile/
│   │   │   │   ├── css/
│   │   │   │   ├── js/
│   │   │   │   └── images/
│   │   │   ├── home/
│   │   │   └── account/
│   │   │
│   │   ├── templates/                    ← HTML Templates
│   │   │   ├── dashboard/
│   │   │   │   ├── dashboard.html
│   │   │   │   ├── profile.html
│   │   │   │   └── ...
│   │   │   ├── riskprofile/
│   │   │   │   ├── risk-profile.html
│   │   │   │   ├── recommendations.html   ← NEW: Initial recommendations
│   │   │   │   └── ...
│   │   │   ├── home/
│   │   │   └── account/
│   │   │
│   │   ├── manage.py                     ← Django CLI
│   │   ├── requirements.txt              ← Python Dependencies
│   │   ├── db.sqlite3                    ← Database
│   │   ├── nasdaq-listed.csv             ← Stock Data
│   │   │
│   │   ├── Qantas_LSTM_trained_model_fivedays.h5    ← Trained Models
│   │   └── Qantas_GRU_trained_model_oneday.h5
│   │
│   ├── frontend/                         ← Optional Frontend (Unused)
│   │   ├── static/
│   │   └── templates/
│   │
│   └── README.md
│
├── Documentation/                        ← User Guides & Docs
│   ├── TRAINED_MODELS_INTEGRATION.md
│   ├── RISK_PROFILE_RECOMMENDATIONS.md
│   ├── TENSORFLOW_COMPATIBILITY_GUIDE.md
│   ├── QUICK_START_RECOMMENDATIONS.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── ...
│
└── .gitignore
```

## 📁 Django App Structure (Backend)

Each Django app follows this pattern:

### 1. **portfolio_management_system/** (Project Settings)
```
portfolio_management_system/
├── settings.py          ← Configuration (databases, apps, keys)
├── urls.py             ← URL routing
├── wsgi.py             ← Server config
└── __init__.py
```

### 2. **dashboard/** (Main App)
```
dashboard/
├── models.py           ← Database models (Portfolio, StockHolding)
├── views.py            ← HTTP handlers & API endpoints
├── urls.py             ← URL patterns
├── admin.py            ← Django admin config
├── apps.py             ← App configuration
├── tests.py            ← Test cases
├── recommendations.py  ← Recommendation engine (NEW)
├── trained_models.py   ← ML model integration (NEW)
├── portfolio_summary.py ← Portfolio analysis
├── migrations/         ← Database migration history
└── __init__.py
```

### 3. **riskprofile/** (Risk Assessment)
```
riskprofile/
├── models.py           ← RiskProfile model
├── views.py            ← Risk profile questionnaire handler
├── urls.py             ← Risk profile routes
├── admin.py
├── tests.py
├── migrations/
└── __init__.py
```

### 4. **home/** (Authentication)
```
home/
├── models.py           ← Custom user models
├── views.py            ← Login/signup handlers
├── urls.py
├── migrations/
└── __init__.py
```

## 🎨 Static Files (CSS, JS, Images)

```
static/
├── dashboard/
│   ├── css/           ← Dashboard styling
│   ├── js/            ← Dashboard JavaScript
│   ├── images/        ← Dashboard images
│   └── fonts/         ← Custom fonts
├── riskprofile/
│   ├── css/           ← Risk profile styling
│   ├── js/            ← Risk profile validation (custom.js)
│   └── images/        ← Risk profile images
├── home/              ← Home page assets
└── account/           ← Account page assets
```

## 📄 Templates (HTML)

```
templates/
├── dashboard/
│   ├── dashboard.html ← Main portfolio view
│   ├── profile.html   ← User profile page
│   └── ...
├── riskprofile/
│   ├── risk-profile.html        ← Questionnaire (Q1-Q13)
│   ├── recommendations.html     ← Initial recommendations (NEW)
│   └── ...
├── home/              ← Home page templates
└── account/           ← Account management templates
```

## 🗄️ Database Models

### Dashboard App
```python
Portfolio
├── user (FK)
├── total_investment
├── created_at
└── updated_at

StockHolding
├── portfolio (FK)
├── company_symbol
├── company_name
├── sector
├── number_of_shares
├── investment_amount
├── buying_value (JSON)
└── timestamps
```

### Risk Profile App
```python
RiskProfile
├── user (OneToOne)
├── category (Conservative/Balanced/Assertive/Aggressive)
├── age
├── emergency_funds
├── investment_percentage
├── expected_return_rate
├── keep_capital_safe
├── annual_take_home_income
├── worry_if_fall_percentage
├── current_life_stage
├── investment_familiarity
├── investment_length
├── work_status
└── critical_situation_response
```

## 🔄 Data Flow

```
User Login
    ↓
Risk Profile Questionnaire (riskprofile/views.py)
    ↓
Generate Initial Recommendations (recommendations.py)
    ├── get_initial_recommendations_by_risk_profile()
    ├── Fetch stock fundamentals (yfinance)
    ├── Score by risk profile match
    ├── Compute AI sentiment
    ├── Get trained ML predictions
    └── Return top 10 stocks
    ↓
Show Recommendations Page (templates/recommendations.html)
    ↓
Add Stocks to Portfolio (dashboard/views.py)
    ├── Create StockHolding records
    └── Store in Portfolio
    ↓
Portfolio Dashboard (dashboard/views.py)
    ├── Display holdings
    ├── Show portfolio metrics
    └── Generate portfolio-based recommendations
    ↓
Portfolio-Based Recommendations (recommendations.py)
    ├── get_portfolio_recommendations()
    ├── Similar stocks (same fundamentals)
    ├── Complementary stocks (different sectors)
    └── Score with all AI/ML models
```

## 📊 Key Files (New Additions)

### Recommendation Engine
- **File**: `dashboard/recommendations.py`
- **Size**: ~600 lines
- **Functions**:
  - `get_initial_recommendations_by_risk_profile()` - Initial recs based on risk
  - `get_portfolio_recommendations()` - Recs based on portfolio holdings
  - `recommend_stocks()` - Similar stocks
  - `recommend_complementary_stocks()` - Diversification stocks
  - Score blending functions

### Trained Models Integration
- **File**: `dashboard/trained_models.py`
- **Size**: ~200 lines
- **Class**: `TrainedModelPredictor`
- **Models**: LSTM (5-day), GRU (1-day)
- **Fallback**: Graceful degradation if TensorFlow incompatible

### Risk Profile Recommendations
- **File**: `templates/riskprofile/recommendations.html`
- **Purpose**: Display initial stock recommendations after questionnaire
- **Features**: Beautiful UI, all scores, action buttons

### Risk Profile Validation
- **File**: `static/riskprofile/js/custom.js`
- **Updated**: Form validation for Q1-Q13
- **Features**: Clean error messages, guided navigation

## 🚀 Deployment Structure

For production:
```
portfolio-manager/
├── docker-compose.yml     ← Container orchestration
├── nginx.conf            ← Web server config
├── gunicorn.conf         ← Application server config
├── .env                  ← Environment variables
├── .gitignore            ← Version control ignore
├── README.md             ← Project documentation
│
├── NewPortfoioManagementSystem/
│   └── backend/          ← As above
│
└── docs/                 ← Additional documentation
```

## ✅ What's Clean Now

| Item | Status | Notes |
|------|--------|-------|
| Folder nesting | ✅ Clean | No duplicate `NewPortfoioManagementSystem/backend/NewPortfoioManagementSystem/backend/` |
| Django apps | ✅ Organized | dashboard, riskprofile, home, portfolio_management_system |
| Static files | ✅ Organized | Per-app CSS, JS, images |
| Templates | ✅ Organized | Per-app HTML files |
| Code files | ✅ Clean | Separated concerns (models, views, recommendations, ml_models) |
| Documentation | ✅ Complete | Multiple guides for different aspects |

## 📋 File Organization Checklist

✅ **Backend Logic**
- Models in `models.py`
- Views & routes in `views.py`
- URLs in `urls.py`
- Recommendations in `recommendations.py`
- ML integration in `trained_models.py`

✅ **Frontend Assets**
- Styles in `static/<app>/css/`
- Scripts in `static/<app>/js/`
- Images in `static/<app>/images/`

✅ **Templates**
- HTML in `templates/<app>/`
- One template per view/feature
- Responsive design for mobile

✅ **Documentation**
- Each feature has a guide
- Setup instructions included
- Troubleshooting provided
- API documentation available

## 🎯 Best Practices Applied

1. **Separation of Concerns**
   - Each app handles one domain
   - Models, views, templates separate
   - Logic files (recommendations.py, trained_models.py) isolated

2. **Django Convention**
   - Standard app structure
   - Models-Views-Templates pattern
   - URLs organized hierarchically

3. **Scalability**
   - Easy to add new apps
   - Easy to add new models
   - Easy to add new views/endpoints

4. **Maintainability**
   - Clear file organization
   - Logical grouping
   - Documented structure

## 🔍 No Duplicates

```
❌ BEFORE (Wrong):
backend/
├── NewPortfoioManagementSystem/  ← DUPLICATE NESTING
│   └── backend/
│       └── dashboard/
└── dashboard/                     ← CORRECT

✅ AFTER (Clean):
backend/
├── dashboard/                     ← Single location
├── riskprofile/
├── home/
├── portfolio_management_system/
├── static/
└── templates/
```

---

**Status**: ✅ **CLEAN & ORGANIZED**

Your project now has a professional, maintainable structure! 🎉

