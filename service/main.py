from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import SessionLocal
from .schemas import CampaignBrief, CampaignPlanResponse, LookalikeRequest
from .planner import plan_campaign
from .embeddings_store import EmbeddingsStore
from . import models

app = FastAPI(title="Mini Viral Agent")

try:
    emb_store = EmbeddingsStore()
except FileNotFoundError:
    emb_store = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/plan_campaign", response_model=CampaignPlanResponse)
def plan_campaign_endpoint(brief: CampaignBrief, db: Session = Depends(get_db)):
    return plan_campaign(db, brief)

@app.post("/lookalike_influencers")
def lookalike_endpoint(req: LookalikeRequest, db: Session = Depends(get_db)):
    if emb_store is None:
        raise HTTPException(status_code=500, detail="Embeddings not loaded")

    exists = db.query(models.InfluencerRecommendation).filter(
        models.InfluencerRecommendation.influencer_id == req.influencer_id
    ).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Influencer not found")

    neighbors = emb_store.get_lookalike_by_influencer(req.influencer_id, req.top_k)

    # if no neighbors (e.g. no embedding), return empty gracefully
    if not neighbors:
        return []

    id_to_handle = {
        r.influencer_id: r.handle
        for r in db.query(models.InfluencerRecommendation)
        .filter(models.InfluencerRecommendation.influencer_id.in_([n[0] for n in neighbors]))
        .all()
    }
    return [
        {"influencer_id": inf_id, "handle": id_to_handle.get(inf_id, ""), "similarity": score}
        for inf_id, score in neighbors
    ]
