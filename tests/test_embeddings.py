import os
import pytest

from service.embeddings_store import EmbeddingsStore

def test_embeddings_store_init():
    # Skip if embeddings file not present
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    emb_path = os.path.join(base_dir, "data", "processed", "influencer_embeddings.pkl")
    if not os.path.exists(emb_path):
        pytest.skip("Embeddings file not generated yet")
    store = EmbeddingsStore()
    assert len(store.ids) > 0
