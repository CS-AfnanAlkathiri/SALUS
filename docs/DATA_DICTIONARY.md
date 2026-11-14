# Data dictionary

| File | Records | Key | Purpose |
| --- | ---: | --- | --- |
| astronaut_profiles.csv | 8 | astronaut_id | Fictional role, age, baseline days, and provenance |
| daily_health_records.csv | 480 | astronaut_id + mission_day | Daily numerical values, symptoms, context, and synthetic scenario annotations |
| guided_assessments.csv | 45 | assessment_id | Saved illustrative events including the separate emergency scenario |

Heart rate uses bpm, sleep uses hours, pressures use mmHg, temperature uses Celsius, and fatigue and headache are fictional 0–10 ratings. The detailed definitions and simulation design are in the [original dataset README](../backend/data/README_DATASET.md).

Seeded measurements and user-entered observations remain separate. For each indicator and day, the history chart selects the most recent available observation. Imported assessment values are preserved in assessment findings and do not create duplicate daily measurements. Blank values stay absent. Scenario labels are used for evaluation only, and imported assessment rows never enter training.
