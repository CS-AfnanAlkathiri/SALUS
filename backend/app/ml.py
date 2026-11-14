import hashlib
import json
import os
import tempfile
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

from .store import CatalogEntry, DATA, STATE, daily_rows, seed, transaction

FEATURE_SETS = [
    ("resting_hr_bpm", "sleep_hours"),
    ("resting_hr_bpm",),
    ("sleep_hours",),
]
VERSION = "iforest-1"
ARTIFACT = STATE / "model.joblib"
LIMITATION = "Statistical comparison with synthetic mission history. Clinical significance requires crew medical review."

def vector(row, features):
    return [float(row[key]) for key in features]

def complete(row, features):
    return all(row.get(key) not in (None, "") for key in features)

def report(actual, predicted):
    precision, recall, f1, _ = precision_recall_fscore_support(actual, predicted, average="binary", zero_division=0)
    return dict(precision=precision, recall=recall, f1=f1,
                confusion_matrix=confusion_matrix(actual, predicted, labels=[0, 1]).tolist(), count=len(actual))

def fingerprint():
    digest = hashlib.sha256()
    for name in ("astronaut_profiles.csv", "daily_health_records.csv"):
        digest.update((DATA / name).read_bytes())
    return f"{VERSION}:{sklearn.__version__}:{digest.hexdigest()}"

def train():
    rows = daily_rows()
    training = [r for r in rows if int(r["mission_day"]) <= 30]
    evaluation = [r for r in rows if int(r["mission_day"]) > 30]
    astronauts = sorted({r["astronaut_id"] for r in training})
    models = {}
    metadata = {"model_version": VERSION, "training_rows": len(training), "evaluation_rows": len(evaluation),
                "coverage": {key: sum(complete(r, (key,)) for r in training) for key in
                             ("resting_hr_bpm", "sleep_hours", "systolic_bp_mmhg", "diastolic_bp_mmhg", "body_temp_c")}}
    for features in FEATURE_SETS:
        baselines = {}
        matrices = []
        for astronaut in astronauts:
            usable = [r for r in training if r["astronaut_id"] == astronaut and complete(r, features)]
            if len(usable) < 20:
                continue
            matrix = np.array([vector(r, features) for r in usable])
            center, scale = matrix.mean(axis=0), matrix.std(axis=0)
            scale = np.where(scale > 1e-6, scale, 1.0)
            baselines[astronaut] = (center, scale, len(usable))
            matrices.append((matrix - center) / scale)
        if matrices:
            model = IsolationForest(n_estimators=160, contamination=0.06, random_state=42)
            model.fit(np.concatenate(matrices))
            models[features] = (model, baselines)
    metrics = {}
    for astronaut in astronauts:
        actual, predicted = [], []
        for row in evaluation:
            if row["astronaut_id"] != astronaut:
                continue
            finding = analyze(models, astronaut, int(row["mission_day"]), row)
            if finding["anomaly_flag"] is not None:
                actual.append(int(row["scenario_injected"]))
                predicted.append(int(finding["anomaly_flag"]))
        metrics[astronaut] = (actual, predicted)
    metadata["aggregate"] = report([x for a, _ in metrics.values() for x in a], [x for _, p in metrics.values() for x in p])
    metadata["per_astronaut"] = {key: report(*pairs) for key, pairs in metrics.items()}
    metadata["evaluation_rows_unscored"] = len(evaluation) - metadata["aggregate"]["count"]
    metadata["evaluation_with_single_feature"] = sum(not complete(r, FEATURE_SETS[0]) and any(complete(r, f) for f in FEATURE_SETS[1:]) for r in evaluation)
    metadata["train_day_range"] = [1, 30]
    metadata["evaluation_day_range"] = [31, 60]
    metadata["limitations"] = [LIMITATION]
    with tempfile.NamedTemporaryFile(dir=STATE, delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        joblib.dump({"fingerprint": fingerprint(), "models": models, "metadata": metadata}, temporary)
        os.replace(temporary, ARTIFACT)
    finally:
        temporary.unlink(missing_ok=True)
    return models, metadata

def load():
    if ARTIFACT.exists():
        try:
            bundle = joblib.load(ARTIFACT)
            if bundle["fingerprint"] == fingerprint():
                return bundle["models"], bundle["metadata"]
        except (ValueError, KeyError, EOFError, OSError):
            pass
    return train()

def analyze(models, astronaut, day, readings):
    result = dict(astronaut_id=astronaut, mission_day=day, baseline_status="baseline_not_ready",
                  model_version=VERSION, features_used=[], current_values={}, baseline_values={},
                  baseline_deviations={}, anomaly_flag=None, anomaly_score=None,
                  top_deviating_indicators=[], limitations=[LIMITATION])
    if day <= 30:
        return result
    if not any(astronaut in baseline for _, baseline in models.values()):
        return result
    result["baseline_status"] = "compatible_readings_needed"
    for features in FEATURE_SETS:
        if features not in models or not complete(readings, features):
            continue
        model, baselines = models[features]
        if astronaut not in baselines:
            continue
        center, scale, _ = baselines[astronaut]
        values = np.array(vector(readings, features))
        z = (values - center) / scale
        score = float(-model.decision_function(z.reshape(1, -1))[0])
        result.update(baseline_status="ready", features_used=list(features), current_values=dict(zip(features, values.tolist())),
                      baseline_values=dict(zip(features, center.tolist())), baseline_deviations=dict(zip(features, (values-center).tolist())),
                      anomaly_flag=score > 0, anomaly_score=round(score, 5),
                      top_deviating_indicators=sorted(features, key=lambda key: abs(z[features.index(key)]), reverse=True))
        return result
    return result

if __name__ == "__main__":
    seed()
    _, metadata = train()
    with transaction(write=True) as db:
        db.merge(CatalogEntry(kind="model", entry_id=VERSION, payload=metadata))
    print(json.dumps(metadata, indent=2))
