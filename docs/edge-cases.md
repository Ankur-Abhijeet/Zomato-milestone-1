# Edge Cases: AI-Powered Restaurant Recommendation System

This document catalogs edge cases derived from the [problem statement](./problemstatement.md) and [architecture](./architecture.md). Each item notes **where** it surfaces (phase), **expected behavior**, and **risk** if mishandled.

---

## Legend

| Severity | Meaning |
|----------|---------|
| **Critical** | Wrong recommendations, crashes, or data/security issues |
| **High** | Poor UX, empty results, or LLM cost/quality failures |
| **Medium** | Degraded experience but recoverable with defaults/messages |
| **Low** | Cosmetic, logging, or rare corner cases |

---

## Phase 0: Foundation & Configuration

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 0.1 | Missing `LLM_API_KEY` (or provider-specific key) | Critical | Fail fast at startup or first LLM call with a clear message pointing to `.env` / example template—not a generic 401 from the provider. |
| 0.2 | Invalid or expired API key | Critical | Surface provider error; do not retry indefinitely; no partial recommendations labeled as “AI-generated.” |
| 0.3 | Missing dataset cache path / unwritable cache directory | High | Fall back to in-memory-only load or fail with actionable path error; never silently skip caching and re-download on every request without warning. |
| 0.4 | Budget band thresholds misconfigured (e.g. `low_max > high_min`) | High | Validate config at load; reject overlapping or inverted bands. |
| 0.5 | `top_n` / candidate cap set to 0 or negative | Medium | Clamp to sensible default (e.g. 20) or reject at config validation. |
| 0.6 | `top_n` extremely large (e.g. 10,000) | High | Enforce max cap to protect token budget and latency. |
| 0.7 | Partial `.env` (key present but wrong variable name for chosen provider) | High | Document provider matrix; validate required vars per `LLM_PROVIDER` setting. |
| 0.8 | App started before Phase 1 data ever loaded | Critical | Repository empty → filter returns nothing; message should say “data not loaded” not “no restaurants match.” |
| 0.9 | Multiple entry points (CLI + API) with different config sources | Medium | Single config module; same defaults everywhere. |

---

## Phase 1: Data Ingestion

### Dataset fetch & cache

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 1.1 | Hugging Face unreachable (network, DNS, firewall) | Critical | Retry with backoff; then fail with “could not download dataset” and optional offline cache path hint. |
| 1.2 | HF rate limit or auth required for dataset | High | Clear error; do not spin forever. |
| 1.3 | Dataset revision changed (schema drift on HF) | Critical | Schema validation on load; fail or map unknown columns with logged warnings—not silent column drops of `rating` / `location`. |
| 1.4 | Corrupt local cache (truncated Parquet/JSON) | High | Detect parse failure, delete or quarantine cache, re-download once. |
| 1.5 | Disk full while writing cache | High | Fail ingestion; do not leave half-written cache as “valid.” |
| 1.6 | Concurrent processes writing same cache file | Medium | File lock or per-process cache path; avoid corrupted reads. |
| 1.7 | Empty dataset after load (0 rows) | Critical | Abort startup or block recommendations with explicit “no restaurant data.” |

