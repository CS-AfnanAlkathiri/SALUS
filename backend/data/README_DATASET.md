# SALUS synthetic dataset — version 1.0

**Purpose:** Functional demonstration of an astronaut-specific longitudinal health history, guided self-assessment, and personalized anomaly detection. All data are **fictional and simulated**. This is not NASA astronaut data, a clinical dataset, or evidence of medical model performance.

## Files
- `astronaut_profiles.csv`: 8 fictional profiles. Ages and roles are fabricated metadata, not model inputs.
- `daily_health_records.csv`: 480 daily observations, 8 astronauts x 60 mission days. Includes heart rate, sleep, blood pressure, temperature, symptom scores, missing measurements, and scenario labels.
- `guided_assessments.csv`: symptom-driven and routine assessment sessions linked by `astronaut_id` and `mission_day`. Includes a **separate** simulated emergency case to test rule-based escalation; do not use it for ML training.

## Suggested ML design
1. Split each astronaut's timeline chronologically: days 1–30 for a preliminary personal baseline; days 31–60 for demonstration/testing. Never randomly split days within the same astronaut for this use case.
2. Train a personal or pooled-with-personal-normalization anomaly detector on **physiological measurements actually available**. Start with `resting_hr_bpm` and `sleep_hours`, which have near-complete coverage. Add blood pressure or temperature only after defining handling for missing values, measurement consistency, and sufficient training observations.
3. `scenario_injected`, `scenario_type`, `symptoms_reported`, `data_origin`, and `example_followup_category` are **NOT training features**. Scenario labels are only simulation annotations for checking demo behavior; do not treat them as medically validated truth.
4. Fit preprocessing/imputation using training days only; keep a missingness indicator when useful. Do not fabricate measurements at inference time. If insufficient history, show `baseline_not_ready`.
5. Report raw anomaly scores as **statistical deviations**, not illness probabilities or clinical risk levels. This dataset cannot validate medical effectiveness.
6. Keep deterministic urgent-warning-sign rules independent from ML and RAG. The emergency demonstration in `guided_assessments.csv` is explicitly excluded from ML training.
7. If retraining later, avoid automatically absorbing flagged or unreviewed observations into the baseline.

## Synthetic scenarios
- AST-02, AST-04, AST-06, AST-08, days 41–50: lower sleep and elevated resting HR, higher fatigue.
- AST-03 and AST-07, days 47–52: elevated resting HR and blood pressure; palpitations noted on selected days.
- AST-01 and AST-05, days 36–39: headache episodes and mild sleep disruption.
- `ASM-EMERGENCY-DEMO`: artificial sudden severe chest pain/collapse input; tests escalation workflow only.

## Schema / units
`astronaut_id`: fictional ID; `mission_day`: integer 1–60.
`resting_hr_bpm`: beats/min; `sleep_hours`: hours/night; `systolic_bp_mmhg`, `diastolic_bp_mmhg`: mmHg; `body_temp_c`: Celsius.
`fatigue_score_0_10`, `headache_score_0_10`: fictional self-report severity scales, 0–10 (not validated clinical scales).
`symptoms_reported`: semicolon-separated symptom tokens or `none`.
`measurement_context`: fixed simulated resting context; not evidence of real device collection.
`scenario_type`: simulated scenario category; `scenario_injected`: binary simulation label; `data_origin`: always `synthetic_demo`.
`assessment_id`: unique session identifier; `body_region`: `head_brain`, `chest_heart`, or `general_health`.
`chief_concern`: reason for assessment; `symptom_onset`: simple demo value; `urgent_warning_sign_reported`: yes/no input, **not clinically validated**.
`example_followup_category`: illustrative UX routing label, **not a treatment recommendation or medical ground truth**.

## Integration
Join guided assessments to daily records by `astronaut_id` and `mission_day`. Use the assessment record as the event that invokes measurement storage and ML analysis. The anatomy UI selects `body_region`; the guided engine selects questions; the RAG retrieves cited evidence from separately sourced NASA documents. **Do not train the ML model on NASA research text.**

## Limits
No medical diagnosis, treatment safety, mission fitness, or threshold can be inferred from this fabricated dataset. The simulated anomalies are deliberately obvious and any resulting model metrics are only a software demonstration. For a real deployment, obtain appropriate real-world/flight data, clinical expertise, validation, and approved mission protocols.
