import csv
import json
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Portfolio, StockHolding, WalletTransaction, WatchlistItem
from .portfolio_summary import build_portfolio_summary
from .recommendations import get_portfolio_recommendations, get_initial_recommendations_by_risk_profile
from .news_agent import get_portfolio_companies, save_portfolio_companies_to_file, fetch_portfolio_news
from .trained_models import compute_trained_models_evaluation_matrix
from riskprofile.models import RiskProfile
from riskprofile.views import risk_profile
import yfinance as yf

# AlphaVantage API
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
import subprocess as sp

def get_alphavantage_key():
  return settings.ALPHAVANTAGE_KEY

def _get_price_for_date(symbol, date):
  ts = TimeSeries(key=get_alphavantage_key(), output_format='json')
  data, meta_data = ts.get_daily(symbol=symbol, outputsize='compact')
  try:
    return float(data[date]['4. close'])
  except KeyError:
    raise ValueError(f"No trading data for {symbol} on {date} — markets were closed on this day. Please choose a trading day.")

def _get_current_price(symbol):
  try:
    ticker = yf.Ticker(symbol)
    last_price = None
    try:
      last_price = getattr(ticker.fast_info, 'last_price', None)
    except Exception:
      last_price = None
    if last_price is None:
      hist = ticker.history(period='2d')
      if not hist.empty:
        last_price = hist['Close'].iloc[-1]
    return float(last_price or 0)
  except Exception as e:
    print(f"Error fetching current price for {symbol}: {e}")
    return 0.0

@login_required
def dashboard(request):
  if RiskProfile.objects.filter(user=request.user).exists():
    try:
      portfolio = Portfolio.objects.get(user=request.user)
    except Portfolio.DoesNotExist:
      portfolio = Portfolio.objects.create(user=request.user)
    portfolio.update_investment()
    holding_companies = StockHolding.objects.filter(portfolio=portfolio)
    holdings = []
    sectors = [[], []]
    sector_wise_investment = {}
    stocks = [[], []]
    for c in holding_companies:
      company_symbol = c.company_symbol
      company_name = c.company_name
      number_shares = c.number_of_shares
      investment_amount = c.investment_amount
      average_cost = investment_amount / number_shares if number_shares else 0
      holdings.append({
        'CompanySymbol': company_symbol,
        'CompanyName': company_name,
        'NumberShares': number_shares,
        'InvestmentAmount': investment_amount,
        'AverageCost': average_cost,
      })
      total = portfolio.total_investment or 0
      stocks[0].append(round((investment_amount / total) * 100, 2) if total else 0)
      stocks[1].append(company_symbol)
      if c.sector in sector_wise_investment:
        sector_wise_investment[c.sector] += investment_amount
      else:
        sector_wise_investment[c.sector] = investment_amount
    for sec in sector_wise_investment.keys():
      total = portfolio.total_investment or 0
      sectors[0].append(round((sector_wise_investment[sec] / total) * 100, 2) if total else 0)
      sectors[1].append(sec)

    companies = get_portfolio_companies(portfolio)
    save_portfolio_companies_to_file(companies)
    news = fetch_portfolio_news(companies)

    context = {
      'holdings': holdings,
      'totalInvestment': portfolio.total_investment,
      'walletBalance': portfolio.wallet_balance,
      'stocks': stocks,
      'sectors': sectors,
      'news': news
    }

    return render(request, 'dashboard/dashboard.html', context)
  else:
    return redirect('risk-profile')


