# Stock Recommendation System - File Structure

Complete overview of all files in the stock recommendation system package.

## Directory Structure

```
stock_recommendation_system/
├── __init__.py                          # Package initialization
├── config.py                            # Configuration management
├── recommendations.py                   # Main recommendation engine
├── trained_models.py                    # ML model loading and inference
├── requirements.txt                     # Python dependencies
├── README.md                            # Main documentation
├── FILE_STRUCTURE.md                    # This file
├── .env.example                         # Example environment variables
│
├── models/                              # Pre-trained machine learning models
│   ├── Qantas_GRU_trained_model_oneday.h5      # GRU model for 1-day predictions
│   └── Qantas_LSTM_trained_model_fivedays.h5  # LSTM model for 5-day predictions
│
├── data/                                # Reference and data files
│   └── nasdaq-listed.csv                # NASDAQ stock listings reference
│
├── docs/                                # Documentation
│   ├── INSTALLATION.md                  # Detailed installation guide
│   ├── USAGE.md                         # Usage examples and patterns
│   ├── API.md                           # Complete API reference
│   └── FILE_STRUCTURE.md                # This documentation
│
├── examples/                            # Integration examples
│   └── example_integration.py           # Examples for Django, Flask, FastAPI, etc.
│
└── tests/                               # Test files
    ├── __init__.py                      # Tests module init
    └── test_recommendations.py          # Comprehensive test suite
```

## Core Files

### `recommendations.py` (679 lines)
Main recommendation engine with the following key components:

**Classes:**
- `NewsAnalyzer` - AI sentiment analysis on financial news
- `StockForecastingModel` - LSTM-based price forecasting

**Functions:**
- `get_alphavantage_key()` - Get Alpha Vantage API key
- `get_stock_fundamentals(symbol)` - Fetch stock fundamentals
- `build_stock_features_dataframe(symbols_list)` - Build feature dataframe
- `compute_stock_similarity(stocks_df)` - Similarity matrix computation
- `compute_ai_model_scores(symbols_list)` - AI scoring
- `blend_scores()` - Score blending
- `recommend_stocks()` - Portfolio-based recommendations
- `recommend_complementary_stocks()` - Complementary recommendations
- `get_portfolio_recommendations()` - Combined recommendations
- `get_risk_profile_stock_universe()` - Risk-based stock list
- `score_stock_for_risk_profile()` - Risk profile scoring
- `get_initial_recommendations_by_risk_profile()` - Risk-based recommendations
- `get_popular_stocks_list()` - Popular stocks list

### `trained_models.py` (351 lines)
Machine learning model management.

**Classes:**
- `TrainedModelPredictor` - Load and use pre-trained models

**Functions:**
- `compute_trained_model_scores()` - Batch predictions
- `blend_with_model_scores()` - Score blending
- `evaluate_trained_model()` - Model evaluation
- `compute_trained_models_evaluation_matrix()` - Evaluation matrix

### `config.py` (206 lines)
Configuration management and settings.

**Functions:**
- `get_config_summary()` - Configuration overview
- `validate_config()` - Configuration validation

**Constants:**
- API keys, model paths, weights, feature toggles, etc.

### `__init__.py` (45 lines)
Package initialization with public API exports.

## Documentation Files

### `README.md` (600+ lines)
Comprehensive project documentation including:
- Feature overview
- System architecture
- Installation quick start
- Basic usage examples
- API reference summary
- Integration examples
- Troubleshooting guide
- Performance information

### `docs/INSTALLATION.md` (400+ lines)
Step-by-step installation guide covering:
- System requirements
- Virtual environment setup
- Dependency installation
- Environment variables
- Installation verification
- Troubleshooting
- GPU setup
- Docker setup

### `docs/USAGE.md` (600+ lines)
Comprehensive usage examples including:
- Quick start guide
- Advanced usage patterns
- Flask/FastAPI integration
- Django integration
- Batch processing
- Performance optimization
- Error handling
- Data export

### `docs/API.md` (400+ lines)
Complete API reference with:
- All function signatures
- Parameter descriptions
- Return value documentation
- Code examples
- Performance characteristics
- Configuration options

## Data Files

### `models/` Directory
Contains pre-trained machine learning models:

**Qantas_GRU_trained_model_oneday.h5** (~500MB)
- Architecture: GRU (Gated Recurrent Unit)
- Input: 30-day price lookback window
- Output: 1-day return prediction (0-100 score)
- Training data: Qantas (QAN) historical prices
- Normalization: Min-max scaling

