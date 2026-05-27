# AI-Powered Restaurant Recommendation System

**Context:** Build a restaurant recommendation service inspired by Zomato. The system should combine structured restaurant data with a Large Language Model (LLM) to produce personalized, human-readable suggestions from natural user preferences.

---

## Goal

Deliver an application that:

1. Accepts user preferences (location, budget, cuisine, ratings, and optional constraints).
2. Uses a real-world restaurant dataset as the source of truth.
3. Invokes an LLM to rank, explain, and present recommendations in natural language.
4. Surfaces results in a clear, actionable format for the end user.

---

## Dataset

Use the Zomato restaurant dataset on Hugging Face:

**[ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)**

During ingestion, load and preprocess the data. Retain fields needed for filtering and display, such as:

- Restaurant name  
- Location  
- Cuisine  
- Cost / price range  
- Rating  
- Any other attributes useful for matching and explanation  

---

## User Inputs

Collect preferences at runtime, including:

| Input | Examples |
|-------|----------|
| **Location** | Delhi, Bangalore |
| **Budget** | Low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | e.g. 4.0+ |
| **Other** | Family-friendly, quick service, etc. |

---

## System Flow

### 1. Data ingestion

- Fetch and clean the dataset from Hugging Face.  
- Normalize fields for filtering and for inclusion in LLM prompts.

### 2. User input

- Capture the preference fields above (CLI, form, or API—your choice).  
- Validate or default missing values where appropriate.

### 3. Integration layer

- Filter the dataset to a candidate set that matches hard constraints (location, budget band, minimum rating, cuisine).  
- Serialize the candidate restaurants into a structured prompt payload.  
- Design prompts so the LLM can compare options, apply soft preferences, and rank results.

### 4. Recommendation engine

The LLM should:

- **Rank** restaurants from best to worst fit for the stated preferences.  
- **Explain** why each pick matches (or trade-offs when data is thin).  
- **Summarize** optionally—a short overview of the top choices or themes.

Structured filtering should narrow the search space; the LLM should handle nuance, tie-breaking, and natural-language explanations.

### 5. Output

Present the top recommendations in a user-friendly layout. Each item should include at minimum:

- Restaurant name  
- Cuisine  
- Rating  
- Estimated cost  
- AI-generated explanation for why it was recommended  

---

## Success Criteria

A complete solution demonstrates:

- End-to-end flow from dataset load → user preferences → filtered candidates → LLM recommendation → displayed results.  
- Sensible filtering so the LLM works on a relevant subset, not the full raw dump.  
- Prompt design that yields consistent, grounded recommendations tied to the provided restaurant data.  
- Readable output that a user could act on without reading raw JSON or logs.
