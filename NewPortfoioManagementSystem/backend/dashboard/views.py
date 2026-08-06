import csv
import json
import requests
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Portfolio, StockHolding
from .portfolio_summary import build_portfolio_summary
from .recommendations import get_portfolio_recommendations
from .news_agent import get_portfolio_companies, save_portfolio_companies_to_file, fetch_portfolio_news
from riskprofile.models import RiskProfile
from riskprofile.views import risk_profile
import yfinance as yf

@login_required
def dashboard(request):
  if RiskProfile.objects.filter(user=request.user).exists():
    try:
      portfolio = Portfolio.objects.get(user=request.user)
    except:
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
      average_cost = investment_amount / number_shares
      holdings.append({
        'CompanySymbol': company_symbol,
        'CompanyName': company_name,
        'NumberShares': number_shares,
        'InvestmentAmount': investment_amount,
        'AverageCost': average_cost,
      })
      stocks[0].append(round((investment_amount / portfolio.total_investment) * 100, 2))
      stocks[1].append(company_symbol)
      if c.sector in sector_wise_investment:
        sector_wise_investment[c.sector] += investment_amount
      else:
        sector_wise_investment[c.sector] = investment_amount
    for sec in sector_wise_investment.keys():
      sectors[0].append(round((sector_wise_investment[sec] / portfolio.total_investment) * 100, 2))
      sectors[1].append(sec)

    companies = get_portfolio_companies(portfolio)
    save_portfolio_companies_to_file(companies)
    news = fetch_portfolio_news(companies)

    context = {
      'holdings': holdings,
      'totalInvestment': portfolio.total_investment,
      'stocks': stocks,
      'sectors': sectors,
      'news': news
    }

    return render(request, 'dashboard/dashboard.html', context)
  else:
    return redirect('risk-profile')


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
      portfolio_beta += beta * (c.investment_amount / portfolio.total_investment)
      portfolio_pe += pe * (c.investment_amount / portfolio.total_investment)
    return JsonResponse({"PortfolioBeta": portfolio_beta, "PortfolioPE": portfolio_pe})
  except Exception as e:
    return JsonResponse({"Error": str(e)})


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
def add_holding(request):
  if request.method == "POST":
    try:
      portfolio = Portfolio.objects.get(user=request.user)
      holding_companies = StockHolding.objects.filter(portfolio=portfolio)
      company_symbol = request.POST.get('company', '').strip()
      company_name = request.POST.get('company_name', '').strip() or company_symbol
      number_stocks = int(request.POST.get('number-stocks', 0))
      trade_date = request.POST.get('date', '').strip()

      if not company_symbol:
        return HttpResponse("Please select a valid stock ticker.", status=400)
      if number_stocks <= 0:
        return HttpResponse("Number of stocks must be greater than zero.", status=400)
      if not trade_date:
        return HttpResponse("Please provide a valid trade date.", status=400)

      ticker = yf.Ticker(company_symbol)
      start_date = datetime.strptime(trade_date, '%Y-%m-%d')
      end_date = (start_date + timedelta(days=1)).strftime('%Y-%m-%d')
      history = ticker.history(start=trade_date, end=end_date)
      buy_price = None

      if not history.empty and not history['Close'].dropna().empty:
        buy_price = float(history['Close'].dropna().iloc[0])
      else:
        recent = ticker.history(period='7d')
        recent = recent[recent['Close'].notna()]
        if not recent.empty:
          buy_price = float(recent['Close'].iloc[-1])

      if buy_price is None or buy_price == 0:
        last_price = getattr(ticker.fast_info, 'last_price', None)
        if last_price:
          buy_price = float(last_price)

      if buy_price is None or buy_price == 0:
        return HttpResponse(f"No valid price data found for {company_symbol} around {trade_date}.", status=400)

      info = ticker.info or {}
      sector = info.get('sector', '')

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

      return JsonResponse({"status": "success"})
    except Exception as e:
      print(e)
      return JsonResponse({"status": "error", "message": str(e)}, status=400)
  return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

def send_company_list(request):
  with open('nasdaq-listed.csv') as csv_file:
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
  print('Function Called')
  try:
    output = sp.check_output("quantdom", shell=True)
  except sp.CalledProcessError:
    output = 'No such command'
  return HttpResponse("Success")


@login_required
def get_recommendations(request):
  try:
    portfolio = Portfolio.objects.get(user=request.user)
    recommendations = get_portfolio_recommendations(portfolio)
    return JsonResponse(recommendations)
  except Portfolio.DoesNotExist:
    return JsonResponse({"Error": "Portfolio not found"})
  except Exception as e:
    return JsonResponse({"Error": str(e)})