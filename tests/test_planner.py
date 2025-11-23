from service.planner import plan_campaign
from service.schemas import CampaignBrief
from service.database import SessionLocal
from service import models

def test_plan_campaign_smoke():
    db = SessionLocal()
    try:
        brief = CampaignBrief(
            objective="Test campaign",
            target_country=None,
            target_language=None,
            category=None,
            platform=None,
            budget=10000,
            desired_influencer_count=10,
        )
        # This will return empty if the mart is empty, but should not raise
        result = plan_campaign(db, brief)
        assert result.total_cost >= 0
        assert result.total_expected_views >= 0
    finally:
        db.close()