@login_required
def get_portfolio_insights(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
    holding_companies = StockHolding.objects.filter(portfolio=portfolio)
    portfolio_beta = 0
    portfolio_pe = 0
    for c in holding_companies:
      ticker = yf.Ticker(c.company_symbol)
      info = ticker.info or {}
      beta = info.get('beta') or info.get('Beta') or 0
      pe = info.get('trailingPE') or info.get('forwardPE') or info.get('PERatio') or 0
      beta = float(beta) if beta not in [None, 'None', 'N/A', ''] else 0
      pe = float(pe) if pe not in [None, 'None', 'N/A', ''] else 0
      total = portfolio.total_investment or 0
      weight = (c.investment_amount / total) if total else 0
      portfolio_beta += beta * weight
      portfolio_pe += pe * weight
    return JsonResponse({"PortfolioBeta": round(portfolio_beta, 2), "PortfolioPE": round(portfolio_pe, 2)})
  except Exception as e:
    return JsonResponse({"Error": str(e)})


@login_required
def update_values(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
    current_value = 0
    unrealized_pnl = 0
    growth = 0
    holding_companies = StockHolding.objects.filter(portfolio=portfolio)
    stockdata = {}
    for c in holding_companies:
      ticker = yf.Ticker(c.company_symbol)
      last_trading_price = None
      try:
        last_trading_price = getattr(ticker.fast_info, 'last_price', None)
      except Exception:
        last_trading_price = None

      if last_trading_price is None:
        hist = ticker.history(period='2d')
        if not hist.empty:
          last_trading_price = hist['Close'].iloc[-1]

      last_trading_price = float(last_trading_price or 0)
      pnl = (last_trading_price * c.number_of_shares) - c.investment_amount
      net_change = pnl / c.investment_amount if c.investment_amount else 0
      stockdata[c.company_symbol] = {
        'LastTradingPrice': last_trading_price,
        'PNL': pnl,
        'NetChange': net_change * 100
      }
      current_value += (last_trading_price * c.number_of_shares)
      unrealized_pnl += pnl
    growth = unrealized_pnl / portfolio.total_investment if portfolio.total_investment else 0
    return JsonResponse({
      "StockData": stockdata, 
      "CurrentValue": current_value,
      "UnrealizedPNL": unrealized_pnl,
      "Growth": growth * 100
    })
  except Exception as e:
    return JsonResponse({"Error": str(e)})


@login_required
def get_financials(request):
  try:
    symbol = request.GET.get('symbol')
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}
    financials = {
      "52WeekHigh": info.get('fiftyTwoWeekHigh', 0),
      "52WeekLow": info.get('fiftyTwoWeekLow', 0),
      "Beta": info.get('beta', 0),
      "BookValue": info.get('bookValue', 0),
      "EBITDA": info.get('ebitda', 0),
      "EVToEBITDA": info.get('enterpriseToEbitda', 0),
      "OperatingMarginTTM": info.get('operatingMargins', 0),
      "PERatio": info.get('trailingPE', 0),
      "PriceToBookRatio": info.get('priceToBook', 0),
      "ProfitMargin": info.get('profitMargins', 0),
      "ReturnOnAssetsTTM": info.get('returnOnAssets', 0),
      "ReturnOnEquityTTM": info.get('returnOnEquity', 0),
      "Sector": info.get('sector', ''),
    }
    return JsonResponse({ "financials": financials })
  except Exception as e:
    return JsonResponse({"Error": str(e)})


@login_required
def portfolio_summary(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
  except Portfolio.DoesNotExist:
    portfolio = Portfolio.objects.create(user=request.user)

  holdings = list(StockHolding.objects.filter(portfolio=portfolio))
  risk_profile = RiskProfile.objects.filter(user=request.user).first()
  summary = build_portfolio_summary(
    holdings,
    risk_profile_category=risk_profile.category if risk_profile else "Balanced"
  )
  return JsonResponse(summary)


@login_required
def profile(request):
  risk_profile = RiskProfile.objects.filter(user=request.user).first()
  return render(request, 'dashboard/profile.html', {
    'risk_profile': risk_profile,
  })


@login_required
@require_POST
def add_holding(request):
  if request.method == "POST":
    try:
      portfolio = Portfolio.objects.get(user=request.user)
      holding_companies = StockHolding.objects.filter(portfolio=portfolio)
      company_symbol = request.POST['company'].split('(')[1].split(')')[0]
      company_name = request.POST['company'].split('(')[0].strip()
      number_stocks = int(request.POST['number-stocks'])
      try:
        buy_price = _get_price_for_date(company_symbol, request.POST['date'])
      except ValueError as e:
        return HttpResponse(str(e), status=400)
      fd = FundamentalData(key=get_alphavantage_key(), output_format='json')
      data, meta_data = fd.get_company_overview(symbol=company_symbol)
      sector = data['Sector']

      found = False
      for c in holding_companies:
        if c.company_symbol == company_symbol:
          c.buying_value.append([buy_price, number_stocks])
          c.save()
          found = True

      if not found:
        c = StockHolding.objects.create(
          portfolio=portfolio,
          company_name=company_name,
          company_symbol=company_symbol,
          number_of_shares=number_stocks,
          sector=sector
        )
        c.buying_value.append([buy_price, number_stocks])
        c.save()

      return HttpResponse("Success")
    except Exception as e:
      print(e)
      return HttpResponse("Error adding holding", status=400)

@login_required
def send_company_list(request):
  csv_path = os.path.join(os.path.dirname(__file__), '..', 'nasdaq-listed.csv')
  with open(csv_path) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    rows = []
    for row in csv_reader:
      if line_count == 0:
        line_count += 1
      else:
        rows.append([row[0], row[1]])
        line_count += 1
  return JsonResponse({"data": rows})


def fetch_news():
  try:
    query_params = {
      "country": "us",
      "category": "business",
      "sortBy": "top",
      "apiKey": settings.NEWSAPI_KEY
    }
    main_url = "https://newsapi.org/v2/top-headlines"
    res = requests.get(main_url, params=query_params, timeout=5)

    if res.status_code != 200:
      print(f"NewsAPI error: {res.status_code}")
      return []

    open_bbc_page = res.json()

    if "articles" not in open_bbc_page:
      print(f"NewsAPI response missing 'articles': {open_bbc_page}")
      return []

    article = open_bbc_page["articles"]

    if not article:
      return []

    results = []
    for ar in article:
      if ar.get("title") and ar.get("url"):
        results.append([ar.get("title", ""), ar.get("description", ""), ar.get("url", "")])

    if not results:
      return []

    news = list(zip(results[::2], results[1::2]))

    if len(results) % 2:
      news.append((results[-1], None))

    return news

  except requests.exceptions.Timeout:
    print("NewsAPI request timed out")
    return []
  except requests.exceptions.RequestException as e:
    print(f"NewsAPI request error: {str(e)}")
    return []
  except Exception as e:
    print(f"Error fetching news: {str(e)}")
    return []


def backtesting(request):
  return JsonResponse({
    "Error": "Backtesting feature is not yet implemented. Coming soon!"
  }, status=501)


@login_required
def get_model_evaluation(request):
  try:
    tickers_param = request.GET.get('tickers', '')
    if tickers_param:
      tickers = [ticker.strip().upper() for ticker in tickers_param.split(',') if ticker.strip()]
    else:
      tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']

    max_samples_param = request.GET.get('max_samples', '50')
    try:
      max_samples = int(max_samples_param)
    except ValueError:
      max_samples = 50

    matrix = compute_trained_models_evaluation_matrix(tickers, max_samples=max_samples)
    return JsonResponse({
      'model_evaluation': matrix,
      'tickers': tickers,
      'max_samples': max_samples
    })
  except Exception as e:
    return JsonResponse({"Error": str(e)})


@login_required
def get_recommendations(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
    # Check if portfolio has holdings
    holding_companies = StockHolding.objects.filter(portfolio=portfolio)

    if holding_companies.exists():
      # User has stocks, use portfolio-based recommendations
      recommendations = get_portfolio_recommendations(portfolio)
    else:
      # User has no stocks, use risk profile-based recommendations
      risk_profile = RiskProfile.objects.filter(user=request.user).first()
      if risk_profile:
        recommendations_list = get_initial_recommendations_by_risk_profile(
          risk_profile.category,
          num_recommendations=10
        )
        recommendations = {
          'similar_stocks': recommendations_list,
          'complementary_stocks': [],
          'source': 'risk_profile',
          'message': f'Personalized recommendations based on your {risk_profile.category} risk profile',
          'ai_models_used': {
            'sentiment_analysis': 'DistilBERT (Transformers)',
            'stock_forecasting': 'LSTM with Exponential Smoothing Fallback',
            'trained_models': {
              'gru_1day': 'GRU model for 1-day price movement prediction',
              'lstm_5day': 'LSTM model for 5-day price movement prediction'
            },
            'scoring_weights': {
              'risk_profile_match': 0.40,
              'sentiment_analysis': 0.35,
              'trained_models': 0.25
            }
          }
        }
      else:
        return JsonResponse({"Error": "Please complete risk profile first"})

    return JsonResponse(recommendations)
  except Portfolio.DoesNotExist:
    # No portfolio exists yet, create one and use risk profile
    try:
      portfolio = Portfolio.objects.create(user=request.user)
      risk_profile = RiskProfile.objects.filter(user=request.user).first()

      if risk_profile:
        recommendations_list = get_initial_recommendations_by_risk_profile(
          risk_profile.category,
          num_recommendations=10
        )
        recommendations = {
          'similar_stocks': recommendations_list,
          'complementary_stocks': [],
          'source': 'risk_profile',
          'message': f'Personalized recommendations based on your {risk_profile.category} risk profile',
          'ai_models_used': {
            'sentiment_analysis': 'DistilBERT (Transformers)',
            'stock_forecasting': 'LSTM with Exponential Smoothing Fallback',
            'trained_models': {
              'gru_1day': 'GRU model for 1-day price movement prediction',
              'lstm_5day': 'LSTM model for 5-day price movement prediction'
            },
            'scoring_weights': {
              'risk_profile_match': 0.40,
              'sentiment_analysis': 0.35,
              'trained_models': 0.25
            }
          }
        }
        return JsonResponse(recommendations)
      else:
        return JsonResponse({"Error": "Please complete risk profile first"})
    except Exception as e:
      return JsonResponse({"Error": str(e)})
  except Exception as e:
    return JsonResponse({"Error": str(e)})


@login_required
@require_POST
def add_wallet_credit(request):
  if request.method == "POST":
    try:
      portfolio = Portfolio.objects.get(user=request.user)
      amount_str = request.POST.get('amount', '').strip()
      if not amount_str:
        return JsonResponse({"Error": "Please enter an amount"}, status=400)
      try:
        amount = float(amount_str)
      except ValueError:
        return JsonResponse({"Error": "Amount must be a valid number"}, status=400)
      if amount <= 0:
        return JsonResponse({"Error": "Amount must be greater than 0"}, status=400)
      portfolio.wallet_balance += amount
      portfolio.save()
      WalletTransaction.objects.create(
        portfolio=portfolio,
        amount=amount,
        transaction_type="CREDIT"
      )
      return JsonResponse({"WalletBalance": portfolio.wallet_balance})
    except Exception as e:
      print(e)
      return JsonResponse({"Error": str(e)}, status=400)


@login_required
@require_POST
def add_to_cart(request):
  if request.method == "POST":
    try:
      portfolio = Portfolio.objects.get(user=request.user)
      company_value = request.POST.get('company', '').strip()
      if '(' in company_value:
        company_symbol = company_value.split('(')[1].split(')')[0]
        company_name = company_value.split('(')[0].strip()
      else:
        company_symbol = company_value
        company_name = request.POST.get('company_name', '').strip() or company_symbol
      number_stocks = int(request.POST['number-stocks'])
      try:
        buy_price = _get_price_for_date(company_symbol, request.POST['date'])
      except ValueError as e:
        return JsonResponse({"Error": str(e)}, status=400)
      item_total = buy_price * number_stocks
      cart = request.session.get('cart', [])
      cart.append({
        'symbol': company_symbol,
        'name': company_name,
        'quantity': number_stocks,
        'price': buy_price,
        'date': request.POST['date'],
        'subtotal': item_total
      })
      request.session['cart'] = cart
      request.session.modified = True
      cart_total = sum(item['subtotal'] for item in cart)
      return JsonResponse({
        "Success": True,
        "CartTotal": cart_total,
        "CartCount": len(cart),
        "Item": {
          'symbol': company_symbol,
          'name': company_name,
          'quantity': number_stocks,
          'price': buy_price,
          'subtotal': item_total
        }
      })
    except Exception as e:
      print(e)
      return JsonResponse({"Error": str(e)}, status=400)


@login_required
def view_cart(request):
  try:
    cart = request.session.get('cart', [])
    cart_total = sum(item['subtotal'] for item in cart)
    return JsonResponse({
      "Cart": cart,
      "CartTotal": cart_total,
      "CartCount": len(cart)
    })
  except Exception as e:
    return JsonResponse({"Error": str(e)}, status=400)


@login_required
def remove_from_cart(request):
  if request.method == "POST":
    try:
      index = int(request.POST.get('index', -1))
      cart = request.session.get('cart', [])
      if 0 <= index < len(cart):
        cart.pop(index)
        request.session['cart'] = cart
        request.session.modified = True
      cart_total = sum(item['subtotal'] for item in cart)
      return JsonResponse({
        "CartTotal": cart_total,
        "CartCount": len(cart)
      })
    except Exception as e:
      return JsonResponse({"Error": str(e)}, status=400)


@login_required
@require_POST
def checkout_cart(request):
  if request.method == "POST":
    try:
      portfolio = Portfolio.objects.get(user=request.user)
      cart = request.session.get('cart', [])
      if not cart:
        return JsonResponse({"Error": "Cart is empty"}, status=400)
      cart_total = sum(item['subtotal'] for item in cart)
      if portfolio.wallet_balance < cart_total:
        return JsonResponse({
          "Error": f"Insufficient wallet balance. Need {cart_total}, have {portfolio.wallet_balance}"
        }, status=400)
      portfolio.wallet_balance -= cart_total
      portfolio.save()
      WalletTransaction.objects.create(
        portfolio=portfolio,
        amount=cart_total,
        transaction_type="PURCHASE"
      )
      holding_companies = StockHolding.objects.filter(portfolio=portfolio)
      for item in cart:
        company_symbol = item['symbol']
        company_name = item['name']
        number_stocks = item['quantity']
        buy_price = item['price']
        fd = FundamentalData(key=get_alphavantage_key(), output_format='json')
        data, meta_data = fd.get_company_overview(symbol=company_symbol)
        sector = data['Sector']
        found = False
        for c in holding_companies:
          if c.company_symbol == company_symbol:
            c.buying_value.append([buy_price, number_stocks])
            c.save()
            found = True
            break
        if not found:
          c = StockHolding.objects.create(
            portfolio=portfolio,
            company_name=company_name,
            company_symbol=company_symbol,
            number_of_shares=number_stocks,
            sector=sector
          )
          c.buying_value.append([buy_price, number_stocks])
          c.save()
      request.session['cart'] = []
      request.session.modified = True
      portfolio.update_investment()
      return JsonResponse({
        "Success": True,
        "WalletBalance": portfolio.wallet_balance,
        "Message": "Purchase completed successfully"
      })
    except Exception as e:
      print(e)
      return JsonResponse({"Error": str(e)}, status=400)


@login_required
@require_POST
def sell_holding(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
    symbol = request.POST.get('symbol', '').strip().upper()
    shares_str = request.POST.get('shares', '').strip()

    if not symbol:
      return JsonResponse({"Error": "Missing stock symbol"}, status=400)

    try:
      shares = int(shares_str)
    except ValueError:
      return JsonResponse({"Error": "Shares must be a whole number"}, status=400)

    if shares <= 0:
      return JsonResponse({"Error": "Shares must be greater than 0"}, status=400)

    holding = StockHolding.objects.filter(portfolio=portfolio, company_symbol=symbol).first()
    if not holding:
      return JsonResponse({"Error": f"No holding found for {symbol}"}, status=400)

    total_shares = holding.number_of_shares
    if shares > total_shares:
      return JsonResponse({
        "Error": f"Insufficient shares. You own {total_shares} shares of {symbol}"
      }, status=400)

    sell_price = _get_current_price(symbol)
    if sell_price <= 0:
      return JsonResponse({"Error": f"Could not fetch the current market price for {symbol}"}, status=400)

    proceeds = round(sell_price * shares, 2)

    remaining = shares
    new_buying_value = []
    for price, quantity in holding.buying_value:
      if remaining <= 0:
        new_buying_value.append([price, quantity])
      elif quantity <= remaining:
        remaining -= quantity
      else:
        new_buying_value.append([price, quantity - remaining])
        remaining = 0

    if not new_buying_value:
      holding.delete()
    else:
      holding.buying_value = new_buying_value
      holding.save()

    portfolio.wallet_balance += proceeds
    portfolio.save()
    WalletTransaction.objects.create(
      portfolio=portfolio,
      amount=proceeds,
      transaction_type="SELL"
    )
    portfolio.update_investment()

    return JsonResponse({
      "Success": True,
      "Proceeds": proceeds,
      "SellPrice": sell_price,
      "SharesSold": shares,
      "RemainingShares": total_shares - shares,
      "WalletBalance": portfolio.wallet_balance,
      "Message": f"Sold {shares} shares of {symbol} for ${proceeds:.2f}"
    })
  except Exception as e:
    print(e)
    return JsonResponse({"Error": str(e)}, status=400)


@login_required
def add_to_watchlist(request):
  if request.method == "POST":
    try:
      portfolio = Portfolio.objects.get(user=request.user)
      company_symbol = request.POST['company'].split('(')[1].split(')')[0]
      company_name = request.POST['company'].split('(')[0].strip()

      watchlist_item, created = WatchlistItem.objects.get_or_create(
        portfolio=portfolio,
        company_symbol=company_symbol,
        defaults={'company_name': company_name}
      )

      if created:
        return JsonResponse({"Success": True, "Symbol": company_symbol, "Name": company_name})
      else:
        return JsonResponse({"Success": False, "Message": "Already in watchlist"}, status=400)
    except Exception as e:
      print(e)
      return JsonResponse({"Error": str(e)}, status=400)


@login_required
def view_watchlist(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
    watchlist_items = WatchlistItem.objects.filter(portfolio=portfolio)

    watchlist_data = []
    ts = TimeSeries(key=get_alphavantage_key(), output_format='json')

    for item in watchlist_items:
      try:
        data, meta_data = ts.get_quote_endpoint(symbol=item.company_symbol)
        current_price = float(data['05. price'])
      except:
        current_price = None

      watchlist_data.append({
        'symbol': item.company_symbol,
        'name': item.company_name,
        'current_price': current_price,
        'added_on': item.added_on.isoformat()
      })

    return JsonResponse({"Watchlist": watchlist_data})
  except Exception as e:
    print(e)
    return JsonResponse({"Error": str(e)}, status=400)


@login_required
def transaction_history(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
  except Portfolio.DoesNotExist:
    portfolio = Portfolio.objects.create(user=request.user)

  transactions = WalletTransaction.objects.filter(portfolio=portfolio).order_by('-timestamp')
  return render(request, 'dashboard/transactions.html', {
    'transactions': transactions,
    'wallet_balance': portfolio.wallet_balance,
    'total_investment': portfolio.total_investment,
  })


@login_required
def remove_from_watchlist(request):
  if request.method == "POST":
    try:
      portfolio = Portfolio.objects.get(user=request.user)
      symbol = request.POST.get('symbol', '')

      WatchlistItem.objects.filter(
        portfolio=portfolio,
        company_symbol=symbol
      ).delete()

      return JsonResponse({"Success": True})
    except Exception as e:
      print(e)
      return JsonResponse({"Error": str(e)}, status=400)


@login_required
def export_data(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
  except Portfolio.DoesNotExist:
    portfolio = Portfolio.objects.create(user=request.user)

  export_type = request.GET.get('type', 'holdings')

  response = HttpResponse(content_type='text/csv')
  writer = csv.writer(response)

  if export_type == 'transactions':
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    writer.writerow(['Timestamp', 'Type', 'Amount'])
    transactions = WalletTransaction.objects.filter(portfolio=portfolio).order_by('-timestamp')
    for txn in transactions:
      writer.writerow([txn.timestamp.isoformat(), txn.transaction_type, txn.amount])
  else:
    response['Content-Disposition'] = 'attachment; filename="holdings.csv"'
    writer.writerow(['Company Name', 'Symbol', 'Sector', 'Number of Shares', 'Investment Amount', 'Average Cost'])
    holdings = StockHolding.objects.filter(portfolio=portfolio)
    for h in holdings:
      avg_cost = h.investment_amount / h.number_of_shares if h.number_of_shares else 0
      writer.writerow([h.company_name, h.company_symbol, h.sector, h.number_of_shares, h.investment_amount, round(avg_cost, 2)])

  return response


@login_required
def get_portfolio_performance(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
    holdings = StockHolding.objects.filter(portfolio=portfolio)
    if not holdings.exists():
      return JsonResponse({"Dates": [], "Values": []})

    symbols = [h.company_symbol for h in holdings]
    shares = {h.company_symbol: h.number_of_shares for h in holdings}

    hist = yf.download(symbols, period='6mo', interval='1d', progress=False, auto_adjust=True)
    if hist.empty or 'Close' not in hist:
      return JsonResponse({"Dates": [], "Values": []})

    close = hist['Close']
    dates = []
    values = []

    if isinstance(close, pd.DataFrame):
      for idx, row in close.iterrows():
        total = 0.0
        for sym in symbols:
          price = row.get(sym)
          if price is not None and price == price:
            total += float(price) * shares.get(sym, 0)
        dates.append(idx.strftime('%Y-%m-%d'))
        values.append(round(total, 2))
    else:
      for idx, price in close.items():
        if price is None or price != price:
          continue
        dates.append(idx.strftime('%Y-%m-%d'))
        values.append(round(float(price) * shares.get(symbols[0], 0), 2))

    return JsonResponse({"Dates": dates, "Values": values})
  except Exception as e:
    return JsonResponse({"Error": str(e)})
