# services/vector_store.py
import faiss
import numpy as np
import pickle
import os
from typing import List, Dict


class FAISSVectorStore:
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.id_mapping: Dict[int, Dict] = {}
        print(f"✅ FAISS index created with dimension {dimension}")
    
    def add_embeddings(self, embeddings: np.ndarray, metadata: List[Dict]):
        if len(embeddings) == 0:
            return
        
        start_id = self.index.ntotal
        self.index.add(embeddings)
        
        for i, meta in enumerate(metadata):
            faiss_id = start_id + i
            self.id_mapping[faiss_id] = {
                "doc_id": meta.get("doc_id"),
                "chunk_id": meta.get("chunk_id")
            }
        
        print(f"✅ Added {len(embeddings)} vectors to FAISS. Total: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        if self.index.ntotal == 0:
            return []
        
        query = query_embedding.reshape(1, -1)
        scores, indices = self.index.search(query, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx in self.id_mapping:
                results.append({
                    "score": float(score),
                    "doc_id": self.id_mapping[idx]["doc_id"],
                    "chunk_id": self.id_mapping[idx]["chunk_id"]
                })
        
        return results
    
    def get_total_vectors(self) -> int:
        return self.index.ntotal
    
    def save(self, folder_path: str):
        os.makedirs(folder_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(folder_path, "faiss_index.bin"))
        with open(os.path.join(folder_path, "id_mapping.pkl"), "wb") as f:
            pickle.dump(self.id_mapping, f)
        print(f"✅ FAISS index saved to {folder_path}")
    
    def load(self, folder_path: str):
        index_path = os.path.join(folder_path, "faiss_index.bin")
        mapping_path = os.path.join(folder_path, "id_mapping.pkl")
        
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            print(f"✅ FAISS index loaded. Total vectors: {self.index.ntotal}")
        
        if os.path.exists(mapping_path):
            with open(mapping_path, "rb") as f:
                self.id_mapping = pickle.load(f)


# Singleton instance
vector_store = FAISSVectorStore(dimension=384)