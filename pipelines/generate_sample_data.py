import random
from datetime import datetime, timedelta
import os
import pandas as pd

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

NUM_INFLUENCERS = 200
MIN_POSTS_PER_INFLUENCER = 20
MAX_POSTS_PER_INFLUENCER = 80

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)

PLATFORMS = ["tiktok", "instagram", "youtube"]
COUNTRIES = ["US", "MX", "BR", "GB", "ES", "FR", "DE"]
LANG_BY_COUNTRY = {
    "US": ["en", "es"],
    "MX": ["es"],
    "BR": ["pt"],
    "GB": ["en"],
    "ES": ["es"],
    "FR": ["fr"],
    "DE": ["de"],
}
CATEGORIES = [
    "music",
    "beauty",
    "gaming",
    "fitness",
    "comedy",
    "education",
    "fashion",
]
CONTENT_STYLES = [
    "high energy dance",
    "storytelling vlogs",
    "tutorials and how to",
    "reaction content",
    "skits and comedy",
    "product reviews",
    "lifestyle b roll",
]
AGE_BRACKETS = ["18-24", "25-34", "35-44"]
AUDIO_TYPES = ["original", "trending", "catalogue"]

CAMPAIGNS = [
    "reggaeton_launch_q2",
    "beauty_summer_2025",
    "gaming_console_drop",
    "fitness_january_push",
    "back_to_school_2025",
    "null",
]

CAPTION_TEMPLATES = [
    "New drop just landed, what do you think",
    "Trying something different today",
    "You asked for it so here it is",
    "Tag a friend who needs to see this",
    "Cannot believe this just happened",
    "Day {n} of posting until this goes viral",
    "Behind the scenes of the next project",
    "POV you are listening to this on repeat",
    "This audio is stuck in my head",
]

def random_handle(category: str, idx: int) -> str:
    base = category.replace(" ", "")
    return f"@{base}{idx:04d}"

def sample_influencers(num_influencers: int) -> pd.DataFrame:
    rows = []
    for i in range(1, num_influencers + 1):
        platform = random.choice(PLATFORMS)
        country = random.choice(COUNTRIES)
        language = random.choice(LANG_BY_COUNTRY[country])
        category = random.choice(CATEGORIES)
        content_style = random.choice(CONTENT_STYLES)
        age_bracket = random.choice(AGE_BRACKETS)

        followers = int(10 ** random.uniform(4, 7))
        avg_views = int(followers * random.uniform(0.05, 0.6))
        engagement_rate = round(random.uniform(0.02, 0.15), 4)

        estimated_cpm = random.uniform(5, 35)
        cost_per_post = round((avg_views / 1000.0) * estimated_cpm, 2)

        handle = random_handle(category, i)

        rows.append(
            {
                "influencer_id": i,
                "handle": handle,
                "platform": platform,
                "follower_count": followers,
                "avg_views": avg_views,
                "engagement_rate": engagement_rate,
                "country": country,
                "language": language,
                "category": category,
                "content_style": content_style,
                "cost_per_post": cost_per_post,
                "age_bracket": age_bracket,
            }
        )
    return pd.DataFrame(rows)

def generate_caption(category: str, content_style: str) -> str:
    template = random.choice(CAPTION_TEMPLATES)
    extra = ""
    if category == "music":
        extra = " New track out now, link in bio."
    elif category == "beauty":
        extra = " Full routine and products in the description."
    elif category == "gaming":
        extra = " Streaming the full run later tonight."
    elif category == "fitness":
        extra = " Save this for your next workout."
    elif category == "education":
        extra = " Let me know what topic to cover next."
    return f"{template.format(n=random.randint(1, 30))}. {content_style.capitalize()}. {extra}".strip()

def sample_posts(influencers_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    post_id = 1

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=120)

    for _, inf in influencers_df.iterrows():
        influencer_id = int(inf["influencer_id"])
        platform = inf["platform"]
        category = inf["category"]
        content_style = inf["content_style"]
        base_views = int(inf["avg_views"])
        engagement_rate = float(inf["engagement_rate"])

        num_posts = random.randint(MIN_POSTS_PER_INFLUENCER, MAX_POSTS_PER_INFLUENCER)

        for _ in range(num_posts):
            posted_at = start_date + timedelta(
                seconds=random.randint(0, int((end_date - start_date).total_seconds()))
            )

            volatility = random.uniform(0.4, 1.8)
            views = max(100, int(base_views * volatility))

            base_eng = engagement_rate * random.uniform(0.7, 1.3)
            likes = max(0, int(views * base_eng * random.uniform(0.6, 0.9)))
            comments = max(0, int(views * base_eng * random.uniform(0.05, 0.15)))
            shares = max(0, int(views * base_eng * random.uniform(0.05, 0.25)))

            audio_type = random.choice(AUDIO_TYPES)

            campaign_tag = random.choice(CAMPAIGNS)
            if campaign_tag == "null":
                campaign_tag = ""

            caption = generate_caption(category, content_style)

            rows.append(
                {
                    "post_id": post_id,
                    "influencer_id": influencer_id,
                    "platform": platform,
                    "posted_at": posted_at.isoformat(),
                    "caption": caption,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "audio_type": audio_type,
                    "campaign_tag": campaign_tag,
                }
            )
            post_id += 1

    return pd.DataFrame(rows)

def main():
    influencers_df = sample_influencers(NUM_INFLUENCERS)
    posts_df = sample_posts(influencers_df)

    influencers_path = os.path.join(DATA_DIR, "influencers.csv")
    posts_path = os.path.join(DATA_DIR, "posts.csv")

    influencers_df.to_csv(influencers_path, index=False)
    posts_df.to_csv(posts_path, index=False)

    print(f"Generated {len(influencers_df)} influencers to {influencers_path}")
    print(f"Generated {len(posts_df)} posts to {posts_path}")

if __name__ == "__main__":
    main()
