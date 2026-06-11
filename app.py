"""
app.py
======

Interactive Streamlit front-end for the Smartphone Upgrade Probability Model.

Run with:

    streamlit run app.py

Adjust the sliders in the sidebar to see how the predicted upgrade probability
under each environmental-framing condition responds. The app is a thin UI layer
over model.py — all of the behavioral logic lives there.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st
from matplotlib.ticker import PercentFormatter

import model

st.set_page_config(page_title="Smartphone Upgrade Probability Model", layout="wide")

st.title("📱 Smartphone Upgrade Probability Model")
st.caption(
    "A theoretical behavioral-economics simulation of how environmental "
    "trade-in framing may shift smartphone upgrade probability through moral "
    "licensing. **Not** a validated empirical forecast."
)

# Load baseline parameters so the sliders can start from sensible defaults.
markets = model.load_parameters()

with st.sidebar:
    st.header("Parameters")
    market_name = st.selectbox("Market", list(markets.keys()))
    base = markets[market_name]

    st.markdown("**Trade-in & timing**")
    credit_to_income = st.slider(
        "Credit-to-income ratio  C/Y", 0.0, 0.5, float(base.credit_to_income), 0.01
    )
    present_bias = st.slider(
        "Present-bias weight  β", 0.6, 1.4, float(base.present_bias), 0.01,
        help="Higher = consumer over-weights the immediate trade-in credit.",
    )

    st.markdown("**Moral licensing channel**")
    moral_licensing_effect = st.slider(
        "Moral-licensing effect  γ", 0.0, 2.0, float(base.moral_licensing_effect), 0.05
    )
    claim_verifiability = st.slider(
        "Claim verifiability  V", 0.0, 1.0, float(base.claim_verifiability), 0.01,
        help="Higher = the manufacturer's green claim is easy to verify, leaving less room to license.",
    )
    env_self_identity = st.slider(
        "Environmental self-identity  ω", 0.0, 1.0, float(base.env_self_identity), 0.01
    )

    st.markdown("**Resistance & disclosure**")
    baseline_resistance = st.slider(
        "Baseline resistance  κ", 0.0, 2.0, float(base.baseline_resistance), 0.05
    )
    specificity = st.slider(
        "Disclosure information specificity  s", 0.0, 1.0, model.DEFAULT_SPECIFICITY, 0.01
    )
    specificity_threshold = st.slider(
        "Specificity threshold  s*", 0.0, 1.0, float(base.specificity_threshold), 0.01
    )

# Build a parameter set from the slider values.
params = model.MarketParameters(
    market=market_name,
    claim_verifiability=claim_verifiability,
    env_self_identity=env_self_identity,
    moral_licensing_effect=moral_licensing_effect,
    present_bias=present_bias,
    discount_factor=base.discount_factor,
    baseline_resistance=baseline_resistance,
    specificity_threshold=specificity_threshold,
    credit_to_income=credit_to_income,
)

probs = {
    cond: model.upgrade_probability(
        params, cond, credit_to_income=credit_to_income, specificity=specificity
    )
    for cond in model.CONDITIONS
}
licensing = model.moral_licensing_strength(
    moral_licensing_effect, claim_verifiability, env_self_identity
)
gap = probs["positive"] - probs["control"]

# --- Top-line metrics --------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Control", f"{probs['control']:.1%}")
c2.metric("Positive framing", f"{probs['positive']:.1%}", f"{gap:+.1%} vs control")
c3.metric("Accurate disclosure", f"{probs['disclosure']:.1%}",
          f"{probs['disclosure'] - probs['control']:+.1%} vs control")
c4.metric("Moral-licensing strength", f"{licensing:.3f}")

# --- Bar chart of framing conditions ----------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Upgrade probability by framing condition")
    fig, ax = plt.subplots(figsize=(6, 4))
    conds = list(model.CONDITIONS)
    colors = ["#6c757d", "#d1495b", "#2a9d8f"]
    bars = ax.bar([model.CONDITION_LABELS[c] for c in conds],
                  [probs[c] for c in conds], color=colors)
    for rect, c in zip(bars, conds):
        ax.text(rect.get_x() + rect.get_width() / 2, probs[c] + 0.01,
                f"{probs[c]:.0%}", ha="center", va="bottom")
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax.set_ylim(0, 1)
    ax.set_ylabel("Upgrade probability")
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=15, ha="right")
    st.pyplot(fig)

# --- Sensitivity curve over credit-to-income --------------------------------
with right:
    st.subheader("Sensitivity to credit-to-income ratio")
    grid = [i / 100 for i in range(0, 51)]
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    for cond, color in zip(conds, colors):
        ys = [
            model.upgrade_probability(params, cond, credit_to_income=cy, specificity=specificity)
            for cy in grid
        ]
        ax2.plot(grid, ys, label=model.CONDITION_LABELS[cond], color=color, linewidth=2)
    ax2.axvline(credit_to_income, color="#adb5bd", linestyle="--", linewidth=1)
    ax2.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax2.set_ylim(0, 1)
    ax2.set_xlim(0, 0.5)
    ax2.set_xlabel("Credit-to-income ratio  C/Y")
    ax2.set_ylabel("Upgrade probability")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.legend(fontsize=8, frameon=False)
    st.pyplot(fig2)

with st.expander("Model formula & assumptions"):
    st.latex(r"P(\text{upgrade}\mid f) = \Phi\!\left[\,v(C/Y) - \delta\kappa "
             r"+ \gamma\,\phi(f)\,(1-V)\,(1-\omega)\,\right]")
    st.markdown(
        """
- **v(C/Y)** — concave utility from the trade-in credit, scaled by present bias β.
- **φ(f)** — framing term: 0 (control), +1 (positive framing), or a logistic
  function of disclosure specificity *s* relative to threshold *s\\** for accurate disclosure.
- Positive "green" framing engages moral licensing and **raises** the upgrade
  probability; accurate, specific disclosure **lowers** it.

This is a stylized simulation intended to generate testable predictions — not a
calibrated forecast of real consumer behavior.
        """
    )
