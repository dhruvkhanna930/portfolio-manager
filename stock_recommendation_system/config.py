"""
Configuration settings for the stock recommendation system.
Can be imported and customized as needed.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# API Keys
# ============================================================================

# Alpha Vantage API Keys (for fallback fundamental data)
ALPHAVANTAGE_KEYS = [
    os.getenv('ALPHAVANTAGE_KEY1'),
    os.getenv('ALPHAVANTAGE_KEY2'),
    os.getenv('ALPHAVANTAGE_KEY3'),
    os.getenv('ALPHAVANTAGE_KEY4'),
    os.getenv('ALPHAVANTAGE_KEY5'),
    os.getenv('ALPHAVANTAGE_KEY6'),
    os.getenv('ALPHAVANTAGE_KEY7'),
]

# Filter out None values
ALPHAVANTAGE_KEYS = [k for k in ALPHAVANTAGE_KEYS if k]

# ============================================================================
# Model Configuration
# ============================================================================

# Path to trained models
MODELS_PATH = os.path.join(
    os.path.dirname(__file__),
    'models'
)

# Model file names
GRU_1DAY_MODEL = os.path.join(MODELS_PATH, 'Qantas_GRU_trained_model_oneday.h5')
LSTM_5DAY_MODEL = os.path.join(MODELS_PATH, 'Qantas_LSTM_trained_model_fivedays.h5')

# Feature settings
USE_TRAINED_MODELS = os.getenv('USE_TRAINED_MODELS', 'true').lower() == 'true'
USE_SENTIMENT_ANALYSIS = os.getenv('USE_SENTIMENT_ANALYSIS', 'true').lower() == 'true'
USE_PRICE_FORECASTING = os.getenv('USE_PRICE_FORECASTING', 'true').lower() == 'true'

# ============================================================================
# Recommendation Settings
# ============================================================================

# Default number of recommendations per category
DEFAULT_RECOMMENDATIONS = 10

# Maximum recommendations to return
MAX_RECOMMENDATIONS = 50

# Popular stocks list for complementary recommendations
POPULAR_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'WMT',
    'JNJ', 'PG', 'KO', 'PEP', 'MCD', 'DIS', 'NFLX', 'INTC', 'AMD', 'CRM',
    'ADBE', 'CSCO', 'ORCL', 'IBM', 'TM', 'BMW', 'F', 'GM', 'BABA', 'TSM',
    'XOM', 'CVX', 'MRK', 'ABBV', 'PFE', 'LLY', 'UNH', 'BA', 'GE', 'RTX'
]

# Risk profile stock universes
RISK_PROFILE_UNIVERSE = {
    'Conservative': [
        'JNJ', 'PG', 'KO', 'PEP', 'MCD', 'WMT', 'T', 'VZ', 'PFE', 'ABBV',
        'CVX', 'XOM', 'MRK', 'LLY', 'UNH', 'MSFT', 'AAPL', 'V', 'JPM', 'BRK.B'
    ],
    'Balanced': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'JPM', 'V', 'WMT', 'JNJ', 'PG', 'KO',
        'PEP', 'MCD', 'DIS', 'CRM', 'CSCO', 'ORCL', 'IBM', 'INTC', 'AMD', 'TSM'
    ],
    'Assertive': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'CRM',
        'ADBE', 'NFLX', 'DIS', 'INTC', 'TSM', 'BABA', 'SQ', 'SHOP', 'ROKU', 'ZM', 'DASH'
    ],
    'Aggressive': [
        'TSLA', 'META', 'NVDA', 'AMD', 'NFLX', 'INTC', 'BABA', 'TSM', 'SQ', 'ROKU',
        'SHOP', 'ZM', 'DASH', 'COIN', 'SOFI', 'RIOT', 'MARA', 'LCID', 'PLTR', 'AI'
    ]
}

# ============================================================================
# Scoring Weights
# ============================================================================

# Weights for blending different score components
SCORING_WEIGHTS = {
    'fundamental': 0.40,      # Rule-based fundamental analysis
    'ai_sentiment': 0.35,     # Sentiment analysis and forecasting
    'trained_models': 0.25    # Trained ML model predictions
}

# Trained model weight combination (1-day vs 5-day)
TRAINED_MODEL_WEIGHTS = {
    '1day': 0.4,              # GRU 1-day prediction weight
    '5day': 0.6               # LSTM 5-day prediction weight
}

# ============================================================================
# Performance Settings
# ============================================================================

# Maximum stocks to process in a batch
MAX_STOCKS_BATCH = int(os.getenv('MAX_STOCKS_BATCH', '50'))

# Cache time-to-live (seconds)
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))

# Request timeout (seconds)
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

# Number of workers for parallel processing
NUM_WORKERS = 4

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Logging format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ============================================================================
# Data Settings
# ============================================================================

# Path to data directory
DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    'data'
)

# NASDAQ listed companies CSV path
NASDAQ_CSV = os.path.join(DATA_PATH, 'nasdaq-listed.csv')

# Default lookback period for historical data
LOOKBACK_PERIOD = '1y'

# ============================================================================
# Feature Toggles
# ============================================================================

# Whether to analyze news sentiment
ENABLE_SENTIMENT_ANALYSIS = USE_SENTIMENT_ANALYSIS

# Whether to use LSTM price forecasting
ENABLE_PRICE_FORECASTING = USE_PRICE_FORECASTING

# Whether to load and use trained models
ENABLE_TRAINED_MODELS = USE_TRAINED_MODELS

# ============================================================================
# Utility Functions
# ============================================================================


def get_config_summary():
    """Return a summary of the current configuration"""
    return {
        'api_keys_configured': len(ALPHAVANTAGE_KEYS) > 0,
        'trained_models_available': (
            os.path.exists(GRU_1DAY_MODEL) and
            os.path.exists(LSTM_5DAY_MODEL)
        ),
        'features_enabled': {
            'sentiment_analysis': ENABLE_SENTIMENT_ANALYSIS,
            'price_forecasting': ENABLE_PRICE_FORECASTING,
            'trained_models': ENABLE_TRAINED_MODELS,
        },
        'scoring_weights': SCORING_WEIGHTS,
        'cache_ttl_seconds': CACHE_TTL,
        'max_batch_size': MAX_STOCKS_BATCH,
    }


def validate_config():
    """Validate the configuration and return any warnings"""
    warnings = []

    if not ALPHAVANTAGE_KEYS:
        warnings.append(
            "No Alpha Vantage API keys configured. "
            "System will work but with potential rate limiting."
        )

    if not os.path.exists(MODELS_PATH):
        warnings.append(f"Models path does not exist: {MODELS_PATH}")

    if not os.path.exists(GRU_1DAY_MODEL):
        warnings.append(f"GRU model not found: {GRU_1DAY_MODEL}")

    if not os.path.exists(LSTM_5DAY_MODEL):
        warnings.append(f"LSTM model not found: {LSTM_5DAY_MODEL}")

    return warnings
