"""Tests for the Phase 16 recommendation scoring.

Pure-function tests -- no DB, no network, no TensorFlow. They pin the two
defects that made the original implementation's output meaningless, so neither
can silently return:

  * the model input window must be (90, 6), the shape the checkpoints declare.
    The original built (30, 1) / (60, 1), which raises a shape error on every
    call -- an error the original caught and replaced with a neutral 50, so
    every "prediction" it ever reported was that constant.
  * blended components must share the 0-100 scale. The original mixed a
    cosine-similarity sum (~0-7) with two 0-100 scores under 0.40/0.35/0.25
    weights, so its stated 40% fundamental weight contributed ~2% in practice.
"""

import math

import pytest

from services import ml_forecast_service as ml
from services import recommendation_service as rec


# --------------------------------------------------------------------------
# model input contract
# --------------------------------------------------------------------------


def _flat_window(value=100.0, bars=None):
    bars = bars or ml.LOOKBACK
    return [[value + i * 0.1] * ml.N_FEATURES for i in range(bars)]


def test_normalized_window_matches_checkpoint_input_shape():
    scaled, _lo, _hi = ml._normalize(_flat_window())
    assert len(scaled) == ml.LOOKBACK == 90
    assert all(len(row) == ml.N_FEATURES == 6 for row in scaled)


def test_normalization_spans_unit_interval():
    scaled, _lo, _hi = ml._normalize(_flat_window())
    flat = [v for row in scaled for v in row]
    assert min(flat) == pytest.approx(0.0)
    assert max(flat) == pytest.approx(1.0)


def test_flat_series_does_not_divide_by_zero():
    """A halted stock has zero spread; it must score neutral, not explode."""
    scaled, lo, hi = ml._normalize([[50.0] * ml.N_FEATURES for _ in range(ml.LOOKBACK)])
    assert lo == hi == 50.0
    assert all(v == 0.5 for row in scaled for v in row)


def test_denormalize_inverts_normalize_on_close():
    window = _flat_window()
    scaled, lo, hi = ml._normalize(window)
    last_scaled_close = scaled[-1][ml.CLOSE_INDEX]
    recovered = ml._denormalize_close(last_scaled_close, lo, hi)
    assert recovered == pytest.approx(window[-1][ml.CLOSE_INDEX])


# --------------------------------------------------------------------------
# score mapping
# --------------------------------------------------------------------------


def test_zero_expected_return_is_neutral():
    assert ml._score_from_return(0.0) == pytest.approx(50.0)


def test_score_is_symmetric_around_neutral():
    up = ml._score_from_return(4.0)
    down = ml._score_from_return(-4.0)
    assert up + down == pytest.approx(100.0)


def test_score_saturates_within_bounds():
    """An implausible +400% must not be able to dominate the blend."""
    assert 0.0 <= ml._score_from_return(400.0) <= 100.0
    assert 0.0 <= ml._score_from_return(-400.0) <= 100.0
    assert ml._score_from_return(400.0) > ml._score_from_return(5.0)


def test_score_is_monotonic_in_return():
    scores = [ml._score_from_return(r) for r in (-5, -1, 0, 1, 5)]
    assert scores == sorted(scores)


# --------------------------------------------------------------------------
# blending -- the scale bug
# --------------------------------------------------------------------------


def test_blend_respects_declared_weights():
    """All components on one scale, so a weight means what it says."""
    blended, coverage = rec._blend({"fit": 100.0, "momentum": 0.0, "sentiment": 0.0, "ml": 0.0})
    assert coverage == pytest.approx(1.0)
    # fit carries 0.40 of a full-scale component -> exactly 40.
    assert blended == pytest.approx(40.0)


def test_blend_renormalizes_when_components_missing():
    """Missing data must not be imputed as a neutral 50 and drag scores centre."""
    blended, coverage = rec._blend({"fit": 90.0, "momentum": None, "sentiment": None, "ml": None})
    assert coverage == pytest.approx(rec.WEIGHTS["fit"])
    assert blended == pytest.approx(90.0)


def test_blend_with_no_components_is_neutral():
    blended, coverage = rec._blend({"fit": None, "momentum": None, "sentiment": None, "ml": None})
    assert blended == pytest.approx(rec.NEUTRAL)
    assert coverage == 0.0


def test_weights_sum_to_one():
    assert sum(rec.WEIGHTS.values()) == pytest.approx(1.0)


# --------------------------------------------------------------------------
# similarity
# --------------------------------------------------------------------------


def test_cosine_of_identical_vectors_is_one():
    v = [1.0, -2.0, 0.5, 3.0, 0.0]
    assert rec._cosine(v, v) == pytest.approx(1.0)


def test_cosine_of_opposite_vectors_is_minus_one():
    v = [1.0, 2.0, 3.0]
    assert rec._cosine(v, [-x for x in v]) == pytest.approx(-1.0)


