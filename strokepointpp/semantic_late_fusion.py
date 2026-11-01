"""Parameter-only semantic probability fusion; no fitting or asset loading.

This optional demonstration keeps each source's scaler and binary readout in
its own latent coordinate system, then combines comparable probabilities.
It is not used to replace the frozen Gate inference adapter automatically.
The pure-Python arithmetic is a reference interface, not bitwise certification
of any PyTorch, NumPy or scikit-learn runtime.
"""
from __future__ import annotations

import math
from collections.abc import Sequence


def _finite_values(values: Sequence[float], name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if not result or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{name} must contain nonempty finite numeric values")
    return result


def stable_sigmoid(logit: float) -> float:
    """Convert a finite binary logit without overflowing at large magnitudes."""
    value = float(logit)
    if not math.isfinite(value):
        raise ValueError("logit must be finite")
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def source_presence_probability(
    features: Sequence[float],
    *,
    feature_mean: Sequence[float],
    feature_scale: Sequence[float],
    coefficients: Sequence[float],
    intercept: float,
) -> float:
    """Evaluate one caller-bound source-specific standardized binary LR head.

    All values are supplied by the caller. No coefficients, fitted scalers,
    subject lists, checkpoints or workstation paths are bundled here. A
    constant fitted feature is represented using its actual saved scaler scale
    (normally 1 for StandardScaler), not by adding a new arbitrary epsilon.
    """
    x = _finite_values(features, "features")
    mean = _finite_values(feature_mean, "feature_mean")
    scale = _finite_values(feature_scale, "feature_scale")
    weights = _finite_values(coefficients, "coefficients")
    if not (len(x) == len(mean) == len(scale) == len(weights)):
        raise ValueError("All source-specific vectors must have the same length")
    if any(value <= 0 for value in scale):
        raise ValueError("feature_scale must be strictly positive")
    bias = float(intercept)
    if not math.isfinite(bias):
        raise ValueError("intercept must be finite")
    terms = tuple((value - center) / width * weight
                  for value, center, width, weight in zip(x, mean, scale, weights))
    if not all(math.isfinite(value) for value in terms):
        raise ValueError("Standardized source-specific LR terms must be finite")
    return stable_sigmoid(math.fsum((*terms, bias)))


def mean_semantic_probabilities(
    source_probabilities: Sequence[Sequence[float]],
) -> tuple[float, ...]:
    """Mean probabilities over sources, preserving the caller's target order.

    Rows are source-specific outputs and columns are matching semantic binary
    targets. The reviewed development version used four sources and two
    targets. Hidden feature channels are never mixed by this function.
    An output is not a validated patient-error risk or a clinical guarantee.
    """
    rows = tuple(_finite_values(row, "source probabilities") for row in source_probabilities)
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("Provide a nonempty rectangular source-by-target table")
    if any(value < 0 or value > 1 for row in rows for value in row):
        raise ValueError("Probabilities must lie in [0, 1]")
    return tuple(math.fsum(row[column] for row in rows) / len(rows)
                 for column in range(len(rows[0])))
