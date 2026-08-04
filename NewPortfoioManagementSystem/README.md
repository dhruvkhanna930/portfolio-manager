# New Portfolio Management System

A cleanly organized Django-based portfolio management application with advanced features including real-time portfolio tracking, AI-powered stock recommendations, and comprehensive financial analytics.

## Features

- **Portfolio Tracking** – Monitor your stock holdings with real-time price updates
- **Portfolio Insights** – Analyze portfolio metrics (Beta, P/E ratio, sector allocation)
- **AI-Powered Recommendations** – Get smart stock suggestions based on:
  - **Similar Stocks** – Recommendations matching your current portfolio's financial characteristics
  - **Complementary Stocks** – Diversification suggestions from different sectors
  - Uses machine learning (cosine similarity) to analyze stock fundamentals from AlphaVantage API
  - Dynamically personalized per user, replacing previous static placeholder recommendations
- **Financial Data Integration** – Real-time data from AlphaVantage API
- **News Feed** – Stay updated with relevant market news
- **Risk Profiling** – Personalized risk assessment and recommendations

## Structure

- `backend/` - Django project and application code
  - `dashboard/` - Portfolio management and recommendations
  - `riskprofile/` - User risk assessment
  - `home/` - Authentication and home page
- `frontend/` - Templates and static assets served by Django

## Requirements

- Python 3.8+
- Django 4.2+
- AlphaVantage API key (free tier available)
- NewsAPI key (free tier available)

## Run locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then visit `http://localhost:8000` and log in.

## Environment Setup

Create a `.env` file in the `backend/` directory with:

```
ALPHAVANTAGE_KEY=your_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
```

## Stock Recommendation System

### Evolution
The app originally had **static placeholder recommendations** with hard-coded stock data in three categories (Short/Mid/Long-term). 

### Current Implementation (AI-Powered)
Now uses machine learning to generate **dynamic, personalized recommendations**:

1. **Similar Stocks Algorithm**
   - Fetches fundamental data for user's portfolio stocks via AlphaVantage API
   - Extracts financial features: P/E ratio, Beta, dividend yield, profit margin, ROE
   - Normalizes features using StandardScaler
   - Computes cosine similarity matrix between stocks
   - Ranks and returns top similar stocks with similarity scores

2. **Complementary Stocks Algorithm**
   - Analyzes user's portfolio sector allocation
   - Searches popular stock universe for diversification candidates
   - Prioritizes stocks from underrepresented sectors
   - Scores by risk profile (lower Beta) and income (dividend yield)

3. **API Endpoint**
   - Route: `/dashboard/get-recommendations/`
   - Returns JSON with both similar and complementary stock recommendations
   - Loads on-demand when user clicks Recommendations tab

### How It Works (Like the Movie Recommender)
```
User Portfolio → Fetch Fundamentals → Feature Extraction → 
Normalize → Compute Similarity → Rank → Display Recommendations
```

## Key Dependencies

- `django` - Web framework
- `alpha_vantage` - Financial data API
- `pandas` - Data manipulation for recommendations
- `scikit-learn` - ML library for similarity analysis (cosine similarity)
- `numpy` - Numerical computing for feature normalization
- `requests` - HTTP library for API calls
