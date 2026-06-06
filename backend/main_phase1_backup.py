from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel       # 🆕 Request body ke liye
import os
import shutil

from pdf_extractor import extract_text
from chunker import chunk_text
from matcher import search_chunks     # 🆕 Matcher import

app = FastAPI(title="AI Learning Assistant")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 🆕 Global variable — last uploaded document ke chunks store karo
# (Phase 2 mein database mein jayenge, abhi memory mein rakhte hain)
stored_chunks = []


# ---------- REQUEST MODELS ----------
class QueryRequest(BaseModel):
    question: str
    top_k: int = 3
    method: str = "tfidf"  # "keyword" ya "tfidf"


# ---------- BASIC ROUTES ----------
@app.get("/")
def read_root():
    return {"message": "Server is running! AI Learning Assistant is ready."}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------- PDF UPLOAD ----------
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global stored_chunks  # Global variable use karenge
    
    if not file.filename.endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed"}
        )
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    extracted_text = extract_text(file_path, method="pdfplumber")
    chunks = chunk_text(extracted_text, method="words", chunk_size=200, overlap=30)
    
    # 🆕 Chunks memory mein store karo (taake query kar sakein)
    stored_chunks = chunks
    
    return {
        "message": "PDF uploaded and processed successfully",
        "filename": file.filename,
        "text_length": len(extracted_text),
        "word_count": len(extracted_text.split()),
        "total_chunks": len(chunks),
        "first_chunk_preview": chunks[0]["text"][:200] + "..." if chunks else "No chunks"
    }


# ---------- 🆕 QUERY ENDPOINT ----------
@app.post("/query")
async def ask_question(request: QueryRequest):
    global stored_chunks
    
    if not stored_chunks:
        return JSONResponse(
            status_code=400,
            content={"error": "No document uploaded yet. Please upload a PDF first."}
        )
    
    # Search relevant chunks
    results = search_chunks(
        query=request.question,
        chunks=stored_chunks,
        method=request.method,
        top_k=request.top_k
    )
    
    # 🆕 FIX: Score threshold check karo
    SCORE_THRESHOLD = 0.01  # Minimum score to consider a match
    
    valid_results = [r for r in results if r["score"] > SCORE_THRESHOLD]
    
    if valid_results:
        # Best matching chunk lo
        best_answer = valid_results[0]["text"]
        best_score = valid_results[0]["score"]
    else:
        # Koi match nahi mila
        best_answer = "Sorry, no relevant content found for your question in the uploaded document."
        best_score = 0.0
    
    return {
        "question": request.question,
        "method": request.method,
        "best_score": best_score,
        "answer": best_answer,
        "all_scores": [{"chunk_id": r["chunk_id"], "score": r["score"]} for r in results],
        "relevant_chunks": valid_results if valid_results else []
    }