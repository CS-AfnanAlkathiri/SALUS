from __future__ import annotations

import logging
import math
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from typing_extensions import TypedDict
from uuid import uuid4

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select

from . import evidence, ml
from .evidence import Evidence
from .paths import GUIDANCE, REGIONS, guides, question_list, region_payload
from .store import (INDICATORS, Answer, Assessment, Astronaut, CatalogEntry, Finding, Measurement,
                    new_measurement, seed, transaction)

class Crew(TypedDict):
    astronaut_id: str
    mission_role: str
    age_years: int
    baseline_phase_days: int
    data_origin: str

class Region(TypedDict):
    id: str
    title: str
    description: str
    concerns: list[str]
    evidence_topic: str

class SessionView(TypedDict):
    assessment_id: str
    astronaut_id: str
    mission_day: int
    body_region: str
    concern: str
    status: str
    origin: str

class Guidance(TypedDict):
    title: str
    steps: list[str]
    sources: list[str]
    review_status: str
    procedure_available: bool

class Guide(TypedDict):
    indicator: str
    title: str
    unit: str
    why: str
    equipment: str
    instructions: str
    common_mistakes: str
    source: str
    limitations: str

class Question(BaseModel):
    id: str
    prompt: str
    type: Literal["choice", "number", "text"]
    options: list[str] = []
    description: str = ""
    optional: bool = False
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    guide_id: str | None = None

class Progress(BaseModel):
    session: SessionView
    question: Question | None
    answered: int
    total: int

class Start(BaseModel):
    astronaut_id: str
    mission_day: int = Field(ge=1, le=3000)
    body_region: str
    concern: str

class Submission(BaseModel):
    question_id: str
    value: str | float | None

class Readings(BaseModel):
    astronaut_id: str
    mission_day: int = Field(ge=1, le=3000)
    measurements: dict[str, float]

class Entry(BaseModel):
    astronaut_id: str
    mission_day: int = Field(ge=1, le=3000)
    indicator: str
    value: float
    context: str = Field(default="self_reported", max_length=150)

class Search(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=3, ge=1, le=10)

class ModelResult(TypedDict):
    astronaut_id: str
    mission_day: int
    baseline_status: str
    model_version: str
    features_used: list[str]
    current_values: dict[str, float]
    baseline_values: dict[str, float]
    baseline_deviations: dict[str, float]
    anomaly_flag: bool | None
    anomaly_score: float | None
    top_deviating_indicators: list[str]
    limitations: list[str]

class Result(BaseModel):
    session: SessionView
    urgent: bool = False
    imported: bool = False
    answers: dict[str, str | float | None] = {}
    measurements: dict[str, float] = {}
    symptom_onset: str | None = None
    ml: ModelResult | None = None
    evidence: list[Evidence] = []
    guidance: Guidance | None = None
    limitations: list[str] = []

class Point(TypedDict):
    mission_day: int
    readings: dict[str, float]
    sources: dict[str, str]

class History(TypedDict):
    records: list[Point]
    assessments: list[SessionView]

def now():
    return datetime.now(timezone.utc).isoformat()

def attrs(row, names):
    return {name: getattr(row, name) for name in names}

def require(db, kind, identifier):
    row = db.get(kind, identifier)
    if row is None:
        raise HTTPException(404, "Record not found")
    return row

def validated_reading(key, value):
    if key not in INDICATORS:
        raise HTTPException(422, "Unknown measurement")
    title, _, low, high = INDICATORS[key]
    if not math.isfinite(value) or not low <= value <= high:
        raise HTTPException(422, f"{title} must be between {low} and {high} for this input format.")
    return value

def answer_map(db, identifier):
    rows = db.scalars(select(Answer).where(Answer.assessment_id == identifier))
    return {row.question_id: row.value for row in rows}

def progress(db, session):
    answers = answer_map(db, session.assessment_id)
    questions = question_list(session.body_region, session.concern, answers)
    active = session.status == "in_progress"
    pending = next((q for q in questions if q["id"] not in answers), None) if active else None
    return Progress(session=attrs(session, SessionView.__annotations__), question=pending,
                    answered=len(answers), total=len(questions))

@asynccontextmanager
async def startup(app):
    app.state.counts = seed()
    app.state.models, app.state.metadata, app.state.index = {}, {}, None
    try:
        app.state.models, app.state.metadata = ml.load()
    except Exception:
        logging.exception("Anomaly model unavailable")
    try:
        app.state.index = evidence.load_index()
    except Exception:
        logging.exception("Evidence unavailable")
    with transaction(write=True) as db:
        if app.state.metadata:
            db.merge(CatalogEntry(kind="model", entry_id=ml.VERSION, payload=app.state.metadata))
        for key, rule in GUIDANCE.items():
            db.merge(CatalogEntry(kind="guidance", entry_id=key, payload=rule))
        if app.state.index:
            for source in app.state.index[0]:
                db.merge(CatalogEntry(kind="evidence", entry_id=source["source_id"], payload=source))
    yield

