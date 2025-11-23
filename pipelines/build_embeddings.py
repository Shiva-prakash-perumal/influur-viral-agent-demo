import os
import pickle
import numpy as np
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://influur:influur@localhost:5432/influur_demo",
)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "data", "processed", "influencer_embeddings.pkl")

def fetch_influencer_texts():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        query = text(
            '''
            select
                i.influencer_id,
                i.content_style,
                coalesce(
                    (
                        select string_agg(caption, ' ')
                        from raw_posts p
                        where p.influencer_id = i.influencer_id
                    ), ''
                ) as sample_captions
            from raw_influencers i
            '''
        )
        result = conn.execute(query)
        rows = result.fetchall()
    return rows

def build_and_save_embeddings():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    rows = fetch_influencer_texts()

    ids = []
    vectors = []
    for influencer_id, content_style, sample_captions in rows:
        text = f"{content_style}. {sample_captions}"
        vec = model.encode(text, normalize_embeddings=True)
        ids.append(int(influencer_id))
        vectors.append(vec)

    vectors = np.vstack(vectors)

    os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
    with open(EMBEDDINGS_PATH, "wb") as f:
        pickle.dump({"ids": ids, "vectors": vectors}, f)

    print(f"Saved embeddings for {len(ids)} influencers at {EMBEDDINGS_PATH}")

if __name__ == "__main__":
    build_and_save_embeddings()