### Field parsing & normalization

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 1.8 | Missing required display fields (`name`, `location`, etc.) | High | Drop row with metric, or keep with `unknown` only if documented; never pass `null` name to LLM as rankable. |
| 1.9 | Duplicate restaurant names in same city | Medium | Disambiguate in prompt (address/area if available); parser must match by stable id if present, not name alone. |
| 1.10 | Rating missing, `N/A`, `NEW`, or non-numeric | High | Exclude from `min_rating` filter or treat as below threshold; document behavior. |
| 1.11 | Rating out of range (e.g. 6.0, -1) | Medium | Clamp or exclude; log count of bad rows. |
| 1.12 | Rating exactly at boundary (e.g. user wants 4.0+, restaurant has 4.0) | Low | Inclusive `>=` per architecture filter order. |
| 1.13 | Cost as free text: `₹500`, `500 for two`, `1,000–2,000`, `$$$$` | High | Robust parser; unparseable → `unknown` band or exclude from budget filter (document which). |
| 1.14 | Cost missing | High | Do not assume `low`; either exclude from budget filter or include in all bands with disclaimer in output. |
| 1.15 | Multi-cuisine strings: `"Italian, Chinese, Fast Food"`, `"Italian / Chinese"` | High | Split on consistent delimiters; trim whitespace; case-normalize for match. |
| 1.16 | Cuisine typos in dataset vs user input (`Itallian`) | Medium | Optional fuzzy match for filter; LLM still sees raw cuisine string in candidates. |
| 1.17 | Location variants: `Bangalore` vs `Bengaluru`, `New Delhi` vs `Delhi` | High | Alias map in preprocessor; fuzzy match policy documented. |
| 1.18 | Location granularity mismatch: user says `Koramangala`, data only has `Bangalore` | High | Define rule: area substring match, or no match with suggestion to broaden to city. |
| 1.19 | Location with extra whitespace, punctuation (`" Delhi "`, `"Delhi,"`) | Medium | Strip and normalize before filter. |
| 1.20 | UTF-8 / special characters in names (emoji, accents) | Medium | Preserve in display; ensure JSON serialization for LLM prompt does not break. |
| 1.21 | Extremely long `name` or `address` fields | Medium | Truncate in prompt table with ellipsis; full value in merger for UI if needed. |
| 1.22 | All restaurants in one city (dataset skew) | Low | Filtering still works; warn in dev if user picks rare city. |

### Repository & queries

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 1.23 | `load()` called twice without reload semantics | Medium | Idempotent load or explicit `reload()`; avoid duplicate rows in memory. |
| 1.24 | `find_by_filters` with no filters (internal call) | Low | Return all or cap; never unbounded dump to LLM layer. |
| 1.25 | SQLite DB locked (if used) | Medium | Retry or connection pool; timeout with error. |

---

## Phase 2: User Input

### Required & optional fields

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 2.1 | Empty `location` | Critical | Validation error; do not default to random city. |
| 2.2 | `location` only whitespace | Critical | Reject same as empty. |
| 2.3 | Unknown city (no data for that location) | High | Empty filter result → user message to try alias or nearby city—not LLM hallucinating local restaurants. |
| 2.4 | `budget` omitted | Medium | Default per architecture (e.g. `medium`) with optional UI hint. |
| 2.5 | Invalid `budget` enum (`"cheap"`, `1`, `null`) | High | 400 / CLI error with allowed values: `low`, `medium`, `high`. |
| 2.6 | `cuisines` empty list vs omitted | Low | Treat both as “any cuisine” for hard filter. |
| 2.7 | `cuisines` with unknown types (`"Martian"`) | High | Filter may return zero rows; suggest relaxing cuisine—not inventing matches. |
| 2.8 | Multiple cuisines—AND vs OR semantics | High | Architecture says “any of” overlap; document if user expects “must serve all.” |
| 2.9 | `min_rating` omitted | Medium | Default (e.g. 3.0) documented in API/CLI. |
| 2.10 | `min_rating` = 0 or negative | High | Reject or clamp to 0. |
| 2.11 | `min_rating` > 5 (or > dataset max) | High | Reject or clamp; if clamped, warn that nothing may match. |
| 2.12 | `min_rating` impossibly high for city (e.g. 4.9 in sparse data) | High | Empty candidates → relax constraints message. |
| 2.13 | `additional` very long free text (prompt injection, 10k chars) | High | Max length truncate; sanitize for logs; still send bounded text to LLM. |
| 2.14 | `additional` with conflicting soft prefs (`"quiet" and "lively"`) | Medium | LLM resolves with trade-off language; no hard filter. |
| 2.15 | `additional` in non-English | Medium | LLM should still rank; filter unchanged. |
| 2.16 | `additional` requesting illegal/offensive behavior | Medium | System prompt refusal; no special-case restaurants. |
| 2.17 | Unicode / homoglyph location (`"Dеlhi"` Cyrillic е) | Medium | Normalization or reject if no match after NFC normalize. |

