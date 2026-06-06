# services/retriever.py
from services.embeddings import embedding_service
from services.vector_store import vector_store
from db.mongo import get_chunks_by_doc_id


class RetrieverService:
    """
    Retrieval pipeline:
    1. Query ka embedding banao
    2. FAISS mein search karo
    3. MongoDB se actual chunk text fetch karo
    """
    
    async def retrieve(self, query: str, doc_id: str = None, top_k: int = 5) -> list:
        """
        Query ke liye relevant chunks retrieve karo.
        
        Returns:
        [
            {"text": "...", "score": 0.85, "chunk_id": 5, "doc_id": "..."},
            ...
        ]
        """
        # Step 1: Query embedding banao
        print(f"🔍 Generating embedding for query: '{query[:50]}...'")
        query_embedding = embedding_service.generate_embedding(query)
        
        # Step 2: FAISS search
        faiss_results = vector_store.search(query_embedding, k=top_k)
        
        if not faiss_results:
            print("❌ No results from FAISS")
            return []
        
        # Step 3: Get actual text from MongoDB
        results = []
        for fr in faiss_results:
            # Agar specific document search karna hai to filter
            if doc_id and fr["doc_id"] != doc_id:
                continue
            
            # MongoDB se chunk text fetch karo
            chunks = await get_chunks_by_doc_id(fr["doc_id"])
            chunk_text = ""
            for chunk in chunks:
                if chunk.get("chunk_id") == fr["chunk_id"]:
                    chunk_text = chunk.get("text", "")
                    break
            
            if chunk_text:
                results.append({
                    "text": chunk_text,
                    "score": fr["score"],
                    "chunk_id": fr["chunk_id"],
                    "doc_id": fr["doc_id"]
                })
        
        print(f"✅ Retrieved {len(results)} chunks")
        return results


# Singleton instance
retriever_service = RetrieverService()