import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# =============================================
# METHOD 1: Simple Keyword Matching
# =============================================

def clean_text(text: str) -> str:
    """
    Text clean karo — lowercase, special characters hatao.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text


def get_keywords(text: str) -> set:
    """
    Text se unique keywords nikalo.
    Common words (stopwords) skip karo.
    """
    # Simple stopwords list
    stopwords = {
        'the', 'is', 'in', 'at', 'of', 'a', 'an', 'and', 'or', 'but',
        'to', 'for', 'on', 'with', 'by', 'from', 'as', 'into', 'this',
        'that', 'it', 'be', 'are', 'was', 'were', 'been', 'will', 'shall',
        'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could', 'would',
        'should', 'may', 'might', 'not', 'no', 'so', 'if', 'then', 'than',
        'too', 'very', 'just', 'about', 'also', 'what', 'which', 'who',
        'how', 'when', 'where', 'why', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own',
        'same', 'new', 'now', 'up', 'out', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'my', 'your', 'his',
        'her', 'its', 'our', 'their', 'me', 'him', 'us', 'them', 'i', 'you',
        'he', 'she', 'we', 'they'
    }
    
    words = clean_text(text).split()
    keywords = set()
    
    for word in words:
        if word not in stopwords and len(word) > 2:
            keywords.add(word)
    
    return keywords


def keyword_match_score(query: str, chunk_text: str) -> float:
    """
    Query ke keywords kitne chunk mein match ho rahe hain.
    Returns: 0.0 to 1.0 score
    """
    query_keywords = get_keywords(query)
    chunk_keywords = get_keywords(chunk_text)
    
    if not query_keywords:
        return 0.0
    
    # Kitne query keywords chunk mein mil gaye
    matched = query_keywords.intersection(chunk_keywords)
    score = len(matched) / len(query_keywords)
    
    return score


def search_chunks_keyword(query: str, chunks: list, top_k: int = 3) -> list:
    """
    Sabhi chunks ko keyword match score do aur top_k return karo.
    """
    results = []
    
    for chunk in chunks:
        score = keyword_match_score(query, chunk["text"])
        
        results.append({
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "score": round(score, 3),
            "method": "keyword_matching"
        })
    
    # Score ke hisaab se sort karo (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]


# =============================================
# METHOD 2: TF-IDF Based Matching (Better!)
# =============================================

def search_chunks_tfidf(query: str, chunks: list, top_k: int = 3) -> list:
    """
    TF-IDF vectors banake cosine similarity se best matching chunks dhundho.
    Keyword matching se zyada smart hai — word importance samajhta hai.
    """
    
    if not chunks:
        return []
    
    # Sab chunks ke text ki list banao
    chunk_texts = [chunk["text"] for chunk in chunks]
    
    # Query ko bhi add karo documents mein
    all_documents = chunk_texts + [query]
    
    # TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',  # Built-in stopwords removal
        max_features=5000       # Top 5000 words consider karo
    )
    
    # Sab documents ko vectors mein convert karo
    tfidf_matrix = vectorizer.fit_transform(all_documents)
    
    # Query vector last row mein hai
    query_vector = tfidf_matrix[-1]
    
    # Chunk vectors baaki sab rows mein hain
    chunk_vectors = tfidf_matrix[:-1]
    
    # Cosine similarity calculate karo
    similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
    
    # Top-k indices dhundho
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        results.append({
            "chunk_id": chunks[idx]["chunk_id"],
            "text": chunks[idx]["text"],
            "score": round(float(similarities[idx]), 3),
            "method": "tfidf"
        })
    
    return results


# =============================================
# MAIN SEARCH FUNCTION
# =============================================

def search_chunks(query: str, chunks: list, method: str = "tfidf", top_k: int = 3) -> list:
    """
    Convenience function — method choose karo.
    Default: tfidf (better accuracy)
    """
    if method == "keyword":
        return search_chunks_keyword(query, chunks, top_k)
    elif method == "tfidf":
        return search_chunks_tfidf(query, chunks, top_k)
    else:
        raise ValueError("Method must be 'keyword' or 'tfidf'")