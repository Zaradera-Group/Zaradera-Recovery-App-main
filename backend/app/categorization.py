"""
Risk-category classification by days past due (PDL aging).

Bands are the CBN prudential-guideline bands for Deposit Money Banks
(confirmed against the published guideline, not assumed):
  0-30    Performing
  31-90   Watchlist
  91-180  Substandard
  181-360 Doubtful
  361+    Lost

This is the single source of truth for a loan's risk category in this app.
The sheet's own "Performance Classification" column is stored alongside
for reference (Snapshot.sheet_classification) but does not drive category —
Zaradera's own field doesn't always track days-past-due directly.
"""

# (upper_bound_inclusive, category_label) — checked in order, first match wins.
_BANDS = [
    (30, "Performing"),
    (90, "Watchlist"),
    (180, "Substandard"),
    (360, "Doubtful"),
]
_FALLBACK_CATEGORY = "Lost"

# Ordering used for trend comparisons (worsening = moving right, improving = moving left).
CATEGORY_ORDER = ["Performing", "Watchlist", "Substandard", "Doubtful", "Lost"]


def categorize(days_past_due: int | float | None) -> str:
    """Return the risk category for a given days-past-due value."""
    if days_past_due is None:
        days_past_due = 0
    days_past_due = int(days_past_due)

    if days_past_due < 0:
        days_past_due = 0

    for upper_bound, label in _BANDS:
        if days_past_due <= upper_bound:
            return label
    return _FALLBACK_CATEGORY


def category_rank(category: str) -> int:
    """Higher rank = worse risk. Used to detect worsening vs improving loans."""
    try:
        return CATEGORY_ORDER.index(category)
    except ValueError:
        return -1
