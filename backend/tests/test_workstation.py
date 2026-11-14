from app import ml
from app.store import Answer, Assessment, Measurement, seed, transaction
from sqlalchemy import func, select

API = "/api/v1"

def request(client, url, body=None, expected=200):
    response = client.get(API + url) if body is None else client.post(API + url, json=body)
    assert response.status_code == expected, response.text
    return response.json()

def begin(client, astronaut, day, region, concern):
    return request(client, "/assessments", dict(astronaut_id=astronaut, mission_day=day, body_region=region, concern=concern), 201)

def answer(client, assessment, value):
    key = assessment["session"]["assessment_id"]
    return request(client, f"/assessments/{key}/answers", {"question_id":assessment["question"]["id"],"value":value})

def finish(client, astronaut, day, region, concern, inputs):
    current = begin(client, astronaut, day, region, concern)
    key = current["session"]["assessment_id"]
    while current["question"]:
        question = current["question"]["id"]
        current = answer(client, current, inputs.get(question))
    assert current["session"]["status"] == "in_progress"
    output = request(client, f"/assessments/{key}/complete", {})
    assert output == request(client, f"/assessments/{key}/complete", {})
    assert output == request(client, f"/assessments/{key}/results")
    return output

def test_import_preserves_distinct_entities_and_seeding_is_repeatable(client):
    health = request(client, "/health")
    assert health["seeded"] == {"profiles":8,"daily_records":480,"assessments":45}
    with transaction() as db:
        count = db.scalar(select(func.count()).select_from(Measurement))
    assert seed() == health["seeded"]
    with transaction() as db:
        assert db.scalar(select(func.count()).select_from(Measurement)) == count
    history = request(client, "/astronauts/AST-02/history?through_day=45")
    assert len(history["records"]) == 45
    assert history["records"][-1]["readings"]["resting_hr_bpm"] == 72.8

def test_fatigue_end_to_end(client):
    output = finish(client,"AST-02",45,"general_health","Fatigue",
                    {"urgent":"No","onset":"Today","recurring":"No","resting_hr_bpm":72.8,"sleep_hours":5.47,"fatigue_score_0_10":7})
    assert output["ml"]["anomaly_flag"] is True
    assert output["evidence"][0]["source_id"] == "sleep"
    assert output["guidance"]["review_status"] == "source_checked_prototype"
    assert output["measurements"]["sleep_hours"] == 5.47
    history = request(client, "/astronauts/AST-02/history?through_day=45")
    assert history["records"][-1]["sources"]["sleep_hours"] == "user_entered"
    assert any(s["assessment_id"] == output["session"]["assessment_id"] for s in history["assessments"])

def test_cardiovascular_end_to_end(client):
    output = finish(client,"AST-03",49,"chest_heart","Palpitations",
                    {"urgent":"No","onset":"Today","recurring":"Yes","notes":"Reported during routine check",
                     "resting_hr_bpm":71.6,"sleep_hours":7.09,"systolic_bp_mmhg":123,"diastolic_bp_mmhg":75})
    assert output["ml"]["baseline_status"] == "ready"
    assert output["evidence"][0]["source_id"] == "cardio"
    assert output["answers"]["notes"]
    assert output["measurements"]["diastolic_bp_mmhg"] == 75

def test_emergency_stops_before_measurements_even_without_optional_services(client, monkeypatch):
    imported = request(client,"/assessments/ASM-EMERGENCY-DEMO/results")
    assert imported["urgent"]
    monkeypatch.setitem(client.app.state._state, "models", {})
    monkeypatch.setitem(client.app.state._state, "index", None)
    a = begin(client,"AST-01",60,"chest_heart","Chest discomfort")
    assert a["question"]["id"] == "urgent"
    result = answer(client,a,"Yes")
    assert result["session"]["status"] == "escalated" and result["question"] is None
    saved = request(client, f"/assessments/{a['session']['assessment_id']}/results")
    assert saved["guidance"] == request(client,"/emergency-support")
    assert saved["ml"] is None and saved["evidence"] == []

def test_invalid_inputs_and_resume(client):
    current = begin(client,"AST-01",1,"general_health","Daily health check")
    key = current["session"]["assessment_id"]
    request(client, f"/assessments/{key}/answers",{"question_id":"resting_hr_bpm","value":70},409)
    answer(client,current,"No")
    current = request(client, f"/assessments/{key}/question")
    assert current["question"]["id"] == "resting_hr_bpm"
    request(client, f"/assessments/{key}/answers",{"question_id":"resting_hr_bpm","value":-1},422)
    assert answer(client,current,63)["question"]["id"] == "sleep_hours"
    assert answer(client,current,63)["question"]["id"] == "sleep_hours"
    with transaction() as db:
        assert db.get(Assessment,key).status == "in_progress"
        assert db.get(Answer,(key,"resting_hr_bpm")).value == 63

def test_cold_start_and_missing_feature_policy(client):
    output = finish(client,"AST-01",1,"general_health","Daily health check",{"urgent":"No","resting_hr_bpm":62.3})
    assert output["ml"]["baseline_status"] == "baseline_not_ready"
    for values, expected in [({},[]), ({"sleep_hours":5.47},["sleep_hours"]),({"body_temp_c":37},[])]:
        result = request(client,"/ml/analyze",{"astronaut_id":"AST-02","mission_day":45,"measurements":values})
        assert result["features_used"] == expected

def test_model_round_trip_and_chronological_counts(client):
    models, metadata = ml.load()
    assert metadata["training_rows"] == metadata["evaluation_rows"] == 240
    assert metadata["train_day_range"] == [1,30]
    assert metadata["evaluation_day_range"] == [31,60]
    assert metadata["aggregate"]["count"] <= 240
    inputs = {"resting_hr_bpm":72.8,"sleep_hours":5.47}
    assert ml.analyze(models,"AST-02",45,inputs) == ml.analyze(client.app.state.models,"AST-02",45,inputs)
    assert set(metadata["per_astronaut"]) == {f"AST-{n:02d}" for n in range(1,9)}

def test_local_evidence_provenance_and_no_match(client, monkeypatch):
    import socket
    def unavailable(*args, **kwargs):
        raise AssertionError("Evidence retrieval should not access the network")
    monkeypatch.setattr(socket,"create_connection",unavailable)
    found = request(client,"/evidence/search",{"query":"circadian fatigue"})
    assert found[0]["source_id"] == "sleep"
    assert found[0]["url"].startswith("https://www.nasa.gov/")
    assert found[0]["retrieved_on"]
    assert request(client,"/evidence/search",{"query":"zxqnonexistent"}) == []
