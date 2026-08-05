from django.test import SimpleTestCase

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
