"""Reproduce the synthetic bilateral-Pcom topology experiment."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from scipy.special import ndtr


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "protocol_freeze_v1.json"
PROTOCOL_SHA = "a20c6faa098e440616beba4182b97706b174a8495f0f9b42cb1df3b2e9e7d7b9"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_protocol():
    if sha256(PROTOCOL) != PROTOCOL_SHA:
        raise ValueError("Frozen protocol has changed")
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def solved_topology_flows(source, distal, feeder, states, open_conductance):
    """Solve the full topology family with one common source/outlet array per case."""
    laplacians = np.zeros((len(states), 3, 3))
    for idx, state in enumerate(states):
        for anterior, opened in enumerate(state):
            if opened:
                edge = np.eye(3)[anterior] - np.eye(3)[2]
                laplacians[idx] += open_conductance * np.outer(edge, edge)
    diagonal = np.eye(3)[None, :, :] * (1 / feeder + 1 / distal)[:, :, None]
    matrix = diagonal[:, None] + laplacians[None, :]
    rhs = np.broadcast_to((source / feeder)[:, None, :, None], (*matrix.shape[:-1], 1))
    nodal = np.linalg.solve(matrix, rhs)[..., 0]
    outlet_flow = nodal / distal[:, None]
    branch_net_flow = np.einsum("tij,ntj->nti", laplacians, nodal)
    residual = (source[:, None] - nodal) / feeder - outlet_flow - branch_net_flow
    if not np.isfinite(outlet_flow).all() or not (outlet_flow > 0).all():
        raise ValueError("A synthetic outlet is physically invalid")
    return outlet_flow, float(np.max(np.abs(residual)))


def predicted_weights(cues, input_probability, states):
    """Condition exclusively on the upstream cue using the frozen probability lookup."""
    p = np.asarray(input_probability)[cues]
    per_side = np.where(states[None, :, :] == 1, p[:, None, :], 1 - p[:, None, :])
    weights = per_side.prod(axis=-1)
    if not np.allclose(weights.sum(axis=1), 1, atol=1e-12, rtol=0):
        raise ValueError("Weights fail normalization")
    return {
        "fixed_bilateral_open_template": np.broadcast_to(np.eye(4)[3], weights.shape),
        "single_MAP_proxy": np.eye(4)[np.argmax(weights, axis=1)],
        "weighted_candidate_topologies": weights,
    }


def abs_gaussian(mean, noise):
    z = mean / noise
    return noise * np.sqrt(2 / np.pi) * np.exp(-z * z / 2) + mean * (2 * ndtr(z) - 1)


def mixture_quantile(flow, weights, noise, p):
    left = flow.min(axis=1) - 10 * noise
    right = flow.max(axis=1) + 10 * noise
    for _ in range(48):
        mid = (left + right) / 2
        cdf = (weights[:, :, None] * ndtr((mid[:, None] - flow) / noise)).sum(axis=1)
        left = np.where(cdf < p, mid, left)
        right = np.where(cdf < p, right, mid)
    return (left + right) / 2


def score(held_out, flow, weights, noise):
    by_mean = np.einsum("nt,nti->ni", weights, flow)
    first = (weights[:, :, None] * abs_gaussian(held_out[:, None] - flow, noise)).sum(axis=1)
    terms = abs_gaussian(flow[:, :, None] - flow[:, None, :], np.sqrt(2) * noise)
    second = np.einsum("nt,ns,ntsi->ni", weights, weights, terms)
    crps = (first - second / 2).mean(axis=1)
    low = mixture_quantile(flow, weights, noise, 0.05)
    high = mixture_quantile(flow, weights, noise, 0.95)
    return crps, {
        "case_mean_CRPS": float(crps.mean()),
        "mean_absolute_error_predictive_mean": float(np.mean(np.abs(held_out - by_mean))),
        "mean_90pct_marginal_interval_coverage": float(np.mean((low <= held_out) & (held_out <= high))),
        "mean_90pct_marginal_interval_width": float(np.mean(high - low)),
    }


def experiment(config):
    graph, design = config["graph"], config["design"]
    states = np.asarray(graph["topology_states"])
    feeder = np.asarray(graph["feed_resistance"])
    noise = graph["held_out_observation_noise_sd"]
    n = design["test_cases_per_regime"]
    rng = np.random.Generator(np.random.PCG64(design["seed"]))
    bootstrap = np.random.Generator(np.random.PCG64(740621))
    signal_check = abs_gaussian(0, noise) - abs_gaussian(0, noise * np.sqrt(2)) / 2
    if not np.isclose(signal_check, noise * (np.sqrt(2) - 1) / np.sqrt(np.pi), atol=1e-12, rtol=0):
        raise ValueError("Normal CRPS identity did not hold")

    results = {}
    for regime in design["regimes"]:
        ranges = np.asarray(graph["distal_resistance_ranges"])
        distal = rng.uniform(ranges[:, 0], ranges[:, 1], size=(n, 3))
        center = rng.uniform(*graph["central_pressure_range"], size=(n, 1))
        sources = center * (1 + feeder / distal)
        if regime["asymmetric"]:
            sources[:, 1] -= rng.uniform(*graph["asymmetric_right_inlet_pressure_decrement"], n)
        flows, residual = solved_topology_flows(sources, distal, feeder, states, graph["active_Pcom_conductance"])
        if residual >= 1e-10:
            raise ValueError("Mass balance failed")
        cues = rng.integers(0, 2, size=(n, 2))
        predictions = predicted_weights(cues, regime["input_open_prob_given_binary_cue"], states)

        # No target or gate decision enters the model. The target is drawn after the predictions.
        latent_open = rng.uniform(size=(n, 2)) < np.asarray(regime["truth_open_prob_given_binary_cue"])[cues]
        true_index = latent_open @ [2, 1]
        held_out = flows[np.arange(n), true_index] + rng.normal(scale=noise, size=(n, 3))
        per_case, summaries = {}, {}
        for arm, weights in predictions.items():
            per_case[arm], summaries[arm] = score(held_out, flows, weights, noise)
        spread = np.ptp(flows, axis=1)
        if not regime["asymmetric"] and (
            spread.max() >= 1e-10
            or np.max(np.ptp(np.stack(list(per_case.values())), axis=0)) >= 1e-10
        ):
            raise ValueError("The balanced control is not invariant to topology")
        indexes = bootstrap.integers(0, n, size=(2000, n))
        comparisons = {}
        for comparator in ("single_MAP_proxy", "fixed_bilateral_open_template"):
            delta = per_case["weighted_candidate_topologies"] - per_case[comparator]
            comparisons[f"candidates_minus_{comparator}"] = {
                "paired_CRPS_difference": float(delta.mean()),
                "descriptive_95pct_case_bootstrap_interval": np.quantile(delta[indexes].mean(axis=1), [0.025, 0.975]).tolist(),
            }
        results[regime["name"]] = {
            "cases": n,
            "mean_topology_flow_range": float(spread.mean()),
            "max_topology_flow_range": float(spread.max()),
            "max_abs_mass_residual": residual,
            "scores": summaries,
            "comparisons": comparisons,
        }
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write scores to a new JSON file")
    args = parser.parse_args(argv)

    start_cpu = time.process_time()
    start_wall = time.perf_counter()
    config = read_protocol()
    output = {
        "protocol_sha256": PROTOCOL_SHA,
        "script_sha256": sha256(Path(__file__)),
        "results": experiment(config),
        "cpu_seconds": time.process_time() - start_cpu,
        "elapsed_seconds": time.perf_counter() - start_wall,
        "patient_payload_reads": 0,
        "protected_holdout_access": 0,
        "new_fits": 0,
        "clinical_Strong3D_inference": 0,
        "scope": "Generated flow observations and fixed probability scenarios in a shared resistance network",
    }
    serialized = json.dumps(output, indent=2, allow_nan=False)
    if args.output is None:
        print(serialized)
    else:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(serialized + "\n")


if __name__ == "__main__":
    main()
