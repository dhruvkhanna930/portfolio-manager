"""Monte Carlo projection (CLAUDE.md §14.6).

Bootstrap resampling of REAL historical daily returns -- deliberately not a
fitted normal distribution. Market returns have fatter tails and more extreme
days than a normal curve admits, so sampling the actual observed history keeps
the crash days in the simulation instead of assuming them away.

Read-only and on-demand: nothing here is stored.
"""

import random
from decimal import Decimal

from services import risk_service

MIN_SIMULATIONS = 100
MAX_SIMULATIONS = 2000
DEFAULT_SIMULATIONS = 1000

MIN_HORIZON_DAYS = 1
MAX_HORIZON_DAYS = 2520  # ~10 trading years; beyond this the fan is meaningless
DEFAULT_HORIZON_DAYS = 252

# Reporting cap -- simulating 2520 days is cheap, but returning 2520 points per
# band is a payload nobody plots.
MAX_REPORTED_POINTS = 260

PERCENTILES = (10, 50, 90)

DISCLAIMER = (
    "A simulation of possible outcomes based on this portfolio's own past daily "
    "returns -- not a forecast or a guarantee. Past behaviour does not predict "
    "future results, and real markets can move outside anything in this range."
)


def _sample_points(total_days):
    """Day indices to report, always including the final day."""
    if total_days <= MAX_REPORTED_POINTS:
        return list(range(1, total_days + 1))
    stride = total_days / MAX_REPORTED_POINTS
    days = sorted({max(1, round(i * stride)) for i in range(1, MAX_REPORTED_POINTS + 1)})
    if days[-1] != total_days:
        days.append(total_days)
    return days


def run_projection(horizon_days=DEFAULT_HORIZON_DAYS, n_simulations=DEFAULT_SIMULATIONS, period="ALL", seed=None):
    """Project current portfolio value forward by bootstrapping its own history.

    `seed` is exposed so a given projection can be reproduced exactly (useful for
    tests and for screenshots that need to stay stable); left None it's random.
    """
    horizon_days = max(MIN_HORIZON_DAYS, min(MAX_HORIZON_DAYS, int(horizon_days)))
    n_simulations = max(MIN_SIMULATIONS, min(MAX_SIMULATIONS, int(n_simulations)))

    returns_by_date, _index = risk_service.get_portfolio_return_series(period)
    returns = [returns_by_date[d] for d in sorted(returns_by_date)]

    from services import analytics_service

    summary = analytics_service.get_portfolio_summary()
    start_value = float(summary["total_current"])

    if len(returns) < risk_service.MIN_OBSERVATIONS or start_value <= 0:
        return {
            "insufficient_data": True,
            "reason": (
                "Not enough price history for this portfolio to simulate from "
                f"({len(returns)} daily observations; need at least {risk_service.MIN_OBSERVATIONS})."
            ),
            "observations": len(returns),
            "start_value": Decimal(str(round(start_value, 2))),
            "horizon_days": horizon_days,
            "n_simulations": n_simulations,
            "bands": [],
            "disclaimer": DISCLAIMER,
        }

    rng = random.Random(seed)
    report_days = _sample_points(horizon_days)
    report_set = set(report_days)

    # values_at_day[d] collects every simulation's value on reported day d, so
    # percentiles are taken across simulations at a fixed horizon -- not along a
    # single path, which would be a different (and wrong) question.
    values_at_day = {d: [] for d in report_days}
    final_values = []

    for _ in range(n_simulations):
        value = start_value
        for day in range(1, horizon_days + 1):
            value *= 1.0 + returns[rng.randrange(len(returns))]
            if day in report_set:
                values_at_day[day].append(value)
        final_values.append(value)

    bands = []
    for day in report_days:
        day_values = values_at_day[day]
        entry = {"day": day}
        for p in PERCENTILES:
            entry[f"p{p}"] = Decimal(str(round(risk_service._percentile(day_values, p), 2)))
        bands.append(entry)

    final_sorted = sorted(final_values)
    return {
        "insufficient_data": False,
        "observations": len(returns),
        "start_value": Decimal(str(round(start_value, 2))),
        "horizon_days": horizon_days,
        "n_simulations": n_simulations,
        "method": "bootstrap resampling of actual historical daily returns (with replacement)",
        "bands": bands,
        "final": {
            f"p{p}": Decimal(str(round(risk_service._percentile(final_sorted, p), 2))) for p in PERCENTILES
        },
        "probability_of_loss_pct": Decimal(
            str(round(100.0 * sum(1 for v in final_sorted if v < start_value) / len(final_sorted), 2))
        ),
        "disclaimer": DISCLAIMER,
    }
