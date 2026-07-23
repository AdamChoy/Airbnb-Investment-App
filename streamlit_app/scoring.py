"""Shared Investment Score logic.

Both Home.py's coverage map and pages/5_Property_Analysis.py show a figure
labelled "Investment Score" for the same LADs/MSOAs. They used to compute it
with two different formulas (different weights, and Home's version omitted
the review-score component entirely), so the same area could show two
different scores on two different pages with no explanation. This module is
the single source of truth so that no longer happens — anything that wants
an Investment Score imports it from here.
"""

PROFILES = {
    "yield": {
        "label": "High Yield",
        "sentence": "Weights short-term rental revenue and yield most heavily, prioritising the highest possible return.",
        "weights": {"revenue": 0.40, "occupancy": 0.15, "str_yield": 0.30, "yield_gap": 0.05, "saturation": 0.05, "review": 0.05},
    },
    "occupancy": {
        "label": "High Occupancy",
        "sentence": "Weights booked-night occupancy most heavily, favouring consistently high demand over headline yield.",
        "weights": {"revenue": 0.15, "occupancy": 0.45, "str_yield": 0.15, "yield_gap": 0.05, "saturation": 0.10, "review": 0.10},
    },
    "quality": {
        "label": "Top Rated",
        "sentence": "Weights guest review scores alongside yield, favouring areas where hosts maintain strong guest satisfaction.",
        "weights": {"revenue": 0.20, "occupancy": 0.15, "str_yield": 0.15, "yield_gap": 0.05, "saturation": 0.10, "review": 0.35},
    },
}
DEFAULT_PROFILE = "yield"


def normalise(series):
    if series.max() == series.min():
        return series * 0
    scaled = ((series - series.min()) / (series.max() - series.min())) * 100
    # A missing input (e.g. no reviews yet) shouldn't NaN out the whole
    # weighted score for that row — treat it as the worst case instead.
    return scaled.fillna(0)


def add_investment_score(df, weights=None):
    """Return a copy of df with score component columns and a final
    investment_score (0-100), using the given weights (defaults to the
    DEFAULT_PROFILE weights, the same ones used across the app unless a
    page lets the user pick a different investor profile)."""
    weights = weights or PROFILES[DEFAULT_PROFILE]["weights"]
    df = df.copy()

    df["revenue_score"] = normalise(df["str_annual_revenue_est"])
    df["occupancy_proxy"] = 365 - df["avg_availability_365"]
    df["occupancy_score"] = normalise(df["occupancy_proxy"])
    df["str_yield_score"] = normalise(df["str_gross_yield"])
    df["yield_gap_score"] = normalise(df["str_vs_ltr_yield_delta"])
    df["saturation_score"] = 100 - normalise(df["total_listings"])
    df["review_score"] = normalise(df["avg_review_score"])

    df["investment_score"] = (
        weights["revenue"] * df["revenue_score"]
        + weights["occupancy"] * df["occupancy_score"]
        + weights["str_yield"] * df["str_yield_score"]
        + weights["yield_gap"] * df["yield_gap_score"]
        + weights["saturation"] * df["saturation_score"]
        + weights["review"] * df["review_score"]
    ).round(1)

    return df