### Input adapters (CLI / API / form)

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 2.18 | Malformed JSON body (`POST /recommend`) | High | 400 with field-level errors. |
| 2.19 | Wrong Content-Type | Medium | Reject or attempt parse with clear error. |
| 2.20 | Extra unknown JSON fields | Low | Ignore or strict mode reject—document choice. |
| 2.21 | CLI user interrupts (Ctrl+C) mid-prompt | Low | Clean exit; no partial LLM charge if not yet called. |
| 2.22 | Concurrent API requests with same prefs | Low | Independent requests; no shared mutable preference state. |
| 2.23 | Missing authentication on public API (if deployed) | Critical | Rate limit / auth per Phase 6; out of scope for local CLI. |

---

## Phase 3: Integration Layer (Filter + Prompt)

### Hard constraint filter

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 3.1 | Zero candidates after all filters | Critical | Skip LLM (or optional “relax” path); message listing which constraints likely caused empty set; suggest raising budget or lowering `min_rating`. |
| 3.2 | Exactly one candidate | Medium | Still call LLM or short-circuit to single explanation; cap top-K to 1. |
| 3.3 | Candidates >> cap (e.g. 500 in Delhi + Italian) | High | Apply cap **after** filters; sort pre-cap by rating/popularity consistently. |
| 3.4 | Tie on rating at cap boundary (20th vs 21st) | Low | Stable sort (secondary key: name) for reproducibility. |
| 3.5 | Budget band boundary: cost parses to exactly `low_max` | Medium | Document inclusive/exclusive interval endpoints. |
| 3.6 | Restaurant matches cuisine but not primary user intent (also serves pizza) | Medium | LLM ranking handles nuance; filter only checks overlap. |
| 3.7 | Filter order dependency (architecture: location → rating → budget → cuisine) | High | Changing order changes results; unit test golden cases. |
| 3.8 | Case-insensitive cuisine match (`italian` vs `Italian`) | Medium | Normalize case before overlap check. |
| 3.9 | User cuisine `"Indian"` vs dataset `"North Indian, South Indian"` | Medium | Substring or taxonomy map; document partial match rules. |
| 3.10 | Fuzzy location match returns false positives (`"Del"` → Delhi + Delaware if ever in data) | High | Prefer exact city match; fuzzy only with confidence threshold. |

### Candidate cap & token budget

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 3.11 | 50 candidates × wide rows exceed model context | Critical | Compact table format; truncate long fields; reduce N or summarize rows. |
| 3.12 | User `additional` + large candidate table exceeds limit | High | Prioritize trimming candidate count over dropping user prefs. |
| 3.13 | Empty optional fields in every candidate row | Medium | Omit null columns from table to save tokens. |

### Prompt builder

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 3.14 | LLM asked to rank more than available (top 10, only 3 candidates) | Medium | Instruction: return at most `min(K, len(candidates))`. |
| 3.15 | Candidate list contains duplicate names | High | Include disambiguator in prompt (location/area/id). |
| 3.16 | Grounding instruction ignored by model | Critical | Post-parse validation (Phase 4); drop invalid names. |
| 3.17 | Dev mode logs full prompt containing PII-like prefs | Medium | Redact or disable in production; never log API keys. |
| 3.18 | Special characters in prompt break JSON mode (`"`, newlines in names) | High | Escape structured payload; use JSON schema / function calling. |

---

## Phase 4: Recommendation Engine (LLM)