**Qantas_LSTM_trained_model_fivedays.h5** (~500MB)
- Architecture: LSTM (Long Short-Term Memory)
- Input: 60-day price lookback window
- Output: 5-day return prediction (0-100 score)
- Training data: Qantas (QAN) historical prices
- Normalization: Min-max scaling

### `data/` Directory

**nasdaq-listed.csv**
- Source: NASDAQ stock list
- Contains: Ticker symbols, names, market caps
- Purpose: Reference data for validation
- Format: CSV with headers

## Configuration Files

### `.env.example` (70 lines)
Template for environment variables:
- Alpha Vantage API keys
- Logging configuration
- Model settings
- Performance tuning
- Django integration options

### `requirements.txt` (11 packages)
Python package dependencies:
- pandas >= 1.5.0 - Data manipulation
- numpy >= 1.24.0 - Numerical computing
- yfinance >= 0.2.0 - Stock data fetching
- scikit-learn >= 1.2.0 - ML utilities
- alpha_vantage >= 2.3.0 - Alternative data source
- transformers >= 4.30.0 - NLP sentiment
- torch >= 2.0.0 - Deep learning (for transformers)
- tensorflow >= 2.13.0 - LSTM/GRU inference
- requests >= 2.32.0 - HTTP requests
- scipy >= 1.10.0 - Scientific computing

## Example Files

### `examples/example_integration.py` (600+ lines)
Integration examples for various frameworks:
1. Django integration with views and caching
2. Flask/FastAPI endpoints
3. Batch processing
4. APScheduler integration
5. Advanced filtering
6. Data export (CSV, JSON, Excel)
7. Error handling patterns

## Test Files

### `tests/test_recommendations.py` (277 lines)
Comprehensive test suite covering:
- Dependency verification
- Stock data fetching
- Fundamentals retrieval
- Sentiment analysis
- Price forecasting
- Similarity scoring
- Blended scoring
- System status

## File Size Summary

```
Core System:
- recommendations.py:    ~25 KB
- trained_models.py:     ~13 KB
- config.py:             ~8 KB
- __init__.py:           ~2 KB

Documentation:
- README.md:             ~30 KB
- docs/INSTALLATION.md:  ~18 KB
- docs/USAGE.md:         ~35 KB
- docs/API.md:           ~25 KB

Models (Pre-trained):
- GRU model:             ~500 MB
- LSTM model:            ~500 MB

Examples:
- example_integration.py: ~25 KB

Tests:
- test_recommendations.py: ~11 KB

Data:
- nasdaq-listed.csv:     ~1-5 MB

Configuration:
- requirements.txt:      ~<1 KB
- .env.example:          ~<1 KB

Total (excluding models): ~150-200 KB
Total (with models):     ~1+ GB
```

## Usage Patterns by File

| Use Case | Primary Files | Secondary Files |
|----------|---------------|-----------------|
| Get recommendations | recommendations.py | trained_models.py, config.py |
| Load ML models | trained_models.py | config.py |
| Configure system | config.py | .env.example |
| Django integration | examples/example_integration.py | recommendations.py |
| Flask integration | examples/example_integration.py | recommendations.py |
| Batch processing | examples/example_integration.py | recommendations.py |
| Testing | tests/test_recommendations.py | All core files |
| Learning | README.md, docs/USAGE.md | examples/example_integration.py |

## Quick Reference

**To use the system:**
1. Install dependencies from `requirements.txt`
2. Copy `.env.example` to `.env` and configure
3. Import from `__init__.py` or `recommendations.py`
4. See `docs/USAGE.md` for examples

**To integrate with Django:**
1. Copy entire directory to your project
2. See `examples/example_integration.py` for Django examples
3. Adapt views and URLs as needed

**To integrate with Flask/FastAPI:**
1. Copy entire directory to your project
2. See `examples/example_integration.py` for Flask/FastAPI examples
3. Wrap functions in your routes

**To test the system:**
```bash
python tests/test_recommendations.py
```

## Notes

- All Python files use Python 3.8+ syntax
- Models are TensorFlow 2.13+ compatible
- Dependencies are minimal (10 packages) for faster installation
- Documentation is comprehensive with examples and troubleshooting
- System is production-ready with error handling and fallbacks
- Designed for easy integration into existing codebases
