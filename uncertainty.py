"""
uncertainty.py
==============

Monte Carlo confidence intervals for the Smartphone Upgrade Probability Model.

The baseline parameters in data/parameters.csv are stylized point estimates.
This module asks: *if every parameter is uncertain, how stable are the
headline results?* It draws many perturbed parameter sets around the baseline,
re-runs the model for each draw, and reports

    * a percentile interval for P(upgrade) under every framing condition,
    * a percentile interval for the licensing gap (positive - control), and
    * the share of draws in which the core ordering holds:
          positive framing > control > accurate disclosure.

Each parameter is perturbed multiplicatively with normal noise,

    theta_draw = theta_baseline * (1 + rel_sd * N(0, 1)),

then clipped to its valid range (e.g. verifiability stays in [0, 1]). The
market name and the specificity threshold s* are left fixed: s* is a property
of the disclosure design rather than of consumers.

Like model.py, this module needs only the Python standard library.

    python uncertainty.py                 # 10,000 draws, 20% relative noise
    python uncertainty.py --draws 2000 --rel-sd 0.1 --seed 7
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, replace
from typing import Dict, List, Sequence, Tuple

from model import (
    CONDITIONS,
    CONDITION_LABELS,
    MarketParameters,
    load_parameters,
    upgrade_probabilities,
)

DEFAULT_DRAWS = 10_000
DEFAULT_REL_SD = 0.20      # 20% relative standard deviation on every parameter
DEFAULT_LEVEL = 0.95       # width of the reported percentile interval

# Valid (low, high) range for each perturbed parameter. ``None`` = unbounded.
PARAMETER_BOUNDS: Dict[str, Tuple[float, float | None]] = {
    "claim_verifiability": (0.0, 1.0),
    "env_self_identity": (0.0, 1.0),
    "moral_licensing_effect": (0.0, None),
    "present_bias": (1e-6, None),
    "discount_factor": (1e-6, 1.0),
    "baseline_resistance": (0.0, None),
    "credit_to_income": (0.0, None),
}


@dataclass
class Interval:
    """A point estimate with a percentile interval from the simulation."""
    baseline: float
    mean: float
    low: float
    high: float


@dataclass
class MarketUncertainty:
    """Monte Carlo summary for one market."""
    market: str
    draws: int
    probabilities: Dict[str, Interval]   # keyed by condition
    licensing_gap: Interval
    ordering_share: float                # share of draws with positive > control > disclosure


def _clip(value: float, bounds: Tuple[float, float | None]) -> float:
    low, high = bounds
    value = max(low, value)
    if high is not None:
        value = min(high, value)
    return value


def perturb_parameters(
    params: MarketParameters,
    rng: random.Random,
    rel_sd: float = DEFAULT_REL_SD,
) -> MarketParameters:
    """Return one randomly perturbed copy of ``params``."""
    if rel_sd < 0:
        raise ValueError("rel_sd must be non-negative")
    changes = {
        name: _clip(getattr(params, name) * (1.0 + rel_sd * rng.gauss(0.0, 1.0)), bounds)
        for name, bounds in PARAMETER_BOUNDS.items()
    }
    return replace(params, **changes)


def percentile(sorted_values: Sequence[float], q: float) -> float:
    """Linear-interpolated percentile of pre-sorted values, q in [0, 1]."""
    if not sorted_values:
        raise ValueError("percentile of empty sequence")
    pos = q * (len(sorted_values) - 1)
    lower = int(pos)
    upper = min(lower + 1, len(sorted_values) - 1)
    frac = pos - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def _interval(baseline: float, samples: List[float], level: float) -> Interval:
    samples = sorted(samples)
    tail = (1.0 - level) / 2.0
    return Interval(
        baseline=baseline,
        mean=sum(samples) / len(samples),
        low=percentile(samples, tail),
        high=percentile(samples, 1.0 - tail),
    )


def simulate_market(
    params: MarketParameters,
    draws: int = DEFAULT_DRAWS,
    rel_sd: float = DEFAULT_REL_SD,
    level: float = DEFAULT_LEVEL,
    seed: int | None = 0,
) -> MarketUncertainty:
    """Run the Monte Carlo simulation for a single market."""
    if draws < 2:
        raise ValueError("draws must be at least 2")
    if not 0.0 < level < 1.0:
        raise ValueError("level must be between 0 and 1")

    rng = random.Random(seed)
    samples: Dict[str, List[float]] = {cond: [] for cond in CONDITIONS}
    gaps: List[float] = []
    ordered = 0

    for _ in range(draws):
        probs = upgrade_probabilities(perturb_parameters(params, rng, rel_sd))
        for cond in CONDITIONS:
            samples[cond].append(probs[cond])
        gaps.append(probs["positive"] - probs["control"])
        if probs["positive"] > probs["control"] > probs["disclosure"]:
            ordered += 1

    base = upgrade_probabilities(params)
    return MarketUncertainty(
        market=params.market,
        draws=draws,
        probabilities={
            cond: _interval(base[cond], samples[cond], level) for cond in CONDITIONS
        },
        licensing_gap=_interval(base["positive"] - base["control"], gaps, level),
        ordering_share=ordered / draws,
    )


def simulate_all(
    markets: Dict[str, MarketParameters] | None = None,
    draws: int = DEFAULT_DRAWS,
    rel_sd: float = DEFAULT_REL_SD,
    level: float = DEFAULT_LEVEL,
    seed: int | None = 0,
) -> Dict[str, MarketUncertainty]:
    """Run :func:`simulate_market` for every market (default: parameters.csv)."""
    markets = load_parameters() if markets is None else markets
    return {
        name: simulate_market(params, draws=draws, rel_sd=rel_sd, level=level, seed=seed)
        for name, params in markets.items()
    }


def _format_interval(iv: Interval) -> str:
    return f"{iv.baseline:6.1%} [{iv.low:6.1%}, {iv.high:6.1%}]"


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    parser.add_argument("--rel-sd", type=float, default=DEFAULT_REL_SD,
                        help="relative standard deviation applied to each parameter")
    parser.add_argument("--level", type=float, default=DEFAULT_LEVEL)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    results = simulate_all(draws=args.draws, rel_sd=args.rel_sd,
                           level=args.level, seed=args.seed)

    print(
        f"Monte Carlo uncertainty — {args.draws:,} draws, "
        f"{args.rel_sd:.0%} relative noise, {args.level:.0%} intervals\n"
    )
    for res in results.values():
        print(res.market)
        for cond in CONDITIONS:
            print(f"  {CONDITION_LABELS[cond]:<24}{_format_interval(res.probabilities[cond])}")
        print(f"  {'Licensing gap':<24}{_format_interval(res.licensing_gap)}")
        print(f"  Ordering holds (positive > control > disclosure) in {res.ordering_share:.1%} of draws\n")


if __name__ == "__main__":
    main()
