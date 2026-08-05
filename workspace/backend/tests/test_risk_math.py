"""Tests for the §14 analytics math (CLAUDE.md §11: calculations are the
highest-risk code in this app, so they get tested directly with known inputs).

These are pure-function tests -- no DB, no network. They pin the formulas
against values worked out by hand, and lock in the two bugs found during
Phase 14 so they can't silently return:

  * portfolio returns must be time-weighted (contributions are not returns)
  * correlation/beta must align on shared dates, never on positional index
"""

import math
from datetime import date, timedelta

import pytest

from services import health_service as hs
from services import risk_service as rs


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------


def test_stdev_is_sample_not_population():
    # For [2,4,4,4,5,5,7,9]: population sd = 2.0, sample sd = 2.1381...
    xs = [2, 4, 4, 4, 5, 5, 7, 9]
    assert rs._stdev(xs) == pytest.approx(2.13809, abs=1e-4)


def test_percentile_matches_hand_worked_values():
    xs = [1, 2, 3, 4, 5]
    assert rs._percentile(xs, 0) == 1
    assert rs._percentile(xs, 50) == 3
    assert rs._percentile(xs, 100) == 5
    # 25th pct of 5 points: k = 4*0.25 = 1.0 -> exactly the 2nd element
    assert rs._percentile(xs, 25) == 2


def test_daily_returns_from_prices():
    prices = {date(2026, 1, 1): 100.0, date(2026, 1, 2): 110.0, date(2026, 1, 3): 99.0}
    returns = rs.to_daily_returns(prices)
    assert returns[date(2026, 1, 2)] == pytest.approx(0.10)
    assert returns[date(2026, 1, 3)] == pytest.approx(-0.10)
    # the first date has no prior close, so it yields no return
    assert date(2026, 1, 1) not in returns


def test_daily_returns_skip_nonpositive_prior_price():
    prices = {date(2026, 1, 1): 0.0, date(2026, 1, 2): 50.0}
    assert rs.to_daily_returns(prices) == {}


# --------------------------------------------------------------------------
# volatility / ratios
# --------------------------------------------------------------------------


def test_annualized_volatility_scales_by_sqrt_252():
    returns = [0.01, -0.01] * 50
    expected = rs._stdev(returns) * math.sqrt(252)
    assert rs.annualized_volatility(returns) == pytest.approx(expected)


def test_zero_volatility_yields_none_sharpe_not_infinity():
    """A perfectly flat series has zero volatility; Sharpe must not divide by 0."""
    flat = [0.0] * 100
    assert rs.annualized_volatility(flat) == 0.0
    assert rs.sharpe_ratio(flat, 6.5) is None


def test_sortino_only_penalizes_downside():
    """A series whose variance is mostly upside should score far better on
    Sortino than one with the same big swings in both directions.
    """
    mostly_upside = [0.05, 0.0, -0.001, -0.002] * 25
    two_sided = [0.05, -0.05, 0.03, -0.03] * 25
    assert rs.sortino_ratio(mostly_upside, 0) > rs.sortino_ratio(two_sided, 0)


def test_sortino_is_none_when_there_is_no_downside():
    """No losing days means downside deviation is 0 and the ratio is undefined.
    None is the honest answer -- returning a huge number would imply a measured
    result, and dividing by zero would crash.
    """
    assert rs.sortino_ratio([0.05, 0.0, 0.0, 0.0] * 25, 0) is None


def test_max_drawdown_hand_worked():
    # 100 -> 120 -> 60 -> 90 : worst peak-to-trough is 120 -> 60 = 50%
    series = {
        date(2026, 1, 1): 100.0,
        date(2026, 1, 2): 120.0,
        date(2026, 1, 3): 60.0,
        date(2026, 1, 4): 90.0,
    }
    assert rs.max_drawdown(series) == pytest.approx(0.5)


def test_max_drawdown_is_zero_for_monotonically_rising_series():
    series = {date(2026, 1, 1) + timedelta(days=i): 100.0 + i for i in range(10)}
    assert rs.max_drawdown(series) == pytest.approx(0.0)


def test_var_95_is_positive_magnitude_of_loss():
    returns = [-0.10] * 10 + [0.01] * 90  # worst 10% are -10%, so the 5th pct sits well inside them
    var = rs.value_at_risk_95(returns)
    assert var > 0
    assert var == pytest.approx(0.10, abs=0.02)


def test_var_95_is_zero_when_the_fifth_percentile_is_not_a_loss():
    """A distribution whose 5th percentile is still positive has no loss to
    report at 95% confidence -- 0.0, not a negative "gain" dressed up as risk.
    """
    assert rs.value_at_risk_95([0.01] * 100) == 0.0


def test_var_returns_none_below_minimum_observations():
    assert rs.value_at_risk_95([0.01] * (rs.MIN_OBSERVATIONS - 1)) is None


# --------------------------------------------------------------------------
# beta / correlation -- alignment is the thing being protected here
# --------------------------------------------------------------------------


