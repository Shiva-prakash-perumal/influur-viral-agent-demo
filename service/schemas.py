from pydantic import BaseModel
from typing import List, Optional

class CampaignBrief(BaseModel):
    objective: str
    target_country: Optional[str] = None
    target_language: Optional[str] = None
    category: Optional[str] = None
    platform: Optional[str] = None
    budget: float
    desired_influencer_count: int = 50

class InfluencerPlanItem(BaseModel):
    influencer_id: int
    handle: str
    platform: str
    estimated_cost: float
    expected_views: float
    virality_score: float

class CampaignPlanResponse(BaseModel):
    influencers: List[InfluencerPlanItem]
    total_cost: float
    total_expected_views: float

class LookalikeRequest(BaseModel):
    influencer_id: int
    top_k: int = 10
