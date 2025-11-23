# Influur Viral Agent Demo

Mini end-to-end prototype of the **data + planning layer** behind an influencer marketing “viral agent”.

This repo shows how to go from:

- raw creator and post-performance data
- dbt models that compute a **virality score** and serving mart
- an **embeddings-based lookalike store**
- a small **FastAPI service** that can:
  - plan a campaign under a budget
  - return lookalike influencers by content style

It’s intentionally small, but uses real tools you’d use in production: Postgres, dbt, FastAPI, SentenceTransformers.

## Table of Contents

- [System & Tech Stack Overview](#system--tech-stack-overview)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Virality Score Rationale](#virality-score-rationale)
- [Embeddings and Lookalikes](#embeddings-and-lookalikes)
- [Planner and API Design](#planner-and-api-design)
- [Tech Stack and Trade-offs](#tech-stack-and-trade-offs)
- [Running the Project](#running-the-project)
- [Next Steps / Extensions](#next-steps--extensions)

---

## System & Tech Stack Overview

![System & Tech Stack](system_overview_tech_stack.png)

### High-Level Flow

1. **Data generation & ingest**
   - Python scripts generate synthetic but realistic influencer + post data as CSVs.
   - A loader script ingests those CSVs into Postgres tables:
     - `raw_influencers`
     - `raw_posts`

2. **Modeling with dbt**
   - dbt builds a pipeline of models:
     - `stg_influencers`, `stg_posts` (staging)
     - `fact_post_performance`, `fct_influencer_features` (core)
     - `mart_influencer_recommendations` in schema `public_marts` (serving mart)
   - The mart exposes one row per influencer with:
     - recent views, engagement, posting activity
     - targeting metadata (country, category, platform, etc.)
     - a simple `virality_score` that balances reach, engagement, and recency.

3. **Embeddings & lookalikes**
   - An offline pipeline reads influencer metadata + sample captions from Postgres.
   - It builds text embeddings with SentenceTransformers and saves them to:
     - `data/processed/influencer_embeddings.pkl`
   - At runtime, an in-memory `EmbeddingsStore` can return:
     - nearest neighbors for a given influencer (`get_lookalike_by_influencer`).

4. **Agent-style API**
   - A FastAPI service sits on top of the mart + embeddings:
     - `POST /plan_campaign`
       - Input: brief + optional filters + budget + desired influencer count.
       - Output: a budget-constrained plan with influencer list, estimated cost, expected views, and virality score.
     - `POST /lookalike_influencers`
       - Input: `influencer_id`, `top_k`.
       - Output: similar influencers with similarity scores.
   - This simulates how a viral agent would:
     - read from a well-defined mart,
     - apply campaign constraints,
     - and return a plan that downstream automation can execute.

---

## Project Structure

```text
influur-viral-agent-demo/
  README.md
  .gitignore
  .env.example
  docker-compose.yml        
  requirements.txt

  data/
    raw/
      influencers.csv       # generated
      posts.csv             # generated
    processed/
      influencer_embeddings.pkl   # generated

  dbt/
    dbt_project.yml
    profiles.yml
    models/
      schema.yml
      staging/
        stg_influencers.sql
        stg_posts.sql
      core/
        fact_post_performance.sql
        fct_influencer_features.sql
      marts/
        mart_influencer_recommendations.sql

  pipelines/
    ingest_raw_to_db.py
    run_dbt.py
    build_embeddings.py
    generate_sample_data.py

  service/
    __init__.py
    database.py
    models.py
    schemas.py
    planner.py
    embeddings_store.py
    main.py

  tests/
    test_planner.py
    test_embeddings.py
```

---

## Data Model

### Raw Layer (Postgres)

- **`raw_influencers`**
  - Synthetic influencer metadata:
    - `influencer_id`, `handle`, `platform`
    - `follower_count`, `avg_views`, `engagement_rate`
    - `country`, `language`, `category`, `content_style`
    - `cost_per_post`, `age_bracket`

- **`raw_posts`**
  - Synthetic post performance:
    - `post_id`, `influencer_id`, `platform`
    - `posted_at`, `caption`
    - `views`, `likes`, `comments`, `shares`
    - `audio_type`, `campaign_tag`

These schemas mimic the kind of signals a viral agent would learn from.

### dbt Models

- **`stg_influencers`**, **`stg_posts`**
  - Thin staging views that cast types and centralize source definitions.

- **`fact_post_performance`**
  - One row per post with:
    - `views`, `likes`, `comments`, `shares`
    - derived `engagement_rate` per post
    - `post_date` (day grain)

- **`fct_influencer_features`**
  - Aggregates performance over the last 90 days:
    - `recent_avg_views`
    - `recent_engagement_rate`
    - `post_count_last_90d`
  - Joins back to influencer metadata.

- **`mart_influencer_recommendations`**
  - Serving mart for the planner:
    - all influencer metadata needed for targeting
    - features from `fct_influencer_features`
    - computed `virality_score`:
  - dbt places this in schema `public_marts`, and the FastAPI layer maps it via SQLAlchemy.

---

## Virality Score Rationale

The `virality_score` is a **simple, hand-tuned heuristic** designed to be:

- stable and numerically well-behaved
- aligned with common influencer marketing intuition.

It combines:

1. **Recent average views (`recent_avg_views`)**
   - Captures *reach*.
   - Uses `log` to compress the range so mega-creators don’t dominate.

2. **Recent engagement rate (`recent_engagement_rate`)**
   - Captures *quality* and how much people actually interact.
   - Scaled as `recent_engagement_rate * 100` to work in “percentage points”.

3. **Post count in the last 90 days (`post_count_last_90d`)**
   - Captures *recency and consistency*.
   - Uses `log(post_count_last_90d + 1)` to reward activity without biasing purely on volume.

Weights:

```sql
0.4 * log(recent_avg_views)
+ 0.4 * engagement_pct
+ 0.2 * log(post_count_last_90d + 1)
```

- 40%: size (recent views)
- 40%: engagement (percentage)
- 20%: recency/consistency

In a real system, you would validate and eventually replace this heuristic with a learned model that better predicts downstream KPIs (e.g., cost-per-view, conversions, track “break” probability). dbt remains the place where such a model’s outputs are exposed as a mart for the agent to consume.

---

## Embeddings and Lookalikes

Script: `pipelines/build_embeddings.py`

- Connects to Postgres.
- For each influencer:
  - concatenates `content_style` and sample `caption`s from `raw_posts`.
  - encodes this text using `SentenceTransformer("all-MiniLM-L6-v2")`.
  - stores normalized vectors in `data/processed/influencer_embeddings.pkl`:

    ```python
    {
      "ids": [...],        # influencer IDs
      "vectors": np.array  # shape (N, embedding_dim)
    }
    ```

Runtime:
- `service/embeddings_store.py` loads this file into an `EmbeddingsStore`.
- The core method:

  ```python
  get_lookalike_by_influencer(influencer_id, top_k)
  ```
returns nearest neighbors in embedding space as `(influencer_id, similarity)` pairs.

This provides a basic foundation for “find creators that feel like this one” and can be extended with extra constraints (regions, pricing, brand safety) as needed.

---

## Planner and API Design

### Planner

File: `service/planner.py`  
Function: `plan_campaign(db, brief)`

Given a `CampaignBrief`, the planner:

1. Filters `public_marts.mart_influencer_recommendations` on:
   - `country`, `language`, `platform`, `category` (when provided).
2. Sorts influencers by `virality_score` descending.
3. Applies a greedy selection under budget:
   - Iterates down the sorted list.
   - Adds an influencer if `total_cost + cost_per_post <= budget`.
   - Stops when the desired number of influencers is reached or no candidates remain.
4. Estimates `expected_views` using `recent_avg_views` (fallback to `follower_count`).
5. Returns a `CampaignPlanResponse` with:
   - `influencers`: plan items with ids, handles, platforms, costs, expected views, virality scores.
   - `total_cost`, `total_expected_views`.

This is the **“mini viral agent” planner**: given a brief and constraints, it outputs a concrete, executable plan.

### FastAPI Endpoints

File: `service/main.py`

- `POST /plan_campaign`
  - Request: `CampaignBrief` JSON
  - Response: `CampaignPlanResponse` JSON
  - Example request body:

    ```json
    {
      "objective": "Break a new education creator on YouTube in the US",
      "target_country": "US",
      "target_language": "en",
      "category": "education",
      "platform": "youtube",
      "budget": 10000,
      "desired_influencer_count": 10
    }
    ```

- `POST /lookalike_influencers`
  - Request:

    ```json
    {
      "influencer_id": 183,
      "top_k": 10
    }
    ```

  - Response: list of `{ "influencer_id": ..., "handle": "...", "similarity": ... }`.

Together these endpoints show how a viral agent could:
- move from a structured brief + budget → concrete influencer set
- expand that set with content-similar creators using embeddings.

---

## Tech Stack and Trade-offs

**Warehouse – Postgres**

- Single source of truth for all tables (raw, staging, marts).
- Simple to run locally in Podman/Docker.
- Schema and SQL patterns mirror modern warehouses (Snowflake/BigQuery/Redshift).

**Modeling – dbt (dbt-core, dbt-postgres)**

- Defines lineage from `raw_influencers` / `raw_posts` → `mart_influencer_recommendations`.
- Makes the mart a clear contract between the data layer and the service/agent.
- Trade-off: some setup overhead, but representative of real-world analytics stacks.

**Pipelines & Access – Python + SQLAlchemy**

- Used for ingestion, dbt runner helper, embeddings, and API database access.
- One connection layer shared by batch and serving code.
- Easy to adapt to other backends.

**API – FastAPI, Pydantic, Uvicorn**

- Lightweight HTTP layer exposing the planner and lookalike functionality.
- Automatic OpenAPI docs at `/docs`.
- Easy integration point for an LLM-based “agent” that calls these endpoints as tools.

**Embeddings – SentenceTransformers, NumPy**

- `all-MiniLM-L6-v2` for fast, small-footprint text embeddings.
- In-memory vector store based on NumPy for simplicity.
- In production you would likely use:
  - a larger or domain-specific model,
  - and a dedicated vector DB (e.g., pgvector, Pinecone, Weaviate).

**Containers – Podman/Docker for Postgres**

- DB runs in a container for reproducibility.
- No host-level DB installation required.
- Mirrors typical dev/prod patterns in data/ML teams.

---

## Running the Project

Below is one way to run everything locally. Adjust Podman vs Docker commands as needed.

### 1. Start Postgres (Podman example)

```bash
podman machine start   # if not already running

podman run -d \
  --name influur_pg \
  -e POSTGRES_DB=influur_demo \
  -e POSTGRES_USER=influur \
  -e POSTGRES_PASSWORD=influur \
  -p 5432:5432 \
  postgres:15
```

Verify:

```bash
podman ps
# should show the influur_pg container running
```

If you prefer Docker Desktop, the equivalent is:

```bash
docker run -d \
  --name influur_pg \
  -e POSTGRES_DB=influur_demo \
  -e POSTGRES_USER=influur \
  -e POSTGRES_PASSWORD=influur \
  -p 5432:5432 \
  postgres:15
```

---

### 2. Python environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

(If you prefer using a shared env, just make sure it has the packages in `requirements.txt` and a compatible `dbt-postgres`.)

---

### 3. Environment variables

Copy the example env file:

```bash
cp .env.example .env
```

By default:

```env
DATABASE_URL=postgresql://influur:influur@localhost:5432/influur_demo
```

matches the container config above.

---

### 4. Generate data and load into Postgres

```bash
# 1) Generate synthetic influencers/posts CSVs
python pipelines/generate_sample_data.py

# 2) Load CSVs into raw_influencers and raw_posts
python pipelines/ingest_raw_to_db.py
```

---

### 5. Run dbt models

```bash
python pipelines/run_dbt.py
```

This sets `DBT_PROFILES_DIR` to `dbt/` and runs `dbt run` there.  
On success, you should have `public_marts.mart_influencer_recommendations` populated in Postgres.

---

### 6. Build embeddings

```bash
python pipelines/build_embeddings.py
```

This creates:

- `data/processed/influencer_embeddings.pkl`

and ensures the embeddings store is ready for the API.

---

### 7. Start the API

```bash
uvicorn service.main:app --reload --port 8000
```

Open:

- Swagger UI: <http://localhost:8000/docs>

---

### 8. Sample requests

#### Plan a campaign

In Swagger, open `POST /plan_campaign` → **Try it out** and use:

```json
{
  "objective": "Break a new education creator on YouTube in the US",
  "target_country": "US",
  "target_language": "en",
  "category": "education",
  "platform": "youtube",
  "budget": 10000,
  "desired_influencer_count": 10
}
```

You should see a structured response with:

- `influencers`: list of plan items
- `total_cost`
- `total_expected_views`

#### Lookalike influencers

Take an `influencer_id` from the `plan_campaign` response (e.g., `183`) and call:

`POST /lookalike_influencers`:

```json
{
  "influencer_id": 183,
  "top_k": 10
}
```

You should see:

- a list of similar influencers
- each with `influencer_id`, `handle`, and `similarity`.

---

## Next Steps / Extensions

Some natural extensions to evolve this closer to a production “viral agent”:

- Incorporate real campaign outcome signals and feedback loops into the mart.
- Replace the heuristic virality score with a learned model (e.g., expected uplift / cost-per-view).
- Add richer constraints to the planner:
  - regional quotas
  - max spend per creator
  - brand-safety tags
- Wrap the planner and lookalike endpoints with an LLM “agent” that:
  - accepts natural language briefs,
  - calls these APIs as tools,
  - iterates on the plan, and
  - returns a final proposal + rationale.

This project follows patterns that scale:  
**dbt defines the data contract, the mart is the product, and the service/agent uses that product to plan campaigns.**
