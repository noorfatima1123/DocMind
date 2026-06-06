# services/embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    """
    Text ko embeddings (vectors) mein convert karta hai.
    Embeddings = text ka mathematical representation.
    Similar text ke embeddings similar hote hain.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Model load karo.
        all-MiniLM-L6-v2:
        - Fast (chhota model)
        - 384 dimensions
        - English ke liye accha
        - Free & open source
        """
        print(f"🔄 Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # MiniLM ke liye
        print(f"✅ Model loaded! Dimension: {self.dimension}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Single text ka embedding generate karo.
        Input: "Machine learning is..."
        Output: [0.12, -0.34, 0.56, ...] (384 numbers)
        """
        return self.model.encode(text, normalize_embeddings=True)
    
    def generate_batch_embeddings(self, texts: list) -> np.ndarray:
        """
        Multiple texts ke embeddings ek saath generate karo.
        Batch processing fast hoti hai.
        
        Input: ["chunk1 text", "chunk2 text", ...]
        Output: [[0.1, 0.2, ...], [0.3, 0.4, ...], ...]
        """
        return self.model.encode(texts, normalize_embeddings=True)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Do embeddings ke beech similarity calculate karo.
        Cosine similarity → 1.0 (same) to -1.0 (opposite)
        """
        return float(np.dot(embedding1, embedding2))


# Singleton instance — ek hi baar model load hoga
embedding_service = EmbeddingService()