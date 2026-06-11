"""
model.py
========

Core simulation engine for the Smartphone Upgrade Probability Model.

The model estimates the probability that a consumer upgrades their smartphone
under one of three environmental-information conditions:

    Control            -> no environmental framing
    Positive framing   -> manufacturer presents the trade-in as "green"
    Accurate disclosure-> consumer receives specific environmental-cost info

The central equation (see README / PRD section 7) is:

    P(upgrade | f) = Phi[ v(C/Y) - kappa + gamma * phi(f) * (1 - V) * (1 - omega) ]

where

    C/Y     trade-in credit-to-income ratio
    v(C/Y)  utility from the trade-in credit relative to income
    kappa   baseline resistance to upgrading (discounted by the discount factor)
    gamma   moral-licensing effect size
    phi(f)  framing-condition effect (depends on the information condition)
    V       claim verifiability  (0 = unverifiable, 1 = fully verifiable)
    omega   environmental self-identity weight (0..1)
    Phi     standard normal cumulative distribution function

IMPORTANT
---------
This is a *theoretical simulation*. The parameters are stylized and are meant
to generate testable predictions, not to forecast real individual behavior.

The module deliberately depends only on the Python standard library so that the
core model is trivial to install and import anywhere. numpy / pandas /
matplotlib are only needed for the notebook, the charts and the Streamlit app.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List

# ---------------------------------------------------------------------------
# Module-level default constants.
#
# These are the "structural" constants of the simulation. They are kept here
# (rather than in parameters.csv) because they describe the *shape* of the
# model rather than a market-specific assumption. Override them by passing
# explicit arguments to the functions below.
# ---------------------------------------------------------------------------

CREDIT_SENSITIVITY = 2.5        # scales how strongly trade-in credit feeds utility
DISCLOSURE_STEEPNESS = 0.12     # how sharply accurate disclosure flips sign at threshold
DEFAULT_SPECIFICITY = 0.80      # default information specificity for "accurate disclosure"

# The three information conditions the model compares.
CONDITIONS = ("control", "positive", "disclosure")

CONDITION_LABELS = {
    "control": "Control (no framing)",
    "positive": "Positive framing",
    "disclosure": "Accurate disclosure",
}


# ---------------------------------------------------------------------------
# Standard normal CDF (Phi) using the standard-library error function.
# ---------------------------------------------------------------------------

def normal_cdf(z: float) -> float:
    """Standard normal cumulative distribution function, Phi(z).

    Implemented with math.erf so that the model needs no third-party
    dependency. Accepts a scalar and returns a probability in (0, 1).
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ---------------------------------------------------------------------------
# Parameter container.
# ---------------------------------------------------------------------------

@dataclass
class MarketParameters:
    """Baseline behavioral parameters for a single market.

    Mirrors one row of data/parameters.csv.
    """
    market: str
    claim_verifiability: float       # V      in [0, 1]
    env_self_identity: float         # omega  in [0, 1]
    moral_licensing_effect: float    # gamma  >= 0
    present_bias: float              # beta   > 0  (weight on the immediate credit)
    discount_factor: float           # delta  in (0, 1]  (weight on future resistance)
    baseline_resistance: float       # kappa  >= 0
    specificity_threshold: float     # s*     in [0, 1]
    credit_to_income: float          # C/Y    >= 0  (baseline trade-in credit / income)

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 1. Trade-in utility:  v(C/Y)
# ---------------------------------------------------------------------------

def trade_in_utility(
    credit_to_income: float,
    present_bias: float = 1.0,
    credit_sensitivity: float = CREDIT_SENSITIVITY,
) -> float:
    """Utility a consumer derives from the trade-in credit, v(C/Y).

    The function is concave in the credit-to-income ratio (square-root form),
    capturing diminishing marginal utility of money. ``present_bias`` (beta)
    multiplies the immediate, salient credit: present-biased / impulsive
    consumers (beta > 1) over-weight the up-front reward.

    Parameters
    ----------
    credit_to_income : C/Y, the trade-in credit as a fraction of income.
    present_bias     : beta, multiplier on the immediate reward.
    credit_sensitivity : structural scale constant.
    """
    if credit_to_income < 0:
        raise ValueError("credit_to_income must be non-negative")
    return present_bias * credit_sensitivity * math.sqrt(credit_to_income)


