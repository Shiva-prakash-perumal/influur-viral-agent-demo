from sqlalchemy import Column, Integer, String, Float, Numeric
from .database import Base

class InfluencerRecommendation(Base):
    __tablename__ = "mart_influencer_recommendations"
    # dbt created this in schema "public_marts", not "marts"
    __table_args__ = {"schema": "public_marts"}

    influencer_id = Column(Integer, primary_key=True)
    handle = Column(String)
    platform = Column(String)
    follower_count = Column(Integer)
    country = Column(String)
    language = Column(String)
    category = Column(String)
    content_style = Column(String)
    cost_per_post = Column(Numeric)
    age_bracket = Column(String)
    recent_avg_views = Column(Float)
    recent_engagement_rate = Column(Float)
    post_count_last_90d = Column(Integer)
    virality_score = Column(Float)