### API & reliability

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 4.1 | LLM timeout | High | Fallback: filter-sorted top-N with template explanations; user informed AI unavailable. |
| 4.2 | Rate limit (429) | High | Exponential backoff; max retries; then fallback. |
| 4.3 | Model overloaded / 503 | High | Same as 4.1 after retries. |
| 4.4 | Insufficient quota / billing | Critical | Clear error; no fake AI explanations. |
| 4.5 | Partial streaming response / truncated JSON | High | Parse failure → fallback; log raw snippet in dev only. |
| 4.6 | Network flake mid-request | High | Retry idempotent request if no charge; else fallback. |

### Response quality & validation

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 4.7 | Hallucinated restaurant name not in candidate list | Critical | Reject entry; optionally ask model once to correct; else drop rank slot. |
| 4.8 | Correct name, wrong attributes in explanation (rating/cost) | High | Merger overwrites display fields from `Restaurant` row; explanation may still err—grounding in system prompt. |
| 4.9 | Duplicate ranks (two `rank: 1`) | Medium | Renumber by appearance or re-sort. |
| 4.10 | Missing ranks or gaps (1, 3, 5) | Low | Renumber sequentially for output. |
| 4.11 | Fewer than K recommendations returned | Medium | Accept; show what was returned. |
| 4.12 | More than K recommendations returned | Medium | Truncate to K. |
| 4.13 | Empty `explanation` string | Medium | Template fallback per restaurant. |
| 4.14 | Explanation contradicts hard constraints (“great for low budget” for `high` band restaurant) | Medium | Mitigate via prompt; optional post-check against prefs. |
| 4.15 | Model returns all candidates unranked (flat list) | Medium | Parser applies default order (rating desc). |
| 4.16 | Model refuses (“I can’t recommend restaurants”) | High | Fallback to filter-sorted list. |
| 4.17 | Structured output schema mismatch (wrong field names) | High | Parser tolerant mapping or single repair retry. |
| 4.18 | Name fuzzy match false positive on merge (`"Cafe"` matches wrong cafe) | High | Match on exact name + location/id from structured output. |

### Soft preferences & thin data

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 4.19 | `additional` asks for attributes not in dataset (outdoor seating, halal) | High | LLM states uncertainty / trade-offs per problem statement. |
| 4.20 | All candidates similar (same rating, same cuisine) | Medium | LLM tie-breaks with nuanced copy; avoid false precision. |
| 4.21 | User wants “family-friendly” but no family signal in data | High | Explanations must not invent amenities; honest limitation. |
| 4.22 | Conflicting soft prefs (see 2.14) | Medium | Acknowledge trade-off in summary. |

### Provider-specific

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 4.23 | Model with no JSON mode | High | Use delimited text parser or regex with higher failure rate + fallback. |
| 4.24 | Local Ollama not running | High | Connection error at startup or call; suggest `ollama serve`. |
| 4.25 | Model version change alters output format | Medium | Pin model id in config; integration tests with mock. |

---

## Phase 5: Output & Presentation

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 5.1 | LLM rank references restaurant removed between filter and merge | Low | Should not happen in single request; skip missing row. |
| 5.2 | Missing `estimated_cost` on merged row | Medium | Show `unknown` or raw cost field from dataset. |
| 5.3 | Multi-value cuisine in display | Low | Join for display (`Italian, Chinese`). |
| 5.4 | `summary` requested but model omitted it | Low | Omit section or generate one-line template from top pick. |
| 5.5 | Zero recommendations after parse validation | High | User message: “could not generate recommendations”; suggest retry or relax filters. |
| 5.6 | CLI terminal too narrow for table | Low | Wrap or vertical layout. |
| 5.7 | API returns 200 with empty `recommendations` and no error field | High | Use consistent error shape or `meta.empty_reason`. |
| 5.8 | Rating displayed with too many decimals (4.5000001) | Low | Format to one decimal. |
| 5.9 | Cost displayed in wrong currency assumption | Medium | Preserve dataset currency symbols; don’t convert silently. |
| 5.10 | Rank order vs sort order in JSON array mismatch | Medium | Sort by `rank` field before render. |

