def _get_field_value(holding, field_name):
    if isinstance(holding, dict):
        return holding.get(field_name)
    return getattr(holding, field_name, None)


def build_portfolio_summary(holdings, risk_profile_category="Balanced"):
    total_investment = 0.0
    sector_totals = {}

    for holding in holdings:
        amount = float(_get_field_value(holding, "investment_amount") or 0)
        total_investment += amount
        sector_name = str(_get_field_value(holding, "sector") or "Uncategorized").strip() or "Uncategorized"
        sector_totals[sector_name] = sector_totals.get(sector_name, 0.0) + amount

    if total_investment <= 0:
        return {
            "total_investment": 0.0,
            "number_of_holdings": len(holdings),
            "sector_count": 0,
            "top_sector": "None",
            "concentration_ratio": 0.0,
            "diversification_score": 100.0,
            "risk_profile_category": risk_profile_category,
            "recommendations": ["Start building a portfolio by adding diversified holdings."],
        }

    sector_breakdown = sorted(sector_totals.items(), key=lambda item: item[1], reverse=True)
    top_sector, top_value = sector_breakdown[0]
    concentration_ratio = round((top_value / total_investment) * 100, 2)
    diversification_score = round(max(0.0, 100.0 - concentration_ratio), 2)

    recommendations = []
    if concentration_ratio > 50:
        recommendations.append(f"Reduce concentration in {top_sector} and add positions in other sectors.")
    if len(sector_breakdown) < 3:
        recommendations.append("Add holdings across at least three sectors to improve diversification.")

    category = (risk_profile_category or "Balanced").strip().lower()
    if category in {"conservative", "balanced"}:
        recommendations.append("Consider adding defensive sectors such as Healthcare or Utilities.")
    elif category in {"assertive", "aggressive"}:
        recommendations.append("Keep an eye on sector concentration while seeking higher-growth opportunities.")

    if not recommendations:
        recommendations.append("Your portfolio looks balanced—keep monitoring the mix over time.")

    return {
        "total_investment": round(total_investment, 2),
        "number_of_holdings": len(holdings),
        "sector_count": len(sector_breakdown),
        "top_sector": top_sector,
        "concentration_ratio": concentration_ratio,
        "diversification_score": diversification_score,
        "risk_profile_category": risk_profile_category,
        "recommendations": recommendations,
    }
