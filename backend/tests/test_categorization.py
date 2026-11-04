import pytest

from app.categorization import categorize, category_rank, CATEGORY_ORDER


@pytest.mark.parametrize(
    "days,expected",
    [
        (0, "Performing"),
        (30, "Performing"),
        (31, "Watchlist"),
        (90, "Watchlist"),
        (91, "Substandard"),
        (180, "Substandard"),
        (181, "Doubtful"),
        (360, "Doubtful"),
        (361, "Lost"),
        (1000, "Lost"),
    ],
)
def test_categorize_boundaries(days, expected):
    assert categorize(days) == expected


def test_categorize_none_defaults_to_performing():
    assert categorize(None) == "Performing"


def test_categorize_negative_treated_as_zero():
    assert categorize(-5) == "Performing"


def test_category_rank_orders_worst_last():
    ranks = [category_rank(c) for c in CATEGORY_ORDER]
    assert ranks == sorted(ranks)


def test_category_rank_unknown_category():
    assert category_rank("Not A Real Category") == -1
