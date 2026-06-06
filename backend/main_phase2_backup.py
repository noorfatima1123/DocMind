from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import shutil
import uuid

from pdf_extractor import extract_text
from chunker import chunk_text
from matcher import search_chunks
from db.postgres import get_db, init_db
from db.mongo import store_document_chunks, get_chunks_by_doc_id
from models.document import Document

app = FastAPI(title="AI Learning Assistant")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- REQUEST MODELS ----------
class QueryRequest(BaseModel):
    question: str
    document_id: str = None  # Kaunsa document search karna hai
    top_k: int = 3
    method: str = "tfidf"


# ---------- STARTUP EVENT ----------
@app.on_event("startup")
def startup():
    """Server start hone pe tables create karo"""
    init_db()
    print("✅ Database initialized!")


# ---------- BASIC ROUTES ----------
@app.get("/")
def read_root():
    return {"message": "Server is running! AI Learning Assistant is ready."}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------- PDF UPLOAD ----------
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    # 1. Check PDF
    if not file.filename.endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed"}
        )
    
    # 2. Save file
    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 3. Extract text
    extracted_text = extract_text(file_path, method="pdfplumber")
    
    # 4. Chunk text
    chunks = chunk_text(extracted_text, method="words", chunk_size=200, overlap=30)
    
    # 5. Store document metadata in PostgreSQL
    doc = Document(
        id=uuid.UUID(file_id),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),  # Default user for now
        title=file.filename.replace(".pdf", ""),
        filename=saved_filename,
        file_path=file_path,
        total_pages=0,  # We'll calculate later if needed
        total_chunks=len(chunks)
    )
    db.add(doc)
    db.commit()
    
    # 6. Store chunks in MongoDB
    await store_document_chunks(file_id, chunks)
    
    return {
        "message": "PDF uploaded and processed successfully",
        "document_id": file_id,
        "filename": file.filename,
        "text_length": len(extracted_text),
        "word_count": len(extracted_text.split()),
        "total_chunks": len(chunks)
    }


# ---------- QUERY ENDPOINT ----------
@app.post("/query")
async def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    
    # 1. Get chunks from MongoDB
    if request.document_id:
        chunks = await get_chunks_by_doc_id(request.document_id)
        if not chunks:
            return JSONResponse(
                status_code=404,
                content={"error": "Document not found"}
            )
    else:
        return JSONResponse(
            status_code=400,
            content={"error": "Please provide a document_id"}
        )
    
    # 2. Search relevant chunks
    results = search_chunks(
        query=request.question,
        chunks=chunks,
        method=request.method,
        top_k=request.top_k
    )
    
    # 3. Filter by score threshold
    SCORE_THRESHOLD = 0.01
    valid_results = [r for r in results if r["score"] > SCORE_THRESHOLD]
    
    if valid_results:
        best_answer = valid_results[0]["text"]
        best_score = valid_results[0]["score"]
    else:
        best_answer = "Sorry, no relevant content found for your question in this document."
        best_score = 0.0
    
    # 4. Save conversation to PostgreSQL
    from models.conversation import Conversation
    conv = Conversation(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        document_id=uuid.UUID(request.document_id) if request.document_id else None,
        question=request.question,
        answer=best_answer,
        sources=str([r["chunk_id"] for r in valid_results])
    )
    db.add(conv)
    db.commit()
    
    return {
        "question": request.question,
        "method": request.method,
        "document_id": request.document_id,
        "best_score": best_score,
        "answer": best_answer,
        "all_scores": [{"chunk_id": r["chunk_id"], "score": r["score"]} for r in results[:5]],
        "relevant_chunks": valid_results[:3]
    }


# ---------- LIST DOCUMENTS ----------
@app.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.upload_date.desc()).all()
    return {
        "total": len(docs),
        "documents": [
            {
                "id": str(doc.id),
                "title": doc.title,
                "filename": doc.filename,
                "total_chunks": doc.total_chunks,
                "upload_date": str(doc.upload_date)
            }
            for doc in docs
        ]
    }