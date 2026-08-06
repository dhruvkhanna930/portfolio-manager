"""AI Suggestions tests (Phase 17).

The model call itself isn't tested -- it's a network round-trip to a third party
and asserting on generated prose would be flaky by construction. What *is* tested
is everything that protects the user from that call: the grounding check, the
shape-coercion of whatever JSON comes back, and the fact-sheet flattening the
check depends on.
"""

import pytest

from services.ai_insight_service import (
    _collect_fact_numbers,
    _narrative_text,
    _normalize_review,
    verify_figures,
)


FACTS = {
    "total_current_inr": 143956.0,
    "total_profit_loss_pct": 7.13,
    "largest_sector": "Technology",
    "largest_sector_pct": 43.58,
    "health_score": 63,
    "sharpe_ratio": -0.58,
    "has_holdings": True,
    "allocation_by_sector_pct": {"Technology": 43.58, "Metals": 21.42},
    "top_holdings": [{"symbol": "WIPRO.NS", "weight_pct": 25.88}],
}


@pytest.fixture
def numbers():
    return _collect_fact_numbers(FACTS)


# -- flattening ------------------------------------------------------------


def test_collect_walks_nested_dicts_and_lists(numbers):
    assert 43.58 in numbers  # top level
    assert 21.42 in numbers  # nested dict
    assert 25.88 in numbers  # inside a list of dicts


def test_collect_excludes_booleans(numbers):
    """has_holdings=True must not make 1.0 a quotable figure."""
    assert 1.0 not in numbers


# -- grounding check -------------------------------------------------------


def test_exact_figure_passes(numbers):
    assert verify_figures("Technology is 43.58% of the portfolio.", numbers) == []


def test_rounded_figure_passes(numbers):
    """A model rounding 43.58 to 43.6 is being helpful, not wrong."""
    assert verify_figures("Technology is 43.6%.", numbers) == []


def test_complement_of_a_percentage_passes(numbers):
    """"the other 56.4%" is a legitimate way to describe a 43.58% share."""
    assert verify_figures("The remaining 56.4% is spread elsewhere.", numbers) == []


def test_rupees_with_comma_grouping_passes(numbers):
    assert verify_figures("Worth ₹1,43,956 today.", numbers) == []


def test_rupees_with_lakh_scale_passes(numbers):
    """₹1.44 lakh and ₹143956 are the same claim written two ways."""
    assert verify_figures("Worth about ₹1.44 lakh.", numbers) == []


def test_bare_integers_are_not_checked(numbers):
    """Prose counts like "3 winners" aren't quantitative claims worth flagging."""
    assert verify_figures("You hold 11 assets, 3 of them winners.", numbers) == []


def test_fabricated_percentage_is_flagged(numbers):
    assert verify_figures("Technology is 39% of the portfolio.", numbers) == ["39%"]


def test_fabricated_rupee_amount_is_flagged(numbers):
    assert verify_figures("Your portfolio is worth ₹2,50,000.", numbers) == ["₹2,50,000"]


def test_multiple_fabrications_reported_once_each(numbers):
    flagged = verify_figures("Down 12.5%, and again 12.5%, plus 88.1%.", numbers)
    assert flagged == ["12.5%", "88.1%"]


def test_negative_figures_are_checked(numbers):
    """A sign flip on Sharpe changes the meaning entirely, so -0.58 vs 0.58
    must not be treated as the same number."""
    assert verify_figures("Sharpe of 3.4%.", numbers) == ["3.4%"]


# -- response coercion -----------------------------------------------------


def test_normalize_accepts_the_documented_shape():
    review = _normalize_review(
        {
            "headline": "H",
            "summary": "S",
            "observations": [{"title": "T", "body": "B", "sentiment": "concern"}],
            "questions_to_consider": ["Q?"],
            "blind_spots": ["BS"],
        }
    )
    assert review["observations"][0]["sentiment"] == "concern"
    assert review["questions_to_consider"] == ["Q?"]


def test_normalize_rescues_observations_returned_as_strings():
    """JSON mode guarantees valid JSON, not the right keys -- a plain list of
    strings should render, not 500."""
    review = _normalize_review({"observations": ["just a sentence"]})
    assert review["observations"] == [
        {"title": "Observation", "body": "just a sentence", "sentiment": "neutral"}
    ]


def test_normalize_rejects_unknown_sentiment():
    review = _normalize_review({"observations": [{"title": "T", "body": "B", "sentiment": "bullish"}]})
    assert review["observations"][0]["sentiment"] == "neutral"


def test_normalize_handles_a_completely_empty_response():
    review = _normalize_review({})
    assert review["headline"]
    assert review["observations"] == []
    assert review["blind_spots"] == []


def test_normalize_wraps_a_bare_string_list_field():
    review = _normalize_review({"blind_spots": "only one thing"})
    assert review["blind_spots"] == ["only one thing"]


# -- narrative flattening --------------------------------------------------


def test_narrative_covers_every_field_the_check_must_read():
    """A figure hiding in a blind_spot must still be verified, so the flattener
    has to reach every string field."""
    text = _narrative_text(
        {
            "headline": "A 1.1%",
            "summary": "B 2.2%",
            "observations": [{"title": "C 3.3%", "body": "D 4.4%"}],
            "questions_to_consider": ["E 5.5%"],
            "blind_spots": ["F 6.6%"],
        }
    )
    for figure in ("1.1%", "2.2%", "3.3%", "4.4%", "5.5%", "6.6%"):
        assert figure in text
