# v0.20 — Final Model-Change Approval Pack

**Decision: HOLD**

This pack closes v0.16–v0.20 without adding new model families. The four existing references/challengers are fitted once and reused across the audits below.

## v0.16 Coverage decomposition

2024 component incurred reconciliation gap: `0.000000`.

| coverage         |   covered_policy_rows_proxy |   covered_exposure_proxy |   claims |         incurred |   claim_frequency_per_covered_exposure_proxy |   incurred_per_covered_exposure_proxy |   share_of_total_claim_count |   share_of_total_incurred |
|:-----------------|----------------------------:|-------------------------:|---------:|-----------------:|---------------------------------------------:|--------------------------------------:|-----------------------------:|--------------------------:|
| liability        |                      168069 |                 126005   |    18811 |      2.4407e+07  |                                  0.149288    |                             193.699   |                  0.478944    |                0.640496   |
| property         |                       53254 |                  41338.6 |    12166 |      9.84631e+06 |                                  0.294301    |                             238.187   |                  0.309757    |                0.25839    |
| glass            |                      165056 |                 123867   |     5740 |      2.28376e+06 |                                  0.0463401   |                              18.4373  |                  0.146145    |                0.0599313  |
| theft            |                      148530 |                 111987   |      845 | 709897           |                                  0.00754552  |                               6.33911 |                  0.0215144   |                0.0186294  |
| legal_protection |                      168072 |                 126006   |     1650 | 578783           |                                  0.0130946   |                               4.59329 |                  0.0420104   |                0.0151886  |
| occupants        |                      168073 |                 126006   |       18 | 148980           |                                  0.00014285  |                               1.18233 |                  0.000458295 |                0.00390959 |
| fire             |                      148528 |                 111985   |       46 | 131647           |                                  0.000410769 |                               1.17558 |                  0.0011712   |                0.00345474 |

## v0.17 Severity-tail audit

Top 1% of positive-loss policy rows account for **20.52%** of total incurred.

| model           | subset                             |   rows |   tweedie_deviance |   calibration_ratio |   mean_absolute_policy_loss_error |
|:----------------|:-----------------------------------|-------:|-------------------:|--------------------:|----------------------------------:|
| Tweedie_GLM     | all                                | 168085 |            93.9318 |            0.953069 |                           373.401 |
| Tweedie_GLM     | exclude_top_0_5pct_positive_losses | 167978 |            84.1551 |            1.12544  |                           338.917 |
| Tweedie_GLM     | exclude_top_1pct_positive_losses   | 167872 |            81.2377 |            1.19693  |                           327.692 |
| XGBoost_Tweedie | all                                | 168085 |            93.9513 |            0.933593 |                           368.409 |
| XGBoost_Tweedie | exclude_top_0_5pct_positive_losses | 167978 |            83.9874 |            1.10251  |                           333.904 |
| XGBoost_Tweedie | exclude_top_1pct_positive_losses   | 167872 |            81.098  |            1.17243  |                           322.692 |

## v0.18 Transport uncertainty

| version   | segment          | model           |   rows |    point |   ci95_low |   ci95_high |
|:----------|:-----------------|:----------------|-------:|---------:|-----------:|------------:|
| v0.18     | returning_policy | Tweedie_GLM     | 105307 | 0.993642 |   0.953818 |    1.03678  |
| v0.18     | returning_policy | XGBoost_Tweedie | 105307 | 0.950147 |   0.909693 |    0.99568  |
| v0.18     | new_policy       | Tweedie_GLM     |  62778 | 0.824594 |   0.703276 |    0.948449 |
| v0.18     | new_policy       | XGBoost_Tweedie |  62778 | 0.881174 |   0.747542 |    1.00544  |
| v0.18     | business_type_NB | Tweedie_GLM     |  96391 | 0.86105  |   0.788731 |    0.938451 |
| v0.18     | business_type_NB | XGBoost_Tweedie |  96391 | 0.916543 |   0.84     |    0.996618 |
| v0.18     | business_type_P  | Tweedie_GLM     |  71694 | 1.03655  |   0.983137 |    1.08622  |
| v0.18     | business_type_P  | XGBoost_Tweedie |  71694 | 0.949061 |   0.905332 |    0.991326 |

## v0.19 Value for complexity

| model           | target    |   fit_seconds |   predict_seconds_2024 |   prediction_ms_per_1000_policies |   serialized_model_mb |   transformed_feature_count |   locked_scale_from_2023 |   2024_deviance |   2024_calibration_ratio |
|:----------------|:----------|--------------:|-----------------------:|----------------------------------:|----------------------:|----------------------------:|-------------------------:|----------------:|-------------------------:|
| Poisson_GLM     | frequency |       0.52194 |               0.221854 |                           1.31989 |            0.00714302 |                          88 |                 1.0124   |         1.11854 |                 0.963088 |
| XGBoost_Poisson | frequency |       1.34029 |               0.813175 |                           4.83788 |            0.723606   |                          88 |                 1.02776  |         1.11884 |                 0.960085 |
| Tweedie_GLM     | loss      |       4.67803 |               0.225386 |                           1.34091 |            0.0071888  |                          88 |                 0.914125 |        93.9318  |                 0.953069 |
| XGBoost_Tweedie | loss      |       1.56509 |               0.87037  |                           5.17815 |            0.798616   |                          88 |                 1.20756  |        93.9513  |                 0.933593 |

## v0.20 Approval gates

- `locked_2024_frequency_bootstrap_supports_xgb`: **False**
- `locked_2024_pure_premium_bootstrap_supports_xgb`: **False**
- `rolling_origin_frequency_support_consistent_across_windows`: **False**
- `rolling_origin_pure_premium_support_consistent_across_windows`: **False**
- `same_model_is_closer_to_one_for_returning_and_new_business`: **False**
- `xgb_has_lower_locked_2024_pure_premium_deviance`: **False**
- `xgb_pure_premium_is_more_complex_on_size_or_fit_time`: **True**

Final decision: **HOLD**