# ---------------------------------------------------------------------------
# 2. Framing-condition term:  phi(f)
# ---------------------------------------------------------------------------

def framing_term(
    condition: str,
    specificity: float = DEFAULT_SPECIFICITY,
    specificity_threshold: float = 0.5,
    steepness: float = DISCLOSURE_STEEPNESS,
) -> float:
    """Framing-condition multiplier phi(f).

    Returns a value that scales the moral-licensing channel:

        control     -> 0.0
            No environmental framing, so no licensing channel is activated.

        positive    -> +1.0
            Manufacturer's "green" claim fully engages moral licensing:
            the consumer feels the environmental cost is already handled.

        disclosure  -> in [-1, +1], depending on information specificity
            Vague disclosure (specificity << threshold) still reads like a
            feel-good claim and licenses upgrading (phi -> +1). As the
            disclosure becomes more specific and passes the threshold, it
            shifts to *suppressing* upgrades (phi -> -1) because the consumer
            now confronts a concrete environmental cost.

    The disclosure curve is a logistic in (specificity - threshold):

        phi = 1 - 2 * logistic((specificity - threshold) / steepness)
    """
    condition = condition.lower()
    if condition == "control":
        return 0.0
    if condition == "positive":
        return 1.0
    if condition == "disclosure":
        x = (specificity - specificity_threshold) / steepness
        logistic = 1.0 / (1.0 + math.exp(-x))
        return 1.0 - 2.0 * logistic
    raise ValueError(
        f"Unknown condition {condition!r}; expected one of {CONDITIONS}"
    )


# ---------------------------------------------------------------------------
# 3 & 5. Moral-licensing strength:  gamma * phi(f) * (1 - V) * (1 - omega)
# ---------------------------------------------------------------------------

def moral_licensing_strength(
    moral_licensing_effect: float,
    claim_verifiability: float,
    env_self_identity: float,
    framing: float = 1.0,
) -> float:
    """Strength of the moral-licensing push on the latent upgrade score.

    This is the term  gamma * phi(f) * (1 - V) * (1 - omega).

    With ``framing=1.0`` (the default) it returns the *capacity* for moral
    licensing under positive framing, i.e. how much room a "green" claim has
    to nudge a consumer toward upgrading. It shrinks when claims are easy to
    verify (V -> 1) or when the consumer has a strong environmental identity
    (omega -> 1).
    """
    return moral_licensing_effect * framing * (1.0 - claim_verifiability) * (1.0 - env_self_identity)


# ---------------------------------------------------------------------------
# 4. Latent upgrade score:  z
# ---------------------------------------------------------------------------

def latent_upgrade_score(
    params: MarketParameters,
    condition: str,
    credit_to_income: float | None = None,
    specificity: float = DEFAULT_SPECIFICITY,
    credit_sensitivity: float = CREDIT_SENSITIVITY,
) -> float:
    """Latent (pre-Phi) upgrade score z for a market under a condition.

        z = v(C/Y) - delta * kappa + gamma * phi(f) * (1 - V) * (1 - omega)

    The baseline resistance kappa is weighted by the discount factor delta:
    resistance is experienced partly in the future, so a more patient consumer
    (delta -> 1) feels it more fully.
    """
    cy = params.credit_to_income if credit_to_income is None else credit_to_income

    utility = trade_in_utility(cy, params.present_bias, credit_sensitivity)
    resistance = params.discount_factor * params.baseline_resistance
    phi = framing_term(
        condition,
        specificity=specificity,
        specificity_threshold=params.specificity_threshold,
    )
    licensing = moral_licensing_strength(
        params.moral_licensing_effect,
        params.claim_verifiability,
        params.env_self_identity,
        framing=phi,
    )
    return utility - resistance + licensing


# ---------------------------------------------------------------------------
# 6. Upgrade probability:  Phi(z)
# ---------------------------------------------------------------------------

