import csv
import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATE = Path(os.environ.get("SALUS_STATE_DIR", ROOT / "state"))
INDICATORS = {
    "resting_hr_bpm": ("Resting heart rate", "bpm", 1, 350),
    "sleep_hours": ("Sleep duration", "h", 0, 24),
    "systolic_bp_mmhg": ("Systolic blood pressure", "mmHg", 1, 400),
    "diastolic_bp_mmhg": ("Diastolic blood pressure", "mmHg", 1, 400),
    "body_temp_c": ("Body temperature", "°C", 20, 50),
    "fatigue_score_0_10": ("Fatigue", "/10", 0, 10),
    "headache_score_0_10": ("Headache", "/10", 0, 10),
    "blood_glucose_mgdl": ("Blood glucose", "mg/dL", 1, 2000),
}

class Base(DeclarativeBase):
    pass

class Astronaut(Base):
    __tablename__ = "astronauts"
    astronaut_id: Mapped[str] = mapped_column(primary_key=True)
    mission_role: Mapped[str]
    age_years: Mapped[int]
    baseline_phase_days: Mapped[int]
    data_origin: Mapped[str]

class Daily(Base):
    __tablename__ = "daily_records"
    astronaut_id: Mapped[str] = mapped_column(ForeignKey("astronauts.astronaut_id"), primary_key=True)
    mission_day: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)

class Assessment(Base):
    __tablename__ = "assessments"
    assessment_id: Mapped[str] = mapped_column(primary_key=True)
    astronaut_id: Mapped[str] = mapped_column(ForeignKey("astronauts.astronaut_id"), index=True)
    mission_day: Mapped[int]
    body_region: Mapped[str]
    concern: Mapped[str]
    status: Mapped[str]
    origin: Mapped[str]
    started_at: Mapped[str | None]
    completed_at: Mapped[str | None]

class Answer(Base):
    __tablename__ = "assessment_answers"
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.assessment_id"), primary_key=True)
    question_id: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[object] = mapped_column(JSON)

class Finding(Base):
    __tablename__ = "assessment_findings"
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.assessment_id"), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)

class Measurement(Base):
    __tablename__ = "measurements"
    measurement_id: Mapped[str] = mapped_column(primary_key=True)
    astronaut_id: Mapped[str] = mapped_column(ForeignKey("astronauts.astronaut_id"), index=True)
    mission_day: Mapped[int]
    assessment_id: Mapped[str | None] = mapped_column(ForeignKey("assessments.assessment_id"))
    indicator: Mapped[str]
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str]
    context: Mapped[str]
    source: Mapped[str]
    timestamp: Mapped[str | None]
    validation_status: Mapped[str]

class CatalogEntry(Base):
    __tablename__ = "catalog"
    kind: Mapped[str] = mapped_column(String, primary_key=True)
    entry_id: Mapped[str] = mapped_column(String, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)

engine = create_engine(f"sqlite:///{STATE / 'salus.sqlite3'}", connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def enable_integrity(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=10000")

@contextmanager
def transaction(write=False):
    with Session(engine) as db:
        if write:
            db.connection().exec_driver_sql("BEGIN IMMEDIATE")
        with db:
            yield db
            if write:
                db.commit()

def read_csv(name, columns):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not set(columns).issubset(reader.fieldnames or []):
            raise ValueError(f"{name} does not match its expected schema")
        return list(reader)

def new_measurement(identifier, astronaut, day, indicator, value, source, context, timestamp=None, assessment=None):
    return Measurement(measurement_id=identifier, astronaut_id=astronaut, mission_day=day,
                       assessment_id=assessment, indicator=indicator, value=value,
                       unit=INDICATORS[indicator][1], context=context, source=source,
                       timestamp=timestamp, validation_status="format_checked")

def seed():
    STATE.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    profiles = read_csv("astronaut_profiles.csv", Astronaut.__table__.columns.keys())
    fields = list(INDICATORS)[:-1]
    daily = read_csv("daily_health_records.csv", ["astronaut_id", "mission_day", "scenario_injected", "scenario_type", "data_origin", "measurement_context", *fields])
    assessments = read_csv("guided_assessments.csv", ["assessment_id", "astronaut_id", "mission_day", "body_region", "chief_concern", "symptom_onset", "urgent_warning_sign_reported", "data_origin", *fields])
    identities = [r["astronaut_id"] for r in profiles]
    daily_keys = [(r["astronaut_id"], int(r["mission_day"])) for r in daily]
    assessment_keys = [r["assessment_id"] for r in assessments]
    if len(set(identities)) != len(identities) or len(set(daily_keys)) != len(daily_keys) or len(set(assessment_keys)) != len(assessment_keys):
        raise ValueError("Duplicate primary key in demo CSV")
    with transaction(write=True) as db:
        for row in profiles:
            for key in ("age_years", "baseline_phase_days"):
                row[key] = int(row[key])
            db.merge(Astronaut(**row))
        db.flush()
        for row in daily:
            astronaut, day = row["astronaut_id"], int(row["mission_day"])
            db.merge(Daily(astronaut_id=astronaut, mission_day=day, payload=row))
            for field in fields:
                if row[field] != "":
                    identifier = f"seed:{astronaut}:{day}:{field}"
                    db.merge(new_measurement(identifier, astronaut, day, field, float(row[field]), row["data_origin"], row["measurement_context"]))
        for row in assessments:
            identifier = row["assessment_id"]
            db.merge(Assessment(assessment_id=identifier, astronaut_id=row["astronaut_id"], mission_day=int(row["mission_day"]),
                                body_region=row["body_region"], concern=row["chief_concern"], origin=row["data_origin"],
                                status="escalated" if row["urgent_warning_sign_reported"] == "yes" else "completed"))
            db.flush()
            db.merge(Finding(assessment_id=identifier, payload={
                "imported": True, "measurements": {field: float(row[field]) for field in fields if row[field] != ""},
                "symptom_onset": row["symptom_onset"], "urgent": row["urgent_warning_sign_reported"] == "yes",
                "limitations": ["Imported scenario. Run a new assessment to produce current model and evidence results."],
            }))
    return {"profiles": len(profiles), "daily_records": len(daily), "assessments": len(assessments)}

def daily_rows():
    with transaction() as db:
        return [r.payload for r in db.scalars(select(Daily).order_by(Daily.astronaut_id, Daily.mission_day))]
