"""
figures.py
==========

Generates the project's charts as PNG files in ./figures.

Run it directly to (re)build every figure:

    python figures.py

Each plotting function returns a matplotlib Figure so the notebook can reuse
them inline. The same functions back the four required charts (plus the
optional present-bias sensitivity chart) described in the PRD.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

import model

FIGURES_DIR = Path(__file__).resolve().parent / "figures"

# A simple, academic look: muted palette, light grid, no chart junk.
CONDITION_COLORS = {
    "control": "#6c757d",     # grey  — no framing
    "positive": "#d1495b",    # red   — "green" framing that nudges upgrades
    "disclosure": "#2a9d8f",  # teal  — accurate disclosure
}
MARKET_COLORS = {
    "United States": "#1d3557",
    "India": "#e76f51",
}


def _apply_academic_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 160,
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.6,
            "legend.frameon": False,
        }
    )


def _percent_axis(ax) -> None:
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax.set_ylim(0, 1)


# ---------------------------------------------------------------------------
# Chart 1 — Upgrade probability by framing condition and market.
# ---------------------------------------------------------------------------

def chart_framing_comparison(markets: Dict[str, model.MarketParameters]):
    _apply_academic_style()
    conditions = list(model.CONDITIONS)
    names = list(markets.keys())

    n_groups = len(conditions)
    n_markets = len(names)
    width = 0.8 / n_markets

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(n_groups)
    for j, name in enumerate(names):
        probs = model.upgrade_probabilities(markets[name])
        heights = [probs[c] for c in conditions]
        offsets = [i + (j - (n_markets - 1) / 2) * width for i in x]
        bars = ax.bar(offsets, heights, width=width,
                      label=name, color=MARKET_COLORS.get(name))
        for rect, h in zip(bars, heights):
            ax.text(rect.get_x() + rect.get_width() / 2, h + 0.015,
                    f"{h:.0%}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(list(x))
    ax.set_xticklabels([model.CONDITION_LABELS[c] for c in conditions])
    _percent_axis(ax)
    ax.set_ylabel("Predicted upgrade probability")
    ax.set_title("Upgrade probability by environmental framing condition")
    ax.legend(title="Market")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Chart 2 — Moral licensing strength vs. claim verifiability.
# ---------------------------------------------------------------------------

def chart_licensing_vs_verifiability(markets: Dict[str, model.MarketParameters]):
    _apply_academic_style()
    grid = [i / 100 for i in range(0, 101)]

    fig, ax = plt.subplots(figsize=(8, 5))
    for name, params in markets.items():
        strength = [
            model.moral_licensing_strength(
                params.moral_licensing_effect, v, params.env_self_identity, framing=1.0
            )
            for v in grid
        ]
        ax.plot(grid, strength, label=name, color=MARKET_COLORS.get(name), linewidth=2)
        ax.scatter([params.claim_verifiability],
                   [model.moral_licensing_strength(
                       params.moral_licensing_effect,
                       params.claim_verifiability,
                       params.env_self_identity)],
                   color=MARKET_COLORS.get(name), zorder=5, s=40)

    ax.set_xlabel("Claim verifiability  V")
    ax.set_ylabel("Moral-licensing strength  γ·(1−V)·(1−ω)")
    ax.set_title("Verifiable claims leave less room for moral licensing")
    ax.set_xlim(0, 1)
    ax.legend(title="Market  (dot = baseline)")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Chart 3 — Upgrade probability across credit-to-income ratios.
# ---------------------------------------------------------------------------

def chart_upgrade_vs_credit(markets: Dict[str, model.MarketParameters]):
    _apply_academic_style()
    grid = [i / 100 for i in range(0, 51)]  # C/Y from 0 to 0.50

    fig, ax = plt.subplots(figsize=(8, 5))
    styles = {"control": "--", "positive": "-", "disclosure": ":"}
    for name, params in markets.items():
        for cond in model.CONDITIONS:
            probs = [
                model.upgrade_probability(params, cond, credit_to_income=cy)
                for cy in grid
            ]
            ax.plot(grid, probs,
                    styles[cond],
                    color=MARKET_COLORS.get(name),
                    linewidth=1.8,
                    label=f"{name} — {model.CONDITION_LABELS[cond]}")

    ax.set_xlabel("Trade-in credit-to-income ratio  C/Y")
    _percent_axis(ax)
    ax.set_ylabel("Predicted upgrade probability")
    ax.set_title("Upgrade probability rises with trade-in credit")
    ax.set_xlim(0, 0.5)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Chart 4 — Accurate-disclosure effect across information specificity.
# ---------------------------------------------------------------------------

def chart_disclosure_specificity(markets: Dict[str, model.MarketParameters]):
    _apply_academic_style()
    grid = [i / 100 for i in range(0, 101)]

    fig, ax = plt.subplots(figsize=(8, 5))
    for name, params in markets.items():
        probs = [
            model.upgrade_probability(params, "disclosure", specificity=s)
            for s in grid
        ]
        ax.plot(grid, probs, color=MARKET_COLORS.get(name), linewidth=2, label=name)
        # reference: control level (no framing at all)
        control = model.upgrade_probability(params, "control")
        ax.axhline(control, color=MARKET_COLORS.get(name),
                   linestyle=":", linewidth=1, alpha=0.6)
        ax.axvline(params.specificity_threshold, color="#adb5bd",
                   linestyle="--", linewidth=1, alpha=0.7)

    ax.set_xlabel("Information specificity of the disclosure  s")
    _percent_axis(ax)
    ax.set_ylabel("Predicted upgrade probability")
    ax.set_title("Vague disclosure licenses; specific disclosure suppresses")
    ax.set_xlim(0, 1)
    ax.legend(title="Market  (dotted = control level)")
    ax.text(0.51, 0.04, "specificity threshold s*", color="#6c757d", fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Chart 5 (optional) — Sensitivity to present bias.
# ---------------------------------------------------------------------------

def chart_present_bias_sensitivity(markets: Dict[str, model.MarketParameters]):
    _apply_academic_style()
    grid = [0.6 + i / 100 for i in range(0, 81)]  # beta from 0.6 to 1.4

    fig, ax = plt.subplots(figsize=(8, 5))
    for name, params in markets.items():
        probs = []
        for beta in grid:
            tweaked = model.MarketParameters(**{**params.as_dict(), "present_bias": beta})
            probs.append(model.upgrade_probability(tweaked, "positive"))
        ax.plot(grid, probs, color=MARKET_COLORS.get(name), linewidth=2, label=name)
        ax.scatter([params.present_bias],
                   [model.upgrade_probability(params, "positive")],
                   color=MARKET_COLORS.get(name), zorder=5, s=40)

    ax.set_xlabel("Present-bias weight on the immediate credit  β")
    _percent_axis(ax)
    ax.set_ylabel("Upgrade probability (positive framing)")
    ax.set_title("More present-biased consumers upgrade more readily")
    ax.legend(title="Market  (dot = baseline)")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Build everything.
# ---------------------------------------------------------------------------

ALL_CHARTS = {
    "01_framing_comparison": chart_framing_comparison,
    "02_licensing_vs_verifiability": chart_licensing_vs_verifiability,
    "03_upgrade_vs_credit": chart_upgrade_vs_credit,
    "04_disclosure_specificity": chart_disclosure_specificity,
    "05_present_bias_sensitivity": chart_present_bias_sensitivity,
}


def build_all(out_dir: Path = FIGURES_DIR) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    markets = model.load_parameters()
    written: List[Path] = []
    for stem, fn in ALL_CHARTS.items():
        fig = fn(markets)
        path = out_dir / f"{stem}.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        written.append(path)
        print(f"wrote {path.relative_to(out_dir.parent)}")
    return written


if __name__ == "__main__":
    build_all()
