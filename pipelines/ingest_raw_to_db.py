import os
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://influur:influur@localhost:5432/influur_demo",
)

def load_csv_to_table(csv_path: str, table_name: str):
    engine = create_engine(DATABASE_URL)
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into {table_name}")

if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    influencers_path = os.path.join(base_dir, "data", "raw", "influencers.csv")
    posts_path = os.path.join(base_dir, "data", "raw", "posts.csv")

    load_csv_to_table(influencers_path, "raw_influencers")
    load_csv_to_table(posts_path, "raw_posts")