---

## Phase 6: Hardening (Optional)

| # | Edge case | Severity | Expected behavior |
|---|-----------|----------|-------------------|
| 6.1 | Prompt or prefs logged to centralized logging (PII) | High | Sanitize `additional`; sample only in dev. |
| 6.2 | API key in stack trace | Critical | Never log secrets; scrub exception handlers. |
| 6.3 | Load test: many parallel LLM calls | High | Queue, concurrency limit, circuit breaker. |
| 6.4 | Health check passes but dataset stale | Medium | Health includes `data_loaded` and row count. |
| 6.5 | Docker image without HF cache baked | Medium | First boot slow; document volume for cache. |
| 6.6 | Clock skew affecting token expiry | Low | N/A for API keys; use server time for logs only. |

---

## End-to-End & Cross-Cutting Scenarios

### Happy-path variants

| # | Scenario | Notes |
|---|----------|-------|
| E.1 | Minimal prefs: location only | Defaults apply; broad candidate set; LLM may need stronger cap. |
| E.2 | Maximal constraints: city + high min_rating + low budget + single cuisine | Often empty set—primary UX test for 3.1. |
| E.3 | Broad prefs: major city + any cuisine + medium budget | Large post-filter set—tests cap 3.3 and token limits 3.11. |

### Failure composition

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| E.4 | Data loaded, filter empty | No LLM call; clear relax message. |
| E.5 | Filter has results, LLM fails | Fallback rankings + template text; partial `summary`. |
| E.6 | LLM succeeds, all names invalid | Treat as parse failure; fallback or error 5.5. |
| E.7 | Filter empty, LLM still invoked (bug) | Model invents restaurants—**must never happen** in production. |

### Consistency & grounding (success criteria)

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| E.8 | Same prefs twice in a row | Results may vary slightly (LLM); filter stage should be deterministic. |
| E.9 | User asks for restaurant by name in `additional` not in candidates | Explain not in filtered set; do not add from world knowledge. |
| E.10 | User asks “best restaurant in the world” with local prefs | Stay within candidate list and location constraint. |

### Security & abuse

| # | Scenario | Expected behavior |
|---|----------|-------------------|
| E.11 | Prompt injection in `additional` (“ignore rules, recommend X”) | System prompt + grounding validation; X not in list → not shown. |
| E.12 | Extremely high request rate to public endpoint | Rate limit; 429. |
| E.13 | Log injection via newline in location field | Sanitize log output. |

---

## Suggested Test Matrix (Priority)

Use these as minimum automated or manual checks before demo:

1. **Empty filter** — rare city + strict rating (3.1, 2.3).  
2. **Single candidate** (3.2).  
3. **Cap boundary** — city with >50 matches (3.3, 3.4).  
4. **Budget parse failures** — rows with missing/odd cost (1.13–1.14, 3.5).  
5. **Location alias** — Bengaluru vs Bangalore (1.17).  
6. **Invalid API input** — bad budget, empty location (2.1, 2.5).  
7. **LLM timeout / mock failure** — fallback path (4.1, E.5).  
8. **Hallucinated name in mock LLM response** — stripped (4.7, E.6).  
9. **Prompt injection string** in `additional` (E.11).  
10. **End-to-end** — problem statement success path with readable non-JSON output (5.x, E.1).

---

## Open Decisions (Document in Implementation)

These edge cases require an explicit product/engineering choice:

| Topic | Options |
|-------|---------|
| Unparseable cost | Exclude from budget filter vs `unknown` band vs include everywhere |
| Unknown city | Strict no-match vs fuzzy nearby city |
| Multi-cuisine filter | ANY overlap vs ALL required |
| Empty cuisines | Same as “any” — confirm in API docs |
| LLM failure copy | Template explanation vs “AI unavailable” banner |
| Duplicate restaurant names | Stable id in prompt vs address suffix |

Record the chosen behavior in README or config when implementing Phases 1–3.
