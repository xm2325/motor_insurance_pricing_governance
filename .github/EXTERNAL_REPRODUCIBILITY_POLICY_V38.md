# External evidence reproducibility policy (v0.38)

For external-validation protocols registered after v0.38, a positive support claim requires at least two independent GitHub Actions executions of the same locked source/split/features/models/gate, matching decision labels and key metrics inside the preregistered numerical tolerance.

A decision disagreement is fail-closed: `NUMERICAL_REPRODUCIBILITY_REVIEW_REQUIRED_AND_NO_POSITIVE_EXTERNAL_CLAIM`.

A stable decision with point metrics outside the registered tolerance is labelled `METRIC_NUMERICAL_REPRODUCIBILITY_REVIEW`; it must not be described as exact reproducibility.

Future iterative estimators must explicitly register solver/tolerance and available convergence metadata. Numerical workflows default to one thread for OMP/OpenBLAS/MKL unless the future preregistration fixes another setting before data access.

These are project governance rules, not insurer or regulatory thresholds, and they do not retroactively alter v0.36.
