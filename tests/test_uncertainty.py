"""Tests for the Monte Carlo uncertainty module.  Run: python -m unittest discover tests"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model import CONDITIONS, load_parameters, upgrade_probabilities  # noqa: E402
from uncertainty import (  # noqa: E402
    PARAMETER_BOUNDS,
    percentile,
    perturb_parameters,
    simulate_market,
)


class PercentileTests(unittest.TestCase):
    def test_endpoints_and_midpoint(self):
        values = [0.0, 1.0, 2.0, 3.0, 4.0]
        self.assertEqual(percentile(values, 0.0), 0.0)
        self.assertEqual(percentile(values, 1.0), 4.0)
        self.assertEqual(percentile(values, 0.5), 2.0)

    def test_interpolates(self):
        self.assertAlmostEqual(percentile([0.0, 10.0], 0.25), 2.5)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            percentile([], 0.5)


class PerturbTests(unittest.TestCase):
    def setUp(self):
        self.us = load_parameters()["United States"]

    def test_zero_noise_returns_baseline(self):
        draw = perturb_parameters(self.us, random.Random(1), rel_sd=0.0)
        self.assertEqual(draw, self.us)

    def test_draws_respect_bounds_under_heavy_noise(self):
        rng = random.Random(2)
        for _ in range(2000):
            draw = perturb_parameters(self.us, rng, rel_sd=1.5)
            for name, (low, high) in PARAMETER_BOUNDS.items():
                value = getattr(draw, name)
                self.assertGreaterEqual(value, low, name)
                if high is not None:
                    self.assertLessEqual(value, high, name)

    def test_fixed_fields_untouched(self):
        draw = perturb_parameters(self.us, random.Random(3), rel_sd=0.5)
        self.assertEqual(draw.market, self.us.market)
        self.assertEqual(draw.specificity_threshold, self.us.specificity_threshold)


class SimulateMarketTests(unittest.TestCase):
    def setUp(self):
        self.markets = load_parameters()

    def test_same_seed_is_reproducible(self):
        us = self.markets["United States"]
        a = simulate_market(us, draws=500, seed=42)
        b = simulate_market(us, draws=500, seed=42)
        self.assertEqual(a, b)

    def test_intervals_bracket_baseline_and_stay_in_unit_range(self):
        for params in self.markets.values():
            res = simulate_market(params, draws=2000, seed=0)
            base = upgrade_probabilities(params)
            for cond in CONDITIONS:
                iv = res.probabilities[cond]
                self.assertAlmostEqual(iv.baseline, base[cond])
                self.assertTrue(0.0 <= iv.low <= iv.baseline <= iv.high <= 1.0, (params.market, cond))

    def test_zero_noise_collapses_interval(self):
        us = self.markets["United States"]
        res = simulate_market(us, draws=50, rel_sd=0.0)
        for cond in CONDITIONS:
            iv = res.probabilities[cond]
            self.assertAlmostEqual(iv.low, iv.high)
        self.assertEqual(res.ordering_share, 1.0)

    def test_core_ordering_is_robust_at_default_noise(self):
        # The headline finding should survive 20% parameter noise in nearly every draw.
        for params in self.markets.values():
            res = simulate_market(params, draws=2000, seed=0)
            self.assertGreater(res.ordering_share, 0.95, params.market)
            self.assertGreater(res.licensing_gap.low, 0.0, params.market)

    def test_invalid_arguments(self):
        us = self.markets["United States"]
        with self.assertRaises(ValueError):
            simulate_market(us, draws=1)
        with self.assertRaises(ValueError):
            simulate_market(us, level=1.0)


if __name__ == "__main__":
    unittest.main()
