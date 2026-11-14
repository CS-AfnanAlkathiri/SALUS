# API contract

The [generated OpenAPI document](openapi.json) specifies request and response shapes for the versioned `/api/v1` API. The frontend derives TypeScript schemas from it.

| Group | Routes |
| --- | --- |
| System | GET health |
| Crew | GET astronauts, astronauts/{id}, astronauts/{id}/history, astronauts/{id}/trends |
| Anatomy | GET body-regions, body-regions/{id} |
| Assessments | POST assessments, GET assessments/{id}, GET assessments/{id}/question, POST assessments/{id}/answers, POST assessments/{id}/complete, GET assessments/{id}/results |
| Measurements | POST measurements, GET measurements/guides, GET measurements/guides/{indicator} |
| Model | GET ml/status/{id}, POST ml/analyze |
| Evidence | POST evidence/search, GET evidence/sources |
| Guidance | GET guidance/{id}, emergency-support |

Missing IDs return 404. An out-of-sequence answer or early completion returns 409. Unsupported measurements, concerns, and malformed payloads return 422. The `through_day` query caps history at the selected mission day.
