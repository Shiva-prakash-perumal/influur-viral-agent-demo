import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "data", "processed", "influencer_embeddings.pkl")

class EmbeddingsStore:
    def __init__(self):
        if not os.path.exists(EMBEDDINGS_PATH):
            raise FileNotFoundError(
                f"Embeddings file not found at {EMBEDDINGS_PATH}. "
                "Run pipelines/build_embeddings.py first."
            )

        with open(EMBEDDINGS_PATH, "rb") as f:
            data = pickle.load(f)
        self.ids = data["ids"]
        self.vectors = data["vectors"]
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def get_lookalike_by_influencer(self, influencer_id: int, top_k: int = 10):
        if influencer_id not in self.ids:
            return []

        idx = self.ids.index(influencer_id)
        base_vec = self.vectors[idx]
        scores = self.vectors @ base_vec
        top_idx = np.argsort(scores)[::-1][: top_k + 1]

        results = []
        for i in top_idx:
            if self.ids[i] == influencer_id:
                continue
            results.append((self.ids[i], float(scores[i])))
            if len(results) >= top_k:
                break
        return results

    def search_by_brief(self, text: str, top_k: int = 10):
        vec = self.model.encode(text, normalize_embeddings=True)
        scores = self.vectors @ vec
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(self.ids[i], float(scores[i])) for i in top_idx]
