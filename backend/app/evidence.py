import hashlib
import json
import os
import tempfile
from datetime import date
from typing_extensions import TypedDict

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from .store import DATA, STATE

VERIFIED = "2026-11-14"

class Evidence(TypedDict):
    source_id: str
    title: str
    section: str
    url: str
    passage: str
    retrieved_on: str
    score: float

def build_index():
    sources = json.loads((DATA / "nasa_sources.json").read_text())
    for source in sources:
        if not source["url"].startswith("https://www.nasa.gov/") or not source["passage"].strip():
            raise ValueError("Evidence must have an official NASA URL and nonempty content")
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([f"{s['section']} {s['tags']} {s['passage']}" for s in sources])
    return sources, vectorizer, matrix

def load_index():
    artifact = STATE / "evidence.joblib"
    signature = hashlib.sha256((DATA / "nasa_sources.json").read_bytes()).hexdigest()
    if artifact.exists():
        try:
            cached_signature, index = joblib.load(artifact)
            if signature == cached_signature:
                return index
        except (ValueError, EOFError, OSError):
            pass
    index = build_index()
    with tempfile.NamedTemporaryFile(dir=STATE, delete=False) as tmp:
        temporary = tmp.name
    try:
        joblib.dump((signature, index), temporary)
        os.replace(temporary, artifact)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return index

def search(index, query, limit=3):
    if index is None:
        return []
    sources, vectorizer, matrix = index
    scores = (matrix @ vectorizer.transform([query]).T).toarray().ravel()
    return [
        {**{k: v for k, v in sources[i].items() if k != "tags"}, "retrieved_on": VERIFIED, "score": round(float(scores[i]), 4)}
        for i in scores.argsort()[::-1][:limit] if scores[i] > 0
    ]

if __name__ == "__main__":
    STATE.mkdir(parents=True, exist_ok=True)
    index = load_index()
    print(f"Indexed {len(index[0])} source sections. Source register checked {date.fromisoformat(VERIFIED)}.")
