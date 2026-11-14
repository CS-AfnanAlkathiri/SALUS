# NASA source register

Sources were checked on November 14, 2026. SALUS retrieves curated paraphrases with official source URLs and section provenance from [nasa_sources.json](../backend/data/nasa_sources.json). It uses a persisted TF-IDF index over section text, tags, and summaries. The index runs offline and returns an empty result for unmatched queries. Update the curated JSON with verified source sections and run `python -m app.evidence` to refresh it.

| Source | Indexed sections |
| --- | --- |
| [Risks of Human Spaceflight](https://www.nasa.gov/hrp/risks/) | Sleep and irregular schedules, cardiovascular adaptations, bone changes |
| [5 Hazards of Human Spaceflight](https://www.nasa.gov/hrp/hazards/) | About the five hazards |
| [Isolation and Confinement](https://www.nasa.gov/hrp/hazard-isolation-and-confinement/) | Behavioral health |
| [In-Flight Medical Reference](https://www.nasa.gov/ochmo/health-and-medical-systems/in-flight-medical-care/) | Medical care away from home |

[Ongoing HRP Research](https://www.nasa.gov/hrp/ongoing-hrp-research/) was reviewed as a starting point. The MVP uses manual ingestion and lightweight local retrieval. Automated NASA HTML extraction and sentence-transformer embeddings remain outstanding.
