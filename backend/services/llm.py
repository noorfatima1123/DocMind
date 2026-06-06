# services/llm.py
import os
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))


def build_prompt(context_chunks: list, question: str, chat_history: list = []) -> str:
    context_text = "\n\n".join([chunk['text'][:500] for chunk in context_chunks[:3]])
    
    # Chat history format karo
    history_text = ""
    if chat_history:
        history_text = "PREVIOUS CONVERSATION:\n"
        for msg in chat_history[-4:]:  # Last 4 messages
            history_text += f"Student: {msg['question']}\n"
            history_text += f"Assistant: {msg['answer'][:200]}\n\n"
    
    return f"""You are an AI Learning Assistant. Answer based on the context and conversation history.

{history_text}
CONTEXT:
{context_text}

STUDENT'S QUESTION: {question}

INSTRUCTIONS:
1. Answer in clear, simple English (2-4 sentences)
2. If this is a follow-up question (e.g., "what about X?", "how does it work?", "why?"), use the conversation history to understand what is being referred to
3. Only use information from the context above
4. If context doesn't contain the answer, say so

YOUR ANSWER:"""


async def generate_answer(context_chunks: list, question: str, chat_history: list = []) -> dict:
    if not context_chunks:
        return {"answer": "No context.", "sources_used": [], "model": "none"}
    
    try:
        prompt = build_prompt(context_chunks, question, chat_history)
        
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "sources_used": [0, 1, 2],
            "model": "llama-3.3-70b (Groq)"
        }
    
    except Exception as e:
        print(f"❌ Groq Error: {e}")
        # Fallback — return best chunk
        return {
            "answer": context_chunks[0]['text'][:300] if context_chunks else "Sorry, I couldn't generate an answer.",
            "sources_used": [0],
            "model": "fallback",
            "error": str(e)
        }