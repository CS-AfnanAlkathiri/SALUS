# SALUS

### AI-Powered Astronaut Health Monitoring & Self-Assessment

**NASA Space Apps Challenge 2026** · *Create Health Monitoring Software for Astronauts on Space Missions*

[**Explore the Live MVP**](https://salus-97vp.onrender.com) · [**View the Project Deck**](https://acrobat.adobe.com/id/urn:aaid:sc:ap:6596418e-ad35-4bd7-aa00-d0953b95a133)

## Overview

**SALUS** is an interactive astronaut-health monitoring and self-assessment prototype designed to explore how crew members could better understand changes in their health during long-duration space missions.

The application brings together an **interactive anatomical dashboard**, **guided symptom-based assessments**, **historical health measurements**, **personalized machine-learning anomaly detection**, and **NASA-referenced health information**. Rather than displaying isolated measurements, SALUS aims to give astronauts context: what changed, how it compares with their own previous readings, and what information or next steps may be relevant.

SALUS was developed as an MVP for the **2026 NASA Space Apps Challenge**. It is a software demonstration, not a clinically validated medical system.

## The Challenge

As space missions extend farther from Earth, astronauts may not have immediate access to ground-based medical support. They need ways to record symptoms, understand health measurements, identify unusual changes, and access relevant guidance.

NASA's challenge asks for a **visual tool** that helps astronauts assess their own health and understand what to do when a measurement or symptom warrants attention. SALUS addresses that brief through a body-centered interface and a guided assessment workflow supported by historical data and research references.

## Key Features

### Interactive Health Dashboard

- **Anatomical body explorer:** a selectable human figure organizes health concerns by body region or system.
- **Health overview:** displays recent measurements, such as resting heart rate, sleep duration, and body temperature.
- **Mission-day context:** presents readings as part of an astronaut's ongoing mission history.
- **Health history:** makes changes over time easier to review.
- **Assessment entry points:** lets astronauts choose a concern and begin a guided check-in.
- **NASA knowledge access:** links health questions and measurements to relevant research information.

### Guided Self-Assessments

SALUS organizes check-ins around concerns such as fatigue, general discomfort, temperature changes, and routine health monitoring. The workflow combines reported symptoms with available measurements to present an understandable assessment summary and next-step information.

The guided assessment component is distinct from the ML model: **structured questions and safety-oriented guidance should not depend on whether an anomaly model flags a reading**. The prototype's emergency pathway is not a substitute for approved onboard medical procedures or trained crew responders.

## Machine Learning: Personalized Anomaly Detection

SALUS explores **unsupervised anomaly detection using Isolation Forest** to identify health measurements that differ from an astronaut's historical patterns.

### Why a personal baseline?

A single population-wide threshold cannot describe every individual's usual physiological patterns. SALUS instead uses historical records to establish a **personal reference baseline** and compare later observations with that astronaut's own data.

### Conceptual ML workflow

1. **Collect historical records:** daily observations are associated with an astronaut identifier and mission day.
2. **Establish a baseline:** an initial observation period provides a reference for that astronaut's usual readings.
3. **Prepare features:** physiological measurements are cleaned and transformed for model input.
4. **Detect deviations:** Isolation Forest assigns anomaly information to observations with unusual combinations of features.
5. **Present context:** the dashboard can show changes relative to the personal baseline alongside guided assessment results.

**Why Isolation Forest?** It can detect unusual observations without requiring a labeled clinical diagnosis for every training record. Its output is an **anomaly signal, not a diagnosis, disease probability, or medically validated risk score**.

### Example: Mission Day 45

In a synthetic demonstration scenario, an astronaut reports fatigue. SALUS can display sleep and resting-heart-rate measurements alongside the astronaut's historical baseline, identify unusual deviations where applicable, and connect the check-in with relevant health information.

The example illustrates a software workflow; it does not establish clinical predictive accuracy.

## Data: Three Connected Synthetic Datasets

SALUS's prototype data model separates identity and baseline context, longitudinal measurements, and assessment events.

| Dataset | Purpose |
| --- | --- |
| `astronaut_profiles.csv` | Astronaut identifiers, mission context, and baseline configuration. |
| `daily_health_records.csv` | Mission-day physiological observations used for historical comparisons and ML experiments. |
| `guided_assessments.csv` | Symptom reports and guided assessment examples associated with astronaut records. |

These datasets are **synthetic demonstration data**, not real astronaut medical records. They are conceptually linked by astronaut identifiers, while daily observations and assessment events remain separate because they represent different kinds of records.

The datasets support reproducible demo scenarios and exploration of personalized monitoring; they do **not** validate medical recommendations or establish real-world model performance.

## NASA Research & Information Retrieval

SALUS uses NASA Human Research Program material to provide **spaceflight-specific scientific context** for health indicators and concerns.

The knowledge component uses **TF-IDF-based information retrieval** to match assessment topics or user questions with relevant reference passages. This is a lightweight retrieval approach; it should not be described as embedding-based semantic search unless that implementation is separately verified.

The intended separation of responsibilities is important:

- **Guided assessment logic** organizes symptoms and measurements.
- **Machine learning** highlights unusual patterns relative to historical data.
- **Information retrieval** surfaces relevant research context and source references.

Retrieved research passages help explain *why an indicator may matter*; they are not automatically approved emergency treatment protocols. SALUS does not claim to be an official NASA medical application or to have been medically certified by NASA.

### Research References

- [NASA Human Research Program — Risks](https://www.nasa.gov/hrp/risks/)
- [NASA Human Research Program — Hazards](https://www.nasa.gov/hrp/hazards/)
- [NASA — In-Flight Medical Care](https://www.nasa.gov/ochmo/health-and-medical-systems/in-flight-medical-care/)

## System Design

SALUS connects several distinct software functions in one experience:

```text
Astronaut / Interactive Dashboard
              |
              v
     Guided Self-Assessment
       /              \
      v                v
Health Records     Symptom Inputs
      |                |
      v                v
Personal Baseline   Assessment Logic
      |
      v
Isolation Forest (Anomaly Detection)
      |
      +------------+----------------+
                   |                |
                   v                v
           Health Insights    NASA Research Retrieval
                   |                |
                   +--------+-------+
                            v
               Assessment Summary
             + References / Next Steps
```

The prototype combines **Python-based data and ML workflows**, a **web-based interactive interface**, and **research retrieval**. The frontend experience was designed and prototyped with **Figma** and developed with AI-assisted software tools. Exact framework and deployment dependencies should be confirmed against the repository's source files before listing them as verified implementation details.

## What Makes SALUS Different?

**Body-centered interaction.** Rather than starting with a spreadsheet of numbers, SALUS gives astronauts a visual entry point into body systems and health concerns.

**Personalized context.** Measurements are considered against an individual's historical pattern, not only generic reference values.

**Complementary methods.** Structured assessments, ML anomaly detection, and NASA research retrieval serve different purposes instead of being treated as one opaque AI diagnosis.

**Designed for communication constraints.** SALUS explores how a clear onboard self-assessment experience could be useful when immediate consultation with Earth is limited. Offline reliability and operational medical use would require additional engineering and validation.

## Demo & Presentation

- **Live MVP:** https://salus-97vp.onrender.com
- **Project presentation:** https://drive.google.com/file/d/1a8hWyLuCFAyVejmZrvlBm_-M3iRSKrFU/view?usp=drivesdk

## Limitations & Responsible Use

SALUS is a **hackathon MVP and research-oriented prototype**. Its datasets and example scenarios are synthetic. Anomaly flags are not medical diagnoses. The system is not a certified medical device and must not replace a crew medical officer, approved mission procedures, or flight-surgeon judgment.

Real-world use would require representative data, clinical and aerospace medical review, validation of thresholds and assessment logic, robust handling of missing measurements, security and privacy safeguards, and mission-specific operational testing.

## Project Context

Developed for the **NASA Space Apps Challenge 2026**, addressing the challenge **“Create Health Monitoring Software for Astronauts on Space Missions.”**

**SALUS — helping astronauts explore their health, recognize changes, and understand the next step.**
