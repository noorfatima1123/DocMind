import re


def split_into_sentences(text: str) -> list:
    """
    Text ko sentences mein todta hai.
    """
    # Sentence endings pe split karo
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Empty sentences hatao, strip karo
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def chunk_text_by_words(text: str, chunk_size: int = 200, overlap: int = 30) -> list:
    """
    Text ko chunks mein todta hai based on word count.
    Pehle sentences mein todta hai, phir words count karta hai.
    """
    
    # Pehle sentences mein todo
    sentences = split_into_sentences(text)
    
    chunks = []
    chunk_id = 0
    current_chunk_sentences = []
    current_word_count = 0
    
    for sentence in sentences:
        sentence_words = len(sentence.split())
        
        # Agar current chunk mein ye sentence add karne se chunk_size exceed ho jaye
        if current_word_count + sentence_words > chunk_size and current_chunk_sentences:
            # Current chunk save karo
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "word_count": current_word_count
            })
            
            # Overlap ke liye — last 1-2 sentences rakh lo
            overlap_sentences = current_chunk_sentences[-2:] if len(current_chunk_sentences) >= 2 else current_chunk_sentences
            
            # Naya chunk start karo
            chunk_id += 1
            current_chunk_sentences = overlap_sentences.copy()
            current_word_count = sum(len(s.split()) for s in overlap_sentences)
        
        # Sentence add karo current chunk mein
        current_chunk_sentences.append(sentence)
        current_word_count += sentence_words
    
    # Last chunk save karo
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text,
            "word_count": current_word_count
        })
    
    print(f"Total sentences: {len(sentences)}")
    print(f"Total chunks created: {len(chunks)}")
    return chunks


def chunk_text(text: str, method: str = "words", **kwargs) -> list:
    """
    Convenience function.
    """
    if method == "words":
        return chunk_text_by_words(text, **kwargs)
    else:
        raise ValueError("Method must be 'words'")