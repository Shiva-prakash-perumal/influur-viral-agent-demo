# Mini Viral Agent Planner

This project is a small, end to end prototype of how I would approach the data side of a "viral agent" for influencer marketing.

The goal is to go from a campaign brief to a concrete influencer plan using a clean data stack:
- Postgres as the warehouse
- dbt for modeling and a virality recommendation mart
- FastAPI for the agent API
- SentenceTransformers and a lightweight embedding store for lookalike search

See the repository structure and comments in each file for details.