def test_cosine_handles_zero_vector():
    assert rec._cosine([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_standardize_centres_each_dimension():
    vectors = [
        [10.0, 1.0, 2.0, 3.0, 4.0],
        [20.0, 2.0, 4.0, 6.0, 8.0],
        [30.0, 3.0, 6.0, 9.0, 12.0],
    ]
    out = rec._standardize(vectors)
    for d in range(len(rec.SIMILARITY_FEATURES)):
        column = [row[d] for row in out]
        assert sum(column) == pytest.approx(0.0, abs=1e-9)


def test_standardize_imputes_missing_at_the_mean():
    """A gap becomes exactly 0 after z-scoring -- i.e. no pull in either direction."""
    vectors = [[10.0, 1.0, 2.0, 3.0, 4.0], [20.0, 2.0, 4.0, 6.0, 8.0], [None, 3.0, 6.0, 9.0, 12.0]]
    out = rec._standardize(vectors)
    assert out[2][0] == pytest.approx(0.0)


def test_outlier_features_are_clamped():
    """One 40,000 P/E must not flatten every other stock's score."""
    assert rec._clamp_feature("pe_ratio", 40000.0) == rec.FEATURE_BOUNDS["pe_ratio"][1]
    assert rec._clamp_feature("beta", -99.0) == rec.FEATURE_BOUNDS["beta"][0]
    assert rec._clamp_feature("pe_ratio", None) is None


def test_sparse_feature_vector_is_rejected():
    """Fewer than three real dimensions is imputation, not similarity."""
    assert rec._feature_vector({"pe_ratio": 20.0}) is None
    assert rec._feature_vector({"pe_ratio": 20.0, "beta": 1.1, "dividend_yield": 2.0}) is not None


# --------------------------------------------------------------------------
# fit rules
# --------------------------------------------------------------------------


def test_conservative_prefers_low_beta_dividend_payers():
    defensive = {"pe_ratio": 12.0, "beta": 0.6, "dividend_yield": 3.0}
    racy = {"pe_ratio": 80.0, "beta": 2.1, "dividend_yield": 0.0}
    assert rec._risk_profile_fit(defensive, "conservative") > rec._risk_profile_fit(racy, "conservative")


def test_aggressive_prefers_high_beta_growth():
    racy = {"pe_ratio": 60.0, "beta": 1.8, "return_on_equity": 25.0}
    defensive = {"pe_ratio": 10.0, "beta": 0.5, "return_on_equity": 5.0}
    assert rec._risk_profile_fit(racy, "aggressive") > rec._risk_profile_fit(defensive, "aggressive")


def test_risk_fit_stays_in_range():
    extreme = {"pe_ratio": 100.0, "beta": 3.0, "dividend_yield": 12.0, "return_on_equity": 90.0}
    for profile in rec.VALID_RISK_PROFILES:
        assert 0.0 <= rec._risk_profile_fit(extreme, profile) <= 100.0


def test_complementary_favours_unheld_sectors_continuously():
    """Ties at the ceiling made ordering fall out of DB row order -- not any more."""
    weights = {"IT": 0.7, "FMCG": 0.05}
    unheld = rec._complementary_fit({}, "Healthcare", weights, None)
    light = rec._complementary_fit({}, "FMCG", weights, None)
    heavy = rec._complementary_fit({}, "IT", weights, None)
    assert unheld > light > heavy


def test_complementary_rewards_lowering_portfolio_beta():
    weights = {"IT": 0.5}
    calmer = rec._complementary_fit({"beta": 0.6}, "Power", weights, 1.4)
    wilder = rec._complementary_fit({"beta": 2.0}, "Power", weights, 1.4)
    assert calmer > wilder


def test_sector_aliases_collapse_to_one_bucket():
    """"IT" and "Technology" are the same sector arriving from two vocabularies."""
    assert rec._canonical_sector("IT") == rec._canonical_sector("Technology")
    assert rec._canonical_sector("Basic Materials") == rec._canonical_sector("Metals")
    assert rec._canonical_sector("Consumer Goods") == rec._canonical_sector("FMCG")


def test_sector_alias_matching_is_case_and_space_insensitive():
    assert rec._canonical_sector("  technology  ") == "Technology"
    assert rec._canonical_sector(None) == "Other"


def test_unknown_sector_passes_through():
    assert rec._canonical_sector("Shipping") == "Shipping"


def test_alias_sector_is_not_treated_as_a_diversifier():
    """The bug this map exists for: 48% in "Technology" must not make "IT" look new."""
    weights = {rec._canonical_sector("Technology"): 0.48}
    tech = rec._complementary_fit({}, rec._canonical_sector("IT"), weights, None)
    genuinely_new = rec._complementary_fit({}, rec._canonical_sector("Power"), weights, None)
    assert genuinely_new > tech


def test_complementary_stays_in_range():
    weights = {"IT": 0.0}
    score = rec._complementary_fit({"beta": 0.1, "dividend_yield": 20.0}, "New", weights, 3.0)
    assert 0.0 <= score <= 100.0


# --------------------------------------------------------------------------
# explanations
# --------------------------------------------------------------------------


def test_explanations_skip_neutral_factors():
    reasons = rec._explain({"fit": 50.0, "momentum": None, "sentiment": 92.0, "ml": None}, "similar")
    factors = [r["factor"] for r in reasons]
    assert "tone of recent news" in factors
    assert all(r["direction"] == "supports" for r in reasons)


def test_explanations_report_negative_factors():
    reasons = rec._explain({"fit": 10.0, "momentum": None, "sentiment": None, "ml": None}, "similar")
    assert reasons and reasons[0]["direction"] == "weighs against"


def test_explanations_are_ranked_by_strength():
    reasons = rec._explain({"fit": 70.0, "momentum": 99.0, "sentiment": None, "ml": None}, "similar")
    assert reasons[0]["factor"] == "recent price trend"
