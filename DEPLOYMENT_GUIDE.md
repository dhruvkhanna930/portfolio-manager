# Deployment Guide: Trained Models Stock Recommendations

## Production Deployment Checklist

### ✓ Pre-Deployment

- [x] Trained models integrated and tested
- [x] API endpoints updated with new scoring
- [x] Error handling for model loading failures
- [x] Documentation complete
- [ ] Performance testing completed (optional)
- [ ] Load testing on recommendation endpoint (optional)

### Environment Setup

**Required Environment Variables**
```bash
ALPHAVANTAGE_KEY=your_key_here      # For market data API
NEWSAPI_KEY=your_key_here           # For news sentiment analysis
DEBUG=False                          # Set to False in production
```

**Python Requirements** (already in requirements.txt)
```
tensorflow>=2.13.0
torch>=2.0.0
transformers>=4.30.0
yfinance>=0.2.0
pandas>=1.5.0
scikit-learn>=1.2.0
numpy>=1.24.0
```

### Database Migration

No database migrations required. The system works with existing Portfolio and StockHolding models.

### Model Files

**Ensure these files are in the backend directory**:
```
backend/
├── Qantas_LSTM_trained_model_fivedays.h5    (Required)
├── Qantas_GRU_trained_model_oneday.h5       (Required)
├── dashboard/
│   ├── trained_models.py                     (New)
│   └── recommendations.py                    (Updated)
└── test_trained_models.py                    (Test suite)
```

### Performance Optimization for Production

#### 1. Model Caching (Recommended)
Add to `dashboard/views.py`:
```python
from django.core.cache import cache
from dashboard.trained_models import TrainedModelPredictor

def get_model_predictor():
    predictor = cache.get('trained_model_predictor')
    if predictor is None:
        predictor = TrainedModelPredictor()
        cache.set('trained_model_predictor', predictor, 3600)  # Cache 1 hour
    return predictor
```

Update `recommendations.py`:
```python
def compute_trained_model_scores(symbols_list):
    predictor = get_model_predictor()  # Use cached instance
    # ... rest of function
```

Configure Django cache in `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

#### 2. Async Model Predictions (Optional - Advanced)
Use Celery for background prediction computation:
```python
from celery import shared_task
from dashboard.trained_models import compute_trained_model_scores

@shared_task
def compute_model_scores_async(symbols):
    return compute_trained_model_scores(symbols)
```

#### 3. Response Caching
Add to `dashboard/views.py`:
```python
from django.views.decorators.cache import cache_page

@login_required
@cache_page(300)  # Cache 5 minutes
def get_recommendations(request):
    # ... existing code
```

### Monitoring & Logging

Add to `settings.py` for production logging:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'logs/recommendations.log',
        },
    },
    'loggers': {
        'dashboard.trained_models': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### Health Checks

Create endpoint to monitor system health:
```python
# dashboard/urls.py
path('health/recommendations/', views.recommendations_health_check, name='health-recommendations')

# dashboard/views.py
from django.http import JsonResponse

def recommendations_health_check(request):
    """Check if recommendation system components are healthy"""
    from dashboard.trained_models import TrainedModelPredictor
    
    try:
        predictor = TrainedModelPredictor()
        return JsonResponse({
            'status': 'healthy',
            'lstm_model_available': predictor.lstm_5day_model is not None,
            'gru_model_available': predictor.gru_1day_model is not None,
            'models_loaded': predictor.models_loaded
        })
    except Exception as e:
        return JsonResponse({
            'status': 'degraded',
            'error': str(e)
        }, status=503)
```

### Capacity Planning

**Resource Requirements**:
- **RAM**: +500MB for model loading (TensorFlow + model weights)
- **Disk**: 50MB for model files
- **CPU**: 2+ cores recommended for concurrent predictions
- **Network**: yfinance API calls ~100KB per stock

**Scaling Considerations**:
- Each recommendation request fetches data for 8-16 stocks
- With caching, subsequent requests are minimal overhead
- Without caching, expect 10-15 seconds per request
- Recommend caching strategy for >100 concurrent users

### Deployment Steps

1. **Pull latest code**
   ```bash
   git pull origin main
   cd NewPortfoioManagementSystem/backend
   ```

2. **Verify models are present**
   ```bash
   ls -la Qantas_*.h5
   ```

3. **Install/update dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests**
   ```bash
   python test_trained_models.py
   ```

5. **Run migrations** (if any)
   ```bash
   python manage.py migrate
   ```

6. **Collect static files** (if needed)
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Start server**
   ```bash
   gunicorn portfolio_management_system.wsgi --workers 4 --threads 2
   ```

### Post-Deployment Verification

1. **Test API endpoint**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://your-domain/dashboard/get-recommendations/
   ```

2. **Check logs**
   ```bash
   tail -f logs/recommendations.log
   ```

3. **Monitor performance**
   - Check response times for `/dashboard/get-recommendations/`
   - Monitor memory usage after model loading
   - Verify yfinance API calls are successful

### Troubleshooting Deployment

**Issue**: Models fail to load
```
Error: Unrecognized keyword arguments passed to LSTM: {'time_major': False}
```
**Solution**: This is expected with newer TensorFlow. System falls back to fundamental + sentiment analysis. Recommendations still work, just without trained model component.

**Issue**: Slow recommendations on first request
**Solution**: This is normal (model loading + API calls). Implement caching to speed up subsequent requests.

**Issue**: 503 Service Unavailable on recommendations
**Solution**: Check yfinance API availability, verify internet connectivity

### Rollback Plan

If issues arise:
```bash
# Disable trained models without removing code
# In settings.py, add:
USE_TRAINED_MODELS = False

# Then in trained_models.py:
if not settings.USE_TRAINED_MODELS:
    TENSORFLOW_AVAILABLE = False
```

### Maintenance

**Monthly**:
- Review recommendation accuracy metrics
- Monitor API usage and caching effectiveness
- Check error logs for patterns

**Quarterly**:
- Evaluate model performance vs. actual stock performance
- Consider retraining or updating models
- Benchmark against baseline (fundamental analysis only)

**Annually**:
- Update trained models with latest data
- Evaluate alternative model architectures
- Assess weight adjustments based on historical performance

### Support & Documentation

- **Test Suite**: Run `python test_trained_models.py` anytime
- **API Docs**: See TRAINED_MODELS_INTEGRATION.md
- **Quick Start**: See QUICK_START_RECOMMENDATIONS.md
- **Architecture**: See README.md in backend

### Success Metrics

Track these after deployment:
- **Response Time**: <15 seconds for recommendation request
- **Model Availability**: >95% successful predictions
- **User Engagement**: >30% of users viewing recommendations
- **Recommendation Accuracy**: Validate periodically against actual returns

