# Model card

**Task.** Identify statistical deviations in synthetic personal mission histories. Resting pulse and sleep are the model features. Systolic pressure, diastolic pressure, and temperature have 212, 212, and 224 available readings across the 240 training rows. They are retained for review and excluded from this model to keep the supported feature sets focused.

**Training.** A pooled Isolation Forest uses each astronaut’s first 30 days to normalize observations. Pooling gives each fit more observations than training separate forests from roughly 30 readings each. This MVP used that design rationale. An empirical comparison against per-astronaut models remains outstanding. Two additional forests support one-feature inference when only pulse or only sleep is available. At least 20 complete training rows are required per astronaut and feature set. Missing readings are never filled in. The evaluation uses Days 31–60.

**Synthetic holdout.** Across 240 observations the model produced 54 true positives, 6 false negatives, 15 false positives, and 165 true negatives against the supplied scenario labels. Precision was 0.783, recall 0.900, and F1 0.837. The [computed metrics](model-metrics.json) include per-astronaut results and missing-feature coverage.

**Interpretation.** The anomaly score is the negated Isolation Forest decision function. Positive values flag a statistical deviation. A finding lists the indicators ordered by absolute standardized deviation, alongside each personal mean and raw difference. Performance varies by astronaut and the synthetic labels provide no clinical validation.
