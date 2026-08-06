from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from unittest.mock import patch

from dashboard.models import Portfolio, StockHolding, WalletTransaction
from dashboard.portfolio_summary import build_portfolio_summary


class PortfolioSummaryTests(SimpleTestCase):
    def test_build_portfolio_summary_detects_concentration(self):
        holdings = [
            {"company_name": "TechCo", "sector": "Technology", "investment_amount": 6000},
            {"company_name": "MedCo", "sector": "Healthcare", "investment_amount": 4000},
        ]

        summary = build_portfolio_summary(holdings, risk_profile_category="Conservative")

        self.assertEqual(summary["total_investment"], 10000)
        self.assertEqual(summary["sector_count"], 2)
        self.assertEqual(summary["top_sector"], "Technology")
        self.assertGreater(summary["concentration_ratio"], 50)
        self.assertIn("Reduce concentration", summary["recommendations"][0])


class SellHoldingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller", password="pass12345")
        self.client.login(username="seller", password="pass12345")
        self.portfolio = Portfolio.objects.create(user=self.user, wallet_balance=100.0)
        self.holding = StockHolding.objects.create(
            portfolio=self.portfolio,
            company_symbol="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            buying_value=[[10.0, 5]],
        )

    def test_get_returns_405(self):
        response = self.client.get("/sell-holding")
        self.assertEqual(response.status_code, 405)

    def test_sell_requires_login(self):
        self.client.logout()
        response = self.client.get("/sell-holding")
        self.assertEqual(response.status_code, 302)

    def test_sell_partial_credits_wallet(self):
        with patch("dashboard.views._get_current_price", return_value=20.0):
            response = self.client.post("/sell-holding", {
                "symbol": "AAPL",
                "shares": "2",
            })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["Success"])
        self.assertEqual(data["Proceeds"], 40.0)
        self.assertEqual(data["RemainingShares"], 3)
        self.assertEqual(data["WalletBalance"], 140.0)

        self.holding.refresh_from_db()
        self.assertEqual(self.holding.number_of_shares, 3)
        self.assertEqual(self.holding.investment_amount, 30.0)
        self.assertEqual(WalletTransaction.objects.filter(transaction_type="SELL").count(), 1)

    def test_sell_more_than_owned_is_rejected(self):
        with patch("dashboard.views._get_current_price", return_value=20.0):
            response = self.client.post("/sell-holding", {
                "symbol": "AAPL",
                "shares": "10",
            })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient shares", response.json()["Error"])

    def test_full_sell_deletes_holding(self):
        with patch("dashboard.views._get_current_price", return_value=20.0):
            response = self.client.post("/sell-holding", {
                "symbol": "AAPL",
                "shares": "5",
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["RemainingShares"], 0)
        self.assertFalse(StockHolding.objects.filter(portfolio=self.portfolio).exists())
        self.portfolio.refresh_from_db()
        self.assertEqual(self.portfolio.wallet_balance, 200.0)

    def test_sell_unknown_symbol_is_rejected(self):
        with patch("dashboard.views._get_current_price", return_value=20.0):
            response = self.client.post("/sell-holding", {
                "symbol": "TSLA",
                "shares": "1",
            })
        self.assertEqual(response.status_code, 400)
        self.assertIn("No holding found", response.json()["Error"])


class TransactionHistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="txnuser", password="pass12345")
        self.client.login(username="txnuser", password="pass12345")
        self.portfolio = Portfolio.objects.create(user=self.user, wallet_balance=50.0)

    def test_history_renders_transactions(self):
        WalletTransaction.objects.create(
            portfolio=self.portfolio, amount=100.0, transaction_type="CREDIT"
        )
        WalletTransaction.objects.create(
            portfolio=self.portfolio, amount=40.0, transaction_type="SELL"
        )
        response = self.client.get("/transactions")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credit")
        self.assertContains(response, "Sell")

    def test_history_requires_login(self):
        self.client.logout()
        response = self.client.get("/transactions")
        self.assertEqual(response.status_code, 302)