def upgrade_probability(
    params: MarketParameters,
    condition: str,
    credit_to_income: float | None = None,
    specificity: float = DEFAULT_SPECIFICITY,
    credit_sensitivity: float = CREDIT_SENSITIVITY,
) -> float:
    """Probability of upgrading, P(upgrade | f) = Phi(z)."""
    z = latent_upgrade_score(
        params,
        condition,
        credit_to_income=credit_to_income,
        specificity=specificity,
        credit_sensitivity=credit_sensitivity,
    )
    return normal_cdf(z)


def upgrade_probabilities(
    params: MarketParameters,
    credit_to_income: float | None = None,
    specificity: float = DEFAULT_SPECIFICITY,
) -> Dict[str, float]:
    """Convenience helper: probability under every condition for one market."""
    return {
        cond: upgrade_probability(
            params, cond, credit_to_income=credit_to_income, specificity=specificity
        )
        for cond in CONDITIONS
    }


def licensing_probability_gap(params: MarketParameters) -> float:
    """How much positive framing raises upgrade probability vs. the control.

    A behaviorally intuitive read-out of moral licensing: the difference in
    predicted upgrade probability between positive framing and the control.
    """
    return (
        upgrade_probability(params, "positive")
        - upgrade_probability(params, "control")
    )


# ---------------------------------------------------------------------------
# CSV loading.
# ---------------------------------------------------------------------------

# Maps CSV column names -> MarketParameters fields. Kept explicit so the CSV
# can use human-readable headers.
_CSV_FIELDS = {
    "market": "market",
    "claim_verifiability": "claim_verifiability",
    "env_self_identity": "env_self_identity",
    "moral_licensing_effect": "moral_licensing_effect",
    "present_bias": "present_bias",
    "discount_factor": "discount_factor",
    "baseline_resistance": "baseline_resistance",
    "specificity_threshold": "specificity_threshold",
    "credit_to_income": "credit_to_income",
}

DEFAULT_PARAMS_PATH = Path(__file__).resolve().parent / "data" / "parameters.csv"


def load_parameters(path: str | Path = DEFAULT_PARAMS_PATH) -> Dict[str, MarketParameters]:
    """Load baseline parameters for every market from a CSV file.

    Returns a dict keyed by market name.
    """
    path = Path(path)
    markets: Dict[str, MarketParameters] = {}
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            kwargs = {field: row[col] for col, field in _CSV_FIELDS.items()}
            params = MarketParameters(
                market=kwargs["market"],
                claim_verifiability=float(kwargs["claim_verifiability"]),
                env_self_identity=float(kwargs["env_self_identity"]),
                moral_licensing_effect=float(kwargs["moral_licensing_effect"]),
                present_bias=float(kwargs["present_bias"]),
                discount_factor=float(kwargs["discount_factor"]),
                baseline_resistance=float(kwargs["baseline_resistance"]),
                specificity_threshold=float(kwargs["specificity_threshold"]),
                credit_to_income=float(kwargs["credit_to_income"]),
            )
            markets[params.market] = params
    return markets


def list_markets(path: str | Path = DEFAULT_PARAMS_PATH) -> List[str]:
    """Convenience: the market names available in the parameters file."""
    return list(load_parameters(path).keys())


# ---------------------------------------------------------------------------
# Tiny self-check when run directly:  python model.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    markets = load_parameters()
    print("Smartphone Upgrade Probability Model — baseline simulation\n")
    header = f"{'Market':<16}{'Control':>10}{'Positive':>10}{'Disclosure':>12}{'Licensing gap':>15}"
    print(header)
    print("-" * len(header))
    for name, params in markets.items():
        probs = upgrade_probabilities(params)
        gap = licensing_probability_gap(params)
        print(
            f"{name:<16}"
            f"{probs['control']:>9.1%} "
            f"{probs['positive']:>9.1%} "
            f"{probs['disclosure']:>11.1%} "
            f"{gap:>+14.1%}"
        )
    print(
        "\nNote: positive 'green' framing raises predicted upgrade probability "
        "(moral licensing);\naccurate, specific disclosure lowers it."
    )
