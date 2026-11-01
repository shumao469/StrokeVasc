"""Strict, torch-free loader for the separately versioned development update."""
from __future__ import annotations

import json
import math
from pathlib import Path


MODELS = ("YZ", "BASE3D", "CONCAT")
POLICIES = ("NONE", "COUNT8", "OLD_YZ_HARD0.05", "OLD_YZ_SOFT0.25",
            "NEW_MRA_LATE_HARD0.05", "NEW_MRA_LATE_SOFT0.25")
METRICS = ("sampled_macro_Dice", "annotation_absent_FPR", "recall_native8",
           "recall_native9", "recall_native10", "recall_native15",
           "corrected_points", "new_error_points", "any_new_error", "rare_TP_lost",
           "sampled_baseline_TP_branch_support_lost")
_FORBIDDEN_KEYS = {"patient_id", "patient_ids", "case_id", "case_ids", "source_ids",
    "per_case", "per_patient", "checkpoint", "state_dict", "coefficients",
    "feature_mean", "feature_scale", "access_token", "password", "private_path"}


def _aggregate_only(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in _FORBIDDEN_KEYS:
                raise ValueError("Patient/model-state fields are not aggregate display inputs")
            _aggregate_only(item)
    elif isinstance(value, list):
        for item in value:
            _aggregate_only(item)
    elif isinstance(value, str):
        if ":\\" in value or ":/" in value or "/mnt/" in value or "\\Users\\" in value:
            raise ValueError("Absolute workstation paths are not public aggregate fields")


def validate_development_update(data: dict) -> dict:
    _aggregate_only(data)
    if data.get("schema") != "StrokeVasc_public_development_benchmark_v1":
        raise ValueError("Unexpected development benchmark schema")
    if data.get("n_patients") != 20 or data.get("review", {}).get("qualified") is not True:
        raise ValueError("A reviewed 20-patient DEV aggregate is required")
    if tuple(data.get("model_order", ())) != MODELS or tuple(data.get("policy_order", ())) != POLICIES:
        raise ValueError("All fixed models and policies must be displayed")
    if set(data.get("summaries", {})) != set(MODELS):
        raise ValueError("Unexpected model set")
    for model in MODELS:
        if set(data["summaries"][model]) != set(POLICIES):
            raise ValueError("Incomplete fixed policy set")
        for policy in POLICIES:
            item = data["summaries"][model][policy]
            if set(item) != set(METRICS):
                raise ValueError("Incomplete metric set")
            for statistic in item.values():
                if not 0 <= statistic["n"] <= 20:
                    raise ValueError("Invalid patient support")
                if not all(math.isfinite(float(value)) for value in
                           (statistic["mean"], *statistic["CI95"])):
                    raise ValueError("Invalid aggregate statistic")
    return data


def load_development_update(release: Path) -> tuple[dict, dict]:
    base = release.resolve()
    result = []
    for name in ("benchmark_20261101_v1.json", "auto_a_20261101_v1.json"):
        path = (base / "results/aggregate" / name).resolve()
        if not path.is_relative_to(base) or path.stat().st_size > 512 * 1024:
            raise ValueError("Unexpected aggregate path or file size")
        result.append(json.loads(path.read_text(encoding="utf-8")))
    development, auto = result
    validate_development_update(development)
    _aggregate_only(auto)
    if (auto.get("schema") != "StrokeVasc_public_auto_a_aggregate_v1"
            or auto.get("n_patients") != 20
            or auto.get("review", {}).get("qualified") is not True
            or auto.get("AUTO_B", {}).get("status") != "NOT_ADMITTED"):
        raise ValueError("Unexpected conditional AUTO-A aggregate")
    return development, auto
