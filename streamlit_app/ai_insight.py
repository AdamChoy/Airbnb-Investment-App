"""AI insight layer for InvestStay.

Turns the already-computed, deterministic investment score (see
add_investment_score in pages/5_Property_Analysis.py) into a short plain-
language write-up for the recommended area. The ranking itself stays
rule-based and transparent; the LLM only narrates the numbers it's given,
so it can't invent figures the app hasn't already computed.

Until an API key is configured, generate_insight() falls back to a
static templated paragraph — the app must never break in a demo just
because OPENAI_API_KEY isn't set.
"""

import os
import streamlit as st

MODEL = "gpt-4o-mini"


def _get_api_key():
    # Prefer Streamlit secrets (st.secrets["OPENAI_API_KEY"] in
    # .streamlit/secrets.toml, never committed) over a plain env var.
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return os.environ.get("OPENAI_API_KEY")


def _static_fallback(area_name, city, budget, stats):
    return (
        f"Based on your search for **{city}** with a budget of **£{budget:,}**, "
        f"**{area_name}** has the highest investment score. It performs well "
        f"because it balances revenue potential, rental yield, demand, and "
        f"market saturation — STR yield of {stats['str_yield']:.1%} against an "
        f"LTR yield of {stats['ltr_yield']:.1%}, with an estimated annual STR "
        f"revenue of £{stats['str_revenue']:,.0f}."
    )


# TODO: remove once OPENAI_API_KEY is configured — these two constants exist
# purely so the AI-shaped UI (Recommendation card, Sentiment "AI Summary"
# card) can be visually tested before a real key is wired in.
_FILLER_INSIGHT = (
    "🤖 *[AI filler — no OPENAI_API_KEY configured yet.]* This is a placeholder "
    "investment insight standing in for the real AI-generated write-up, so the "
    "layout and styling of this card can be checked before the key is added."
)
_FILLER_SUMMARY = (
    "🤖 *[AI filler — no OPENAI_API_KEY configured yet.]* This is a placeholder "
    "review summary standing in for the real AI-generated write-up, so the "
    "layout and styling of this card can be checked before the key is added."
)


@st.cache_data(show_spinner=False)
def generate_insight(area_name: str, city: str, budget: int, stats: dict) -> str:
    """Return a short (3-4 sentence) write-up explaining why `area_name`
    was recommended, grounded only in `stats` (no invented numbers).

    stats expected keys: str_yield, ltr_yield, str_revenue, saturation_score,
    investment_score. Cached per (area_name, city, budget, stats) so the
    same recommendation isn't re-billed on every widget tweak.
    """
    api_key = _get_api_key()
    if not api_key:
        return _FILLER_INSIGHT

    try:
        import openai
    except ImportError:
        return _FILLER_INSIGHT

    prompt = f"""You are writing a short investment insight for a property
investment app. Using ONLY the figures below — do not invent any numbers —
write 3-4 plain-language sentences explaining why {area_name} in {city} is a
good short-term-rental investment for a budget of £{budget:,}.

Figures:
- STR gross yield: {stats['str_yield']:.1%}
- LTR gross yield: {stats['ltr_yield']:.1%}
- Estimated annual STR revenue: £{stats['str_revenue']:,.0f}
- Market saturation score (0-100, lower = more saturated): {stats['saturation_score']:.0f}
- Overall investment score (0-100): {stats['investment_score']:.1f}

Write for a first-time property investor. No headers, no bullet points,
just the sentences."""

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=220,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Network/quota/API errors: never break the demo, just fall back.
        return _static_fallback(area_name, city, budget, stats)


@st.cache_data(show_spinner=False)
def summarise_reviews(msoa_name: str, reviews: tuple[str, ...]) -> str | None:
    """Return a 2-3 sentence summary of `reviews`, grounded only in the
    review text given (no invented claims about the area).

    Unlike generate_insight(), there's no meaningful non-AI fallback for
    summarising free text — if no API key is configured or the call fails,
    this returns None, and callers should just show the raw review
    excerpts instead (which is what happens today with no AI at all).
    """
    reviews = [r.strip() for r in reviews if r and r.strip()]
    if not reviews:
        return None

    api_key = _get_api_key()
    if not api_key:
        return _FILLER_SUMMARY

    try:
        import openai
    except ImportError:
        return _FILLER_SUMMARY

    review_block = "\n".join(f"- {r}" for r in reviews)
    prompt = f"""You are summarising guest reviews for a property investment app.
Using ONLY the reviews below — do not invent details the reviews don't
mention — write a 2-3 sentence summary of what guests say about staying
in {msoa_name}. Focus on recurring themes (e.g. location, cleanliness,
host responsiveness, noise, value). If the reviews disagree, say so
briefly rather than picking one side.

Reviews:
{review_block}

No headers, no bullet points, just the summary sentences."""

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=180,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Network/quota/API errors: never break the demo, just fall back.
        return None