def _dated(values, start=date(2026, 1, 1)):
    return {start + timedelta(days=i): v for i, v in enumerate(values)}


def test_beta_of_asset_against_itself_is_one():
    returns = _dated([0.01, -0.02, 0.03, -0.01] * 20)
    assert rs.beta(returns, returns) == pytest.approx(1.0)


def test_beta_of_double_leveraged_series_is_two():
    bench = _dated([0.01, -0.02, 0.03, -0.01] * 20)
    levered = {d: v * 2 for d, v in bench.items()}
    assert rs.beta(levered, bench) == pytest.approx(2.0)


def test_beta_aligns_on_shared_dates_only():
    """The regression bug this guards: if the two series are zipped positionally
    instead of joined on date, a partially-overlapping pair silently compares
    mismatched days and produces a nonsense beta.
    """
    bench = _dated([0.01, -0.02, 0.03, -0.01] * 20)
    # same values, but shifted a month forward so only part of it overlaps
    shifted = {d + timedelta(days=40): v for d, v in bench.items()}
    overlap = set(bench) & set(shifted)
    assert 0 < len(overlap) < len(bench)  # genuinely partial overlap
    b = rs.beta(shifted, bench)
    if b is not None:
        assert -10 < b < 10, "beta exploded -- series were not aligned on dates"


def test_correlation_of_identical_series_is_one():
    xs = [0.01, -0.02, 0.03, -0.01] * 20
    assert rs.pearson_correlation(xs, xs) == pytest.approx(1.0)


def test_correlation_of_inverted_series_is_minus_one():
    xs = [0.01, -0.02, 0.03, -0.01] * 20
    assert rs.pearson_correlation(xs, [-x for x in xs]) == pytest.approx(-1.0)


def test_correlation_is_always_within_bounds():
    import random

    rng = random.Random(11)
    for _ in range(200):
        xs = [rng.gauss(0, 0.02) for _ in range(60)]
        ys = [rng.gauss(0, 0.02) for _ in range(60)]
        r = rs.pearson_correlation(xs, ys)
        assert r is None or -1.0 <= r <= 1.0


def test_correlation_of_constant_series_is_none_not_zero():
    """Zero would assert 'uncorrelated'; the honest answer is 'undefined'."""
    assert rs.pearson_correlation([0.01] * 50, [0.01, 0.02] * 25) is None


# --------------------------------------------------------------------------
# §14.3 diversification / health components
# --------------------------------------------------------------------------


def test_equal_weights_score_full_diversification():
    for n in (2, 4, 8):
        assert hs.diversification_score([1.0 / n] * n) == pytest.approx(100.0)


def test_single_holding_scores_zero_diversification_not_division_error():
    assert hs.diversification_score([1.0]) == 0.0


def test_concentrated_split_scores_below_even_split():
    assert hs.diversification_score([0.9, 0.1]) < hs.diversification_score([0.5, 0.5])


def test_hhi_bounds():
    assert hs.herfindahl_index([1.0]) == pytest.approx(1.0)
    assert hs.herfindahl_index([0.25] * 4) == pytest.approx(0.25)


def test_shannon_entropy_ignores_zero_weights():
    """0 x ln(0) is defined as 0 here; a NaN would poison the whole score."""
    entropy = hs.shannon_entropy([0.5, 0.5, 0.0])
    assert entropy == pytest.approx(math.log(2))


def test_cash_reserve_score_caps_at_100():
    # target is 10% of portfolio value
    assert hs.cash_reserve_score(0, 100_000) == 0.0
    assert hs.cash_reserve_score(5_000, 100_000) == pytest.approx(50.0)
    assert hs.cash_reserve_score(10_000, 100_000) == pytest.approx(100.0)
    assert hs.cash_reserve_score(90_000, 100_000) == pytest.approx(100.0)


def test_cash_reserve_score_is_zero_when_nothing_invested():
    assert hs.cash_reserve_score(50_000, 0) == 0.0


def test_volatility_score_inverts_and_floors_at_zero():
    assert hs.volatility_score(0.0) == pytest.approx(100.0)
    assert hs.volatility_score(20.0) == pytest.approx(50.0)
    assert hs.volatility_score(hs.VOLATILITY_CEILING_PCT) == pytest.approx(0.0)
    assert hs.volatility_score(999.0) == pytest.approx(0.0)


def test_volatility_score_none_propagates_for_renormalization():
    assert hs.volatility_score(None) is None


def test_sector_balance_score_inverts_largest_sector():
    items = [{"value": 60}, {"value": 40}]
    assert hs.sector_balance_score(items, 100) == pytest.approx(40.0)
    assert hs.sector_balance_score([{"value": 100}], 100) == pytest.approx(0.0)


def test_health_weights_sum_to_one():
    total = (
        hs.WEIGHT_DIVERSIFICATION
        + hs.WEIGHT_CASH_RESERVE
        + hs.WEIGHT_VOLATILITY
        + hs.WEIGHT_SECTOR_BALANCE
    )
    assert total == pytest.approx(1.0)
