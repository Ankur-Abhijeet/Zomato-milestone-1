# AI-Powered Restaurant Recommendation System

Phases **1–4** are implemented (data, preferences, integration, **Groq** recommendations).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional overrides
```

First run downloads ~575MB from Hugging Face and writes `.cache/restaurants.parquet`. Later runs read the cache.

## CLI

```bash
# Load (or refresh) dataset into cache
python main.py load

# Capture preferences (interactive)
python main.py preferences -i

# Preferences from JSON + preview hard-filter match count
python main.py preferences --json '{"location":"Bangalore","budget":"medium","cuisines":["Italian"],"min_rating":4.0,"additional":"family-friendly"}' --preview-filter

# Filter using preference flags (uses validated UserPreferences)
python main.py query --location Bangalore --cuisines Italian --min-rating 4.0 --budget medium

# Phase 3: filter → cap → build LLM prompt
python main.py integrate --location Bangalore --cuisines Italian --min-rating 4.0 --show-prompt

# Phase 4: full recommendations via Groq
cp .env.example .env   # set GROQ_API_KEY=gsk_...
python main.py recommend --location Bangalore --cuisines Italian --min-rating 4.0

# Rule-based fallback (no API call)
python main.py recommend --location Bangalore --cuisines Italian --fallback-only

# Summary stats
python main.py stats
```

## Phase 2: User preferences

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| `location` | Yes | — | City or area; whitespace rejected |
| `budget` | No | `medium` | `low`, `medium`, or `high` |
| `cuisines` | No | any | List; empty = no cuisine filter |
| `min_rating` | No | `3.0` | 0–5 inclusive |
| `additional` | No | — | Soft prefs for LLM; max 500 chars (truncated) |

```python
from input.validator import validate_preferences
from input.serializer import PreferenceSerializer

prefs = validate_preferences({
    "location": "Bangalore",
    "cuisines": ["Italian", "Chinese"],
    "min_rating": 4.0,
    "additional": "family-friendly",
})
payload = PreferenceSerializer.to_dict(prefs)  # stable JSON for Phase 3
```

## Phase 3: Integration layer

Pipeline order: **location → rating → budget → cuisine → cap (30 by default) → prompt**.

```python
from data.repository import RestaurantRepository
from input.validator import validate_preferences
from services.integration import IntegrationService

repo = RestaurantRepository()
repo.load()
prefs = validate_preferences({"location": "Bangalore", "cuisines": ["Italian"], "min_rating": 4.0})

result = IntegrationService(repo).run(prefs)
if result.skip_llm:
    print(result.user_message)  # empty filter + relaxation hints
else:
    payload = result.prompt_payload  # system_message, user_message, candidates
```

- Empty filter → `skip_llm=True` with hints (no prompt built)
- Candidates sorted by rating, votes, name; capped at `CANDIDATE_CAP` (max 50)
- Prompt uses JSON-escaped candidates with unique `id` per row (disambiguates duplicate names)
- Set `LOG_PROMPTS=true` or `integrate -v` to log full prompt in dev

## Phase 4: Recommendation engine (Groq)

Uses the [Groq API](https://console.groq.com) with JSON-mode chat completions (`llama-3.3-70b-versatile` by default).

```python
from data.repository import RestaurantRepository
from input.validator import validate_preferences
from services.integration import IntegrationService
from services.recommendation_engine import RecommendationEngine

repo = RestaurantRepository()
repo.load()
prefs = validate_preferences({"location": "Bangalore", "cuisines": ["Italian"], "min_rating": 4.0})

integration = IntegrationService(repo).run(prefs)
result = RecommendationEngine().recommend(integration, prefs)

for item in result.recommendations:
    print(item.rank, item.name, item.explanation)
```

| Behavior | Detail |
|----------|--------|
| **Provider** | Groq (`GROQ_API_KEY`, `GROQ_MODEL`) |
| **Output** | JSON: `summary` + ranked `recommendations` with `id`, `name`, `explanation` |
| **Validation** | Drops entries not in candidate list (anti-hallucination) |
| **Fallback** | On timeout/rate-limit/parse failure → rating-sorted templates (`used_fallback=True`) |
| **Quota errors** | Fail clearly — no fake AI text |

## Restaurant fields (normalized)

| Field | Source / notes |
|-------|----------------|
| `name` | Restaurant name |
| `city` | Parsed from address (aliases: Bengaluru → Bangalore) |
| `area` | Zomato `location` column |
| `cuisines` | Split list from `cuisines` |
| `cost_inr` / `cost_display` | `approx_cost(for two people)` |
| `budget_band` | `low` ≤ ₹500, `medium` ≤ ₹1500, `high` above (configurable) |
| `rating` | Parsed from `rate` (`4.1/5`); `NEW`/missing → excluded from rating filter |
| `votes`, `rest_type`, `dish_liked`, `url`, … | Preserved for later phases |

## Repository API

```python
from data.repository import RestaurantRepository

repo = RestaurantRepository()
repo.load()
all_restaurants = repo.all()
matches = repo.find_by_filters(
    location="Bangalore",
    budget="medium",
    cuisines=["Italian"],
    min_rating=4.0,
)
```

## Project layout

```
config/          # settings, budget thresholds
models/          # Restaurant, UserPreferences
input/           # validators, serializers, CLI/JSON adapters
services/        # filter, candidate cap, prompt builder, integration
data/            # loader, preprocessor, cache, repository, matching
main.py          # CLI entry point
```

Phase 5 (polished UX / API) can extend `presentation/formatter.py`.

## Configuration

See `.env.example`. Key variables:

- `RESTAURANT_CACHE_PATH` — Parquet cache location
- `BUDGET_LOW_MAX` / `BUDGET_MEDIUM_MAX` — INR thresholds for two people
- `HF_DATASET_ID` — Hugging Face dataset id