app = FastAPI(title="SALUS", version="0.1.0", lifespan=startup)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("SALUS_CORS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
api = APIRouter(prefix="/api/v1")

@api.get("/health")
def health(request: Request):
    return {"status": "ok", "seeded": request.app.state.counts, "ml_ready": bool(request.app.state.models),
            "evidence_ready": request.app.state.index is not None}

@api.get("/astronauts")
def crew() -> list[Crew]:
    with transaction() as db:
        return [attrs(row, Crew.__annotations__) for row in db.scalars(select(Astronaut).order_by(Astronaut.astronaut_id))]

@api.get("/astronauts/{astronaut_id}")
def profile(astronaut_id: str) -> Crew:
    with transaction() as db:
        return attrs(require(db, Astronaut, astronaut_id), Crew.__annotations__)

@api.get("/body-regions")
def regions() -> list[Region]:
    return [region_payload(key) for key in REGIONS]

@api.get("/body-regions/{region_id}")
def region(region_id: str) -> Region:
    if region_id not in REGIONS:
        raise HTTPException(404, "Unknown region")
    return region_payload(region_id)

@api.post("/assessments", status_code=201)
def start(body: Start) -> Progress:
    if body.body_region not in REGIONS or body.concern not in REGIONS[body.body_region][2]:
        raise HTTPException(422, "This concern has no guided assessment")
    with transaction(write=True) as db:
        require(db, Astronaut, body.astronaut_id)
        row = Assessment(**body.model_dump(), assessment_id=str(uuid4()), status="in_progress", origin="user_entered", started_at=now())
        db.add(row)
        return progress(db, row)

@api.get("/assessments/{assessment_id}")
def assessment(assessment_id: str) -> SessionView:
    with transaction() as db:
        return attrs(require(db, Assessment, assessment_id), SessionView.__annotations__)

@api.get("/assessments/{assessment_id}/question")
def next_question(assessment_id: str) -> Progress:
    with transaction() as db:
        return progress(db, require(db, Assessment, assessment_id))

@api.post("/assessments/{assessment_id}/answers")
def submit(assessment_id: str, body: Submission) -> Progress:
    with transaction(write=True) as db:
        row = require(db, Assessment, assessment_id)
        existing = db.get(Answer, (assessment_id, body.question_id))
        if existing and existing.value == body.value:
            return progress(db, row)
        pending = progress(db, row).question
        if pending is None or pending.id != body.question_id:
            raise HTTPException(409, "Refresh to see the current question")
        value = body.value
        if pending.type == "choice" and value not in pending.options:
            raise HTTPException(422, "Choose one of the listed options")
        if pending.type == "number" and value is not None:
            if isinstance(value, str):
                raise HTTPException(422, "Enter a numeric reading")
            value = validated_reading(pending.id, value)
        if pending.type == "text" and value is not None and (not isinstance(value, str) or len(value) > 500):
            raise HTTPException(422, "Enter a note of 500 characters or fewer")
        db.add(Answer(assessment_id=assessment_id, question_id=pending.id, value=value))
        if pending.type == "number" and value is not None:
            db.add(new_measurement(f"{assessment_id}:{pending.id}", row.astronaut_id, row.mission_day,
                                   pending.id, value, row.origin, "guided_assessment_self_report", now(), assessment_id))
        if pending.id == "urgent" and value in ("Yes", "Unsure"):
            row.status = "escalated"
            row.completed_at = now()
            db.add(Finding(assessment_id=assessment_id, payload={"urgent": True, "guidance": GUIDANCE["emergency"], "answers": {"urgent": value}}))
        db.flush()
        return progress(db, row)

def read_result(db, row):
    finding = db.get(Finding, row.assessment_id)
    if finding is None:
        raise HTTPException(409, "Finish the assessment to view results")
    payload = dict(finding.payload)
    if payload.get("urgent"):
        payload.setdefault("guidance", GUIDANCE["emergency"])
    return Result(session=attrs(row, SessionView.__annotations__), **payload)

@api.post("/assessments/{assessment_id}/complete")
def complete_assessment(assessment_id: str, request: Request) -> Result:
    with transaction(write=True) as db:
        row = require(db, Assessment, assessment_id)
        if row.status != "in_progress":
            return read_result(db, row)
        if progress(db, row).question:
            raise HTTPException(409, "There are unanswered questions")
        answers = answer_map(db, assessment_id)
        readings = {key: value for key, value in answers.items() if key in INDICATORS and value is not None}
        limitations = []
        insight = None
        found = []
        try:
            insight = ml.analyze(request.app.state.models, row.astronaut_id, row.mission_day, readings)
            if not request.app.state.models:
                limitations.append("The anomaly model is unavailable.")
            elif insight["baseline_status"] != "ready":
                limitations.append("A compatible baseline and at least one supported reading are required for a model comparison.")
        except Exception:
            logging.exception("Assessment model inference failed")
            limitations.append("The anomaly model is unavailable.")
        try:
            found = evidence.search(request.app.state.index, f"{REGIONS[row.body_region][3]} {row.concern}")
        except Exception:
            logging.exception("Assessment evidence retrieval failed")
        if not found:
            limitations.append("No NASA evidence was returned.")
        guidance = GUIDANCE["routine" if row.concern == "Daily health check" and not (insight and insight["anomaly_flag"]) else "crew_review"]
        payload = dict(answers=answers, measurements=readings, symptom_onset=answers.get("onset"),
                       ml=insight, evidence=found, guidance=guidance, limitations=limitations)
        row.status, row.completed_at = "completed", now()
        db.add(Finding(assessment_id=assessment_id, payload=payload))
        return Result(session=attrs(row, SessionView.__annotations__), **payload)

@api.get("/assessments/{assessment_id}/results")
def results(assessment_id: str) -> Result:
    with transaction() as db:
        return read_result(db, require(db, Assessment, assessment_id))

@api.post("/measurements", status_code=201)
def record(body: Entry, request: Request):
    validated_reading(body.indicator, body.value)
    key = str(uuid4())
    with transaction(write=True) as db:
        require(db, Astronaut, body.astronaut_id)
        db.add(new_measurement(key, body.astronaut_id, body.mission_day, body.indicator, body.value, "user_entered", body.context, now()))
    return {"measurement_id": key, "ml": ml.analyze(request.app.state.models, body.astronaut_id, body.mission_day, {body.indicator: body.value})}

@api.get("/measurements/guides")
def list_guides() -> list[Guide]:
    return guides()

@api.get("/measurements/guides/{indicator_id}")
def guide(indicator_id: str) -> Guide:
    for item in guides():
        if item["indicator"] == indicator_id:
            return item
    raise HTTPException(404, "Measurement guide not found")

@api.get("/astronauts/{astronaut_id}/history")
def history(astronaut_id: str, through_day: int = 3000) -> History:
    with transaction() as db:
        require(db, Astronaut, astronaut_id)
        rows = db.scalars(select(Measurement).where(Measurement.astronaut_id == astronaut_id, Measurement.mission_day <= through_day)
                          .order_by(Measurement.mission_day, Measurement.timestamp, Measurement.measurement_id))
        points = {}
        for row in rows:
            point = points.setdefault(row.mission_day, {"mission_day": row.mission_day, "readings": {}, "sources": {}})
            point["readings"][row.indicator] = row.value
            point["sources"][row.indicator] = row.source
        sessions = db.scalars(select(Assessment).where(Assessment.astronaut_id == astronaut_id, Assessment.mission_day <= through_day)
                              .order_by(Assessment.mission_day.desc(), Assessment.started_at.desc(), Assessment.assessment_id))
        return {"records": list(points.values()), "assessments": [attrs(row, SessionView.__annotations__) for row in sessions]}

@api.get("/astronauts/{astronaut_id}/trends")
def trends(astronaut_id: str, through_day: int = 3000) -> list[Point]:
    return history(astronaut_id, through_day)["records"]

@api.get("/ml/status/{astronaut_id}")
def ml_status(astronaut_id: str, request: Request, mission_day: int = 45):
    profile(astronaut_id)
    models = request.app.state.models
    active = mission_day > 30 and any(astronaut_id in stats for _, stats in models.values())
    return {"baseline_status": "ready" if active else "baseline_not_ready", "model_version": ml.VERSION,
            "available": bool(models), "limitations": [ml.LIMITATION]}

@api.post("/ml/analyze")
def analyze(body: Readings, request: Request) -> ModelResult:
    profile(body.astronaut_id)
    for key, value in body.measurements.items():
        validated_reading(key, value)
    return ml.analyze(request.app.state.models, body.astronaut_id, body.mission_day, body.measurements)

@api.post("/evidence/search")
def search(body: Search, request: Request) -> list[Evidence]:
    return evidence.search(request.app.state.index, body.query, body.limit)

@api.get("/evidence/sources")
def sources(request: Request) -> list[Evidence]:
    index = request.app.state.index
    return [{**{k: v for k, v in source.items() if k != "tags"}, "retrieved_on": evidence.VERIFIED, "score": 0.0}
            for source in index[0]] if index else []

@api.get("/guidance/{guidance_id}")
def guidance(guidance_id: str) -> Guidance:
    if guidance_id not in GUIDANCE:
        raise HTTPException(404, "Guidance not found")
    return GUIDANCE[guidance_id]

@api.get("/emergency-support")
def emergency() -> Guidance:
    return GUIDANCE["emergency"]

app.include_router(api)
frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend.is_dir():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
