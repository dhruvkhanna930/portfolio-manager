from django.urls import path
from . import views

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('profile', views.profile, name='profile'),
    path('company-list', views.send_company_list, name="company-list"),
    path('update-prices', views.update_values, name="update-prices"),
    path('get-financials', views.get_financials, name="get-financials"),
    path('add-holding', views.add_holding, name="add-holding"),
    path('portfolio-summary', views.portfolio_summary, name="portfolio-summary"),
    path('get-portfolio-insights', views.get_portfolio_insights, name="get-portfolio-insights"),
    path('backtesting', views.backtesting, name="backtesting"),
    path('get-recommendations', views.get_recommendations, name="get-recommendations"),
    path('get-model-evaluation', views.get_model_evaluation, name='get-model-evaluation'),
    path('wallet-add-credit', views.add_wallet_credit, name="wallet-add-credit"),
    path('cart-add', views.add_to_cart, name="cart-add"),
    path('cart-view', views.view_cart, name="cart-view"),
    path('cart-remove', views.remove_from_cart, name="cart-remove"),
    path('cart-checkout', views.checkout_cart, name="cart-checkout"),
    path('sell-holding', views.sell_holding, name="sell-holding"),
    path('transactions', views.transaction_history, name="transactions"),
]
