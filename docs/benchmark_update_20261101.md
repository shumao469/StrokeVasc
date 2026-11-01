# Reviewed development update — 1 November 2026

This versioned update keeps the original Y/Z application and frozen external
evaluation unchanged. It adds an interface repair comparison and a separate
dense-decoder sensitivity analysis. Neither replaces the main application.

## Data role and fixed interface

The interface study uses 20 previously evaluated Lausanne external-DEV
patients, 3 fixed backbone outputs and all 6 prespecified policies: 360
patient–model–policy records. Only aggregate results are released. The 65-person
internal holdout, IXI-HH FINAL and UNC/THU outputs were not reopened for this
update. These DEV data are repeated development, not new independent testing.

`Gate-MRA-SemProb-R1` uses four frozen encoder sources. Each source uses its own
24-person FIT MRA data, its own candidate features, fitted standardizer and two
fixed binary logistic-regression heads. Four source-specific probabilities are
averaged for each semantic target: either-side Pcom presence and third-A2
presence. Hidden feature channels from separately trained encoders are not
averaged. The unique FIT union contains 48 patients within the existing
60-person development pool. The encoders have previously seen these patients
through CT, so these are not out-of-fold features.

The eight heads used fixed L2 logistic regression (`C=1`, `lbfgs`,
`max_iter=2000`), no threshold search and no encoder updates. The hard policy
uses threshold 0.05; the soft policy uses the locked 0.25 setting. Per-source
numerical replay was required before fitting. Complete single-MRA annotation
presence targets were independently checked. The result review passed 44,900
checks across 176 source packets, 8 heads and 360 policy records.

The 1 November interface rebuild recorded Python 3.12.13, NumPy 1.26.4,
PyTorch 2.11.0+cu128 and CUDA 12.8. Fixed encoder extraction used four Torch
threads, TF32 enabled for CUDA matmul and cuDNN, and cuDNN benchmarking off.
These settings belong to this reviewed rebuild, not the historical release
environment; strict base-output replay preceded the head fits. Matching package
versions alone is not numerical certification of another machine.

All policies remain visible:

| Policy | Description |
| --- | --- |
| `NONE` | Frozen model output, without a presence constraint |
| `COUNT8` | Existing point-count filtering comparator |
| `OLD_YZ_HARD0.05` | Original reconstructed single-MRA presence interface, hard gate |
| `OLD_YZ_SOFT0.25` | Original reconstructed presence interface, soft correction |
| `NEW_MRA_LATE_HARD0.05` | New per-source semantic-probability interface, hard gate |
| `NEW_MRA_LATE_SOFT0.25` | New per-source semantic-probability interface, soft correction |

The repaired interface also changes supervision modality and head count.
Therefore the comparison does not isolate feature averaging as the sole cause
of any change. No policy was selected on these DEV results to overwrite the
frozen application.

## Endpoint definitions matter

`sampled_macro_Dice` first averages class Dice within each scan over anatomical
classes nonempty in ground truth **or** prediction; it then averages over
patients. Consequently, eliminating a false-positive-only class can remove a
zero-valued class from the within-scan denominator and increase macro Dice
without making any sampled point correct. The original metric and result
values are retained; this explanation prevents a Dice change from being
misreported as corrected points.

`annotation_absent_FPR` uses classes absent in the complete released annotation,
not classes missed by the 2,048 sampled points. Corrected points, new error
points, patients with any new error and rare true-positive points lost are all
relative to the **same model's** `NONE` policy. Shared physical damage across
different models is not added as independent harm. Recall uses the actual
positive-patient denominator of each branch, which can be small.

The new hard Y/Z interface gives sampled macro Dice 0.6742 versus 0.6701
without a constraint, with **0 corrected and 0 newly incorrect points**. This
does not demonstrate effective point correction. The old hard Y/Z interface
gives 0.6849 and 22 corrected/0 new-error points. New soft Y/Z gives 4
corrected/5 new-error points. On the 3D comparator, `COUNT8` and the old soft
interface each give 5 corrected/0 new-error points; the new hard interface
gives 0/0. Full six-policy results, rare-branch statistics and paired intervals
are retained rather than choosing a DEV winner.

The semantic interface is an engineering repair candidate, with no demonstrated
efficacy advantage over the original Y/Z method. Patient-paired bootstrap
intervals use 2,000 draws and are exploratory 95% intervals, not correction for
multiple endpoints or repeated development. Zero observed errors does not
certify the original 10% population-risk gate or clinical safety.

## AUTO-A: conditional dense-decoder sensitivity

A separate zero-fit analysis completed 40 frozen dense forwards on the same
20-person Lausanne DEV cohort and passed 3,284 independent checks. On the
released native annotation grid, patient-mean foreground Dice was **0.8546**,
patient-mean foreground recall **0.8776**, patient-mean precision **0.8341**,
and identity macro Dice **0.6595**
(exploratory patient-bootstrap 95% CI 0.6351–0.6840), with absent-class FPR
**0.0417** (0.0000–0.1000).
The foreground values are arithmetic means over the 20 patient-level metrics,
not metrics computed by pooling all voxels across patients.

This experiment uses reference-derived ROI and intensity normalization. It is
not end-to-end automatic vessel extraction, full-field deployment or a matched
comparison against the sampled-point identity Dice. A genuinely GT-free
automatic pipeline remains `NOT_ADMITTED` until a prospective full-FOV ROI,
normalization and foreground-input binding is available. No stroke-infarct
U-Net is relabelled as a cerebral-vessel identity baseline.

## Public files and operation

- [Interface aggregate JSON](../results/aggregate/benchmark_20261101_v1.json)
  retains all model/policy summaries and locked paired contrasts.
- [Interface aggregate CSV](../source_data/20261101_interface_aggregate.csv)
  contains 18 cohort-level rows, not patient-level predictions.
- [AUTO-A aggregate JSON](../results/aggregate/auto_a_20261101_v1.json) and
  [CSV](../source_data/20261101_auto_a_aggregate.csv) retain the separate task
  definition.
- [`semantic_late_fusion.py`](../strokepointpp/semantic_late_fusion.py) is a
  parameter-only reference interface with stable binary logits and a semantic
  probability mean. It performs no fitting and contains no trained parameters.
- The local CPU-only viewer has a separate **Development update** tab; its
  existing main results and model defaults remain unchanged.
- [Supplementary Fig. 7](../figures/benchmark_update_20261101/StrokeVasc_SupplementaryFigure_7_20261101.svg)
  shows the per-source semantic interface and all fixed policy results;
  [Supplementary Fig. 8](../figures/benchmark_update_20261101/StrokeVasc_SupplementaryFigure_8_20261101.svg)
  shows the separate conditional dense sensitivity experiment. PNG versions
  are in the same folder. Text in SVG remains editable.
- [Panel-ordered source data](../source_data/figures_20261101) contain the two
  conceptual panel-a definitions and six aggregate panel tables. No patient
  dots, images or case-level rows are released in these new illustrations.

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s apps/tests -v
python -m streamlit run apps/streamlit_app.py --server.address 127.0.0.1 --server.port 8851 --browser.gatherUsageStats false
```

Install `requirements-app.txt` in a separate environment before running the
viewer, as described in the [README](../README.md#interactive-viewer--streamlit).
There is no automatic cloud deployment. The public update includes no patient
IDs, per-case records, original images, caches, fitted scalers, weights or
private manuscript files. Original results, scientific thresholds and STOP
decisions remain unchanged. These experiments support transparent method
comparison, not a new NC/NMI mechanism or a validated stroke application.
