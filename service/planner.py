from sqlalchemy.orm import Session
from . import models
from .schemas import CampaignBrief, CampaignPlanResponse, InfluencerPlanItem

def plan_campaign(db: Session, brief: CampaignBrief) -> CampaignPlanResponse:
    query = db.query(models.InfluencerRecommendation)

    if brief.target_country:
        query = query.filter(models.InfluencerRecommendation.country == brief.target_country)
    if brief.target_language:
        query = query.filter(models.InfluencerRecommendation.language == brief.target_language)
    if brief.category:
        query = query.filter(models.InfluencerRecommendation.category == brief.category)
    if brief.platform:
        query = query.filter(models.InfluencerRecommendation.platform == brief.platform)

    candidates = query.order_by(models.InfluencerRecommendation.virality_score.desc()).all()

    selected = []
    total_cost = 0.0
    total_views = 0.0

    for rec in candidates:
        if len(selected) >= brief.desired_influencer_count:
            break

        cost = float(rec.cost_per_post or 0.0)
        if total_cost + cost > brief.budget:
            continue

        expected_views = float(rec.recent_avg_views or rec.follower_count or 0)

        selected.append(
            InfluencerPlanItem(
                influencer_id=rec.influencer_id,
                handle=rec.handle,
                platform=rec.platform,
                estimated_cost=cost,
                expected_views=expected_views,
                virality_score=rec.virality_score or 0.0,
            )
        )
        total_cost += cost
        total_views += expected_views

    return CampaignPlanResponse(
        influencers=selected,
        total_cost=total_cost,
        total_expected_views=total_views,
    )
