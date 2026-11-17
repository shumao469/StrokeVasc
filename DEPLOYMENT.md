# StrokeVasc research-results viewer

This CPU-only Streamlit app displays **packaged, independently reviewed aggregate results** and released PNG illustrations. Its views cover StrokeVasc Gate and the fixed volumetric and fusion comparators.

See the [StrokeVasc repository](https://github.com/shumao469/StrokeVasc) and the
[Windows and WSL quick start](README.md#interactive-app).

## Required packaged files

The separate **Development update** tab uses only
`results/aggregate/benchmark_20261101_v1.json` and
`results/aggregate/auto_a_20261101_v1.json`. It retains all six fixed policies
and distinguishes reference-ROI dense sensitivity from sampled-point labeling.
It does not replace the original cohort panels or run the eight-head fitting
experiment. A missing new aggregate is reported without affecting the frozen
main results. No cloud deployment is performed by this update.

- Entry point: `apps/streamlit_app.py`
- Dependencies: `requirements-app.txt`
- Reviewed aggregate: either `results/aggregate/DEV_FINAL_four_arm_summary_v1.json`, or the two independently reviewed wrappers `externalDEV_Lausanne.json` and `externalFINAL_IXI_HH.json` in that directory (`data/aggregate/` is a compatibility fallback)
- Figures: `figures/main/*.png`, optional `figures/extended_data/*.png`
- Anonymous illustrative previews: `assets/cases/CaseA*.png` and `CaseB*.png`

The aggregate must retain all four fixed arms and mark each cohort as independently reviewed. The viewer never reads the original project, raw images, protected 65-person cohort, original Y/Z files, or a live training directory. Missing aggregate/figure assets are reported explicitly rather than replaced with invented results. Patient/source IDs and private provenance contained in source summaries are not rendered by the UI; inspect the release package separately before any public publication.

When using the packaged per-cohort wrappers, integer point counts are recovered only when the reviewed patient-mean count multiplied by the fixed patient denominator is exactly integer-consistent. The number of patients modified is not recoverable from such a mean and is shown as unavailable, rather than guessed. Native class support missing from a cohort's reviewed statistics remains unavailable; the app does not open labels to fill it.

## Local isolated setup (WSL)

Use a **new** environment inside the release; do not modify a research/training environment:

```bash
cd YOUR_UNPACKED_RELEASE
python3 -m venv .venv-app
.venv-app/bin/python -m pip install -r requirements-app.txt
.venv-app/bin/python -m unittest discover -s apps/tests -v
```

Start on an unused loopback port:

```bash
TMPDIR=/dev/shm .venv-app/bin/python -m streamlit run apps/streamlit_app.py \
  --server.address 127.0.0.1 --server.port 8851 \
  --server.headless true --server.maxUploadSize 8 \
  --server.fileWatcherType none --browser.gatherUsageStats false
```

The local address is **http://127.0.0.1:8851/** once this process has actually started. Health endpoint: `http://127.0.0.1:8851/_stcore/health`. The supplied local verification records HTTP200/`ok` and a loopback-only listener on2026-10-28; current availability still depends on that local process remaining alive. This address works on the hosting computer, not as a public link for other users. There is no public deployment URL in this release. Do not claim a `streamlit.app` URL exists until an authorized deployment succeeds.

If Windows cannot reach the WSL loopback address, verify WSL localhost forwarding; do not change the service to a public/all-interface bind to bypass this check. Use port 8501 only if 8851 is occupied and explicitly record the changed local address. Stop only the specifically recorded demo process when finished; do not stop training jobs or other Streamlit apps.

## Optional, opt-in local NPZ viewer

File selection is disabled unless the operator starts a trusted **local** server with `STROKEPOINT_ENABLE_LOCAL_UPLOAD=1`. A second, unchecked-by-default user consent control must be selected before the uploader appears:

```bash
TMPDIR=/dev/shm STROKEPOINT_ENABLE_LOCAL_UPLOAD=1 .venv-app/bin/python -m streamlit run \
  apps/streamlit_app.py --server.address 127.0.0.1 --server.port 8851 \
  --server.headless true --server.maxUploadSize 8 --server.fileWatcherType none \
  --browser.gatherUsageStats false
```

Accepted NPZ schema is `xyz` **or** `points` (N×3 numeric array) plus optional `labels` (N integers, 0–255). Limits: 8 MiB compressed input, 16 MiB declared uncompressed content, 100,000 input points, 25,000 displayed points. ZIP members and NPY headers are checked before loading; object/pickle arrays, extra members, ambiguous schemas, oversized shapes, path traversal and nonfinite coordinates are rejected. NumPy uses `allow_pickle=False`. The app never extracts the archive, saves the uploaded patient file, sends it to a third-party endpoint, or runs a model. Tests are bounded robustness checks, not a security certification.

**Privacy:** Streamlit file selection transfers bytes to the app server; this is not browser-only processing. Streamlit's multipart parser may spool a large upload to a temporary file before keeping its uploaded-file record in memory. The supplied launcher verifies `/dev/shm` is `tmpfs` and uses `TMPDIR=/dev/shm`, so these framework temporary buffers are RAM-backed rather than a retained patient dataset. The uploader refuses to activate without that setting. Bytes may remain in framework/session memory or temporary RAM buffers until cleared, and OS-level paging/caches are outside this app's control; secure erasure is not promised. Do not select identifiable or unauthorized patient files. Leave upload disabled for public hosting; a cloud server is not the user's local computer.

## Optional hosted deployment

A public release requires a separate decision about publication rights, attribution, privacy and release contents. Dataset or commercial model redistribution is not authorized merely by running this viewer. Public hosting should contain only the reviewed aggregate, authorized PNG previews and code—not environments, raw images, masks, private case provenance, credentials or research checkpoints.

In Streamlit Community Cloud, connect an authorized GitHub account and select `shumao469/StrokeVasc`, branch `main`, and entrypoint `apps/streamlit_app.py`. The adjacent `apps/requirements.txt` references the pinned CPU dependencies. Select a supported Python version in Advanced settings and verify dependencies in that environment. Use the packaged aggregate-only configuration for public hosting.

Official guidance: [Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [file uploader](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader), [Plotly chart display](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart).

## Study scope shown in the app

The task uses a reference-derived binary vessel foreground and 2,048 sampled points, not an end-to-end diagnostic pipeline. DEV and FINAL remain distinct. Rare-class sampling misses and undefined confidence intervals remain visible. Zero incremental error events among 20 patients still imply a 13.9% one-sided 95% risk upper bound, not passage of the original 10% gate. Strong-3D versus simple fusion is the matched-input comparison; frozen single-MRA Y/Z transfer differs in source training and inputs. Original gates and STOP are not weakened or renamed.
