# Hydraulic diagnosis reproducibility record

This is a newly executed benchmark, not a recovery of the historical manuscript partitions. All current models use the same deterministic outer profile splits. Results are exploratory and do not establish superiority over optimized published SOTA architectures.

## Reproduce

Use Python 3 with the pinned requirements. Run from this directory:

```sh
python -m pip install -r requirements.txt
python download_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python audit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python deep_audit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python event_audit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python cross_audit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python latency_audit.py
```

Run latency last, with no other analysis jobs running. Scripts write fresh outputs in `audit/`. Committed execution records are in `results/`. `partitions.json` identifies exact profile IDs; the scripts reconstruct zero-based cycle rows; profiles are lexicographically ordered four-label tuples from `profile.txt`.

## Scope

- 10 repeated outer profile holdouts: 100 training, 22 calibration and 22 test profiles.
- Four-head 300-tree RF; sensor-block permutation repeated five times for each sensor in each partition.
- Compact native-rate CNN and one-block temporal patch mixer: fixed 20 epochs, no hyperparameter optimization or pretraining. These are adaptations, not exact published-model replications.
- Temperature fitting and threshold calibration use disjoint 11-profile sets.
- Cross-conformal variant uses five inner folds and 122 development profiles; pooled score counts are evaluated empirically, without an asserted exact coverage guarantee.
- Pressure-window RF uses training-only PS2 transitions. This does not label actuator strokes.
- CPU timings exclude acquisition, disk I/O and model loading; no embedded power claim is made.

The UCI data remain under CC BY 4.0: https://doi.org/10.24432/C5CW21 . Download checksum is enforced. Source schematic: https://doi.org/10.5194/jsss-7-359-2018 (CC BY 4.0). FS2 is in the cooling circuit; PS1 and PS2 straddle V10.

ChatGPT assisted in software development and analysis. Author review and independent replication remain appropriate before publication. No journal acceptance or ranking is guaranteed.
