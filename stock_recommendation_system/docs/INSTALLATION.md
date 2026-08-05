# Installation Guide

## System Requirements

- Python 3.8 or higher
- pip package manager
- 2GB RAM minimum (4GB recommended for ML models)
- Internet connection for downloading stock data

## Step 1: Extract and Navigate to the Package

```bash
cd stock_recommendation_system
```

## Step 2: Create a Virtual Environment (Recommended)

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **Data Processing**: pandas, numpy, scipy
- **Financial Data**: yfinance, alpha_vantage
- **Machine Learning**: scikit-learn, tensorflow, torch
- **NLP/Sentiment**: transformers
- **API**: requests

### Optional: GPU Support for TensorFlow

For faster model inference on NVIDIA GPUs:

```bash
# First, install CUDA 11.8 and cuDNN from NVIDIA website
# Then install TensorFlow GPU version
pip install tensorflow[and-cuda]
```

## Step 4: Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# Get free API keys from https://www.alphavantage.co/
ALPHAVANTAGE_KEY1=YOUR_KEY_HERE
ALPHAVANTAGE_KEY2=YOUR_KEY_HERE
# Add more keys for better rate limiting
```

**Note**: Alpha Vantage keys are optional. The system works without them using yfinance as primary source.

## Step 5: Verify Installation

Run the test suite to verify everything is working:

```bash
python tests/test_recommendations.py
```

You should see:
```
================================================================================
[STOCK RECOMMENDATION SYSTEM - AI MODEL TEST]
================================================================================

[Testing Dependencies...]

[OK] numpy - OK
[OK] pandas - OK
[OK] yfinance - OK
[OK] scikit-learn - OK
[OK] transformers - OK (Sentiment Analysis Available)
[OK] tensorflow - OK (LSTM Forecasting Available)

[READY] System is ready to provide stock recommendations!
```

## Troubleshooting Installation

### Issue: `ModuleNotFoundError: No module named 'tensorflow'`

**Solution**: TensorFlow is a large library. If installation fails:

```bash
# Try installing with a specific version
pip install tensorflow==2.13.0

# Or install CPU version if GPU unavailable
pip install tensorflow-cpu==2.13.0
```

### Issue: `ImportError: DLL load failed` (Windows)

**Solution**: Some Windows systems need Visual C++ runtime:
1. Download from: https://support.microsoft.com/en-us/help/2977003
2. Install the appropriate version for your Python setup

### Issue: `CUDA out of memory` (GPU systems)

**Solution**: GPU memory is limited. Either:
1. Use CPU instead: `pip install tensorflow-cpu`
2. Reduce batch sizes in the code
3. Process fewer stocks at once

### Issue: `ConnectionError: Failed to fetch stock data`

**Solution**: 
- Check your internet connection
- yfinance might be temporarily unavailable
- Try again in a few minutes
- Alternatively, use cached data or local CSV files

### Issue: TensorFlow model won't load

```
Error loading saved model with safe_mode=False
```

**Solution**: Model was trained with a different TensorFlow version.

```bash
# Update TensorFlow
pip install --upgrade tensorflow==2.13.0

# If still failing, retrain the models with current TensorFlow version
```

## Installation for Different Use Cases

### Minimal Installation (Just Recommendation Logic)

If you only need recommendations without AI models:

```bash
pip install pandas numpy yfinance scikit-learn requests
```

This skips tensorflow/torch which are large packages.

### Full Installation (All Features)

All features including sentiment and price forecasting:

```bash
pip install -r requirements.txt
```

### Django Integration

If integrating into a Django project:

```bash
# Your existing Django installation
pip install -r requirements.txt

# Place stock_recommendation_system in your Django project
# Then import as: from stock_recommendation_system import recommendations
```

### Docker Installation

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-c", "from recommendations import get_portfolio_recommendations; print('Ready')"]
```

Build and run:
```bash
docker build -t stock-recommender .
docker run stock-recommender
```

## Verifying Model Files

Check that trained models are in place:

```bash
# Windows
dir models\*.h5

# macOS/Linux
ls models/*.h5
```

You should see:
- `Qantas_GRU_trained_model_oneday.h5`
- `Qantas_LSTM_trained_model_fivedays.h5`

If models are missing, download them or retrain following the model training guide.

## Performance Testing

Test performance on your system:

```python
import time
from recommendations import get_portfolio_recommendations

start = time.time()
recommendations = get_portfolio_recommendations(
    portfolio_stocks=['AAPL', 'MSFT', 'GOOGL'],
    use_ai=True
)
elapsed = time.time() - start

print(f"Generated {len(recommendations['similar_stocks'])} recommendations in {elapsed:.1f}s")
```

**Expected Performance:**
- Without AI: 5-10 seconds (5-10 stocks)
- With AI: 30-60 seconds (5-10 stocks, depends on sentiment API availability)
- With GPU: 10-20 seconds (with AI)

## Next Steps

1. Read [USAGE.md](USAGE.md) for usage examples
2. Check [API.md](API.md) for detailed API documentation
3. See [../examples/example_integration.py](../examples/example_integration.py) for integration examples
4. Run the test suite: `python tests/test_recommendations.py`

## Getting Help

If you encounter issues:

1. Check this troubleshooting section
2. Run `python tests/test_recommendations.py` to identify missing dependencies
3. Check Python version: `python --version` (should be 3.8+)
4. Check pip is up-to-date: `pip install --upgrade pip`
5. Try installing one package at a time to identify the problematic one

## Uninstalling

To remove the virtual environment:

### Windows
```bash
deactivate
rmdir /s venv
```

### macOS/Linux
```bash
deactivate
rm -rf venv
```
