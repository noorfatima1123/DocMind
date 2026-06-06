from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import shutil
import uuid
import numpy as np

from routes.auth import router as auth_router
from middleware.auth import get_current_user

from pdf_extractor import extract_text
from chunker import chunk_text
from db.postgres import get_db, init_db
from db.mongo import store_document_chunks, get_chunks_by_doc_id
from models.document import Document
from models.conversation import Conversation
from models.user import User

from services.embeddings import embedding_service
from services.vector_store import vector_store
from services.retriever import retriever_service

app = FastAPI(title="AI Learning Assistant - B4 Highlight")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

FAISS_INDEX_PATH = os.path.join(UPLOAD_FOLDER, "faiss_index")


# ---------- REQUEST MODELS ----------
class QueryRequest(BaseModel):
    question: str
    document_ids: list[str] = []
    chat_history: list[dict] = []
    top_k: int = 5
    search_method: str = "embedding"


# ---------- STARTUP ----------
@app.on_event("startup")
def startup():
    init_db()
    if os.path.exists(os.path.join(FAISS_INDEX_PATH, "faiss_index.bin")):
        vector_store.load(FAISS_INDEX_PATH)
        print(f"📂 FAISS index loaded from disk")
    print("✅ Database initialized!")
    print(f"📊 FAISS total vectors: {vector_store.get_total_vectors()}")


# ---------- BASIC ROUTES ----------
@app.get("/")
def read_root():
    return {
        "message": "AI Learning Assistant - B4 PDF Highlight",
        "total_documents_stored": vector_store.get_total_vectors()
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------- PDF UPLOAD ----------
@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    if not file.filename.endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed"}
        )
    
    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print(f"\n📄 Processing: {file.filename} (User: {current_user.email})")
    extracted_text = extract_text(file_path, method="pdfplumber")
    chunks = chunk_text(extracted_text, method="words", chunk_size=200, overlap=30)
    
    print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.generate_batch_embeddings(chunk_texts)
    print(f"✅ Generated {len(embeddings)} embeddings")
    
    metadata = [{"doc_id": file_id, "chunk_id": chunk["chunk_id"]} for chunk in chunks]
    vector_store.add_embeddings(embeddings, metadata)
    
    vector_store.save(FAISS_INDEX_PATH)
    print(f"💾 FAISS index saved to disk")
    
    doc = Document(
        id=uuid.UUID(file_id),
        user_id=current_user.id,
        title=file.filename.replace(".pdf", ""),
        filename=saved_filename,
        file_path=file_path,
        total_pages=0,
        total_chunks=len(chunks)
    )
    db.add(doc)
    db.commit()
    
    await store_document_chunks(file_id, chunks)
    
    return {
        "message": "PDF uploaded successfully",
        "document_id": file_id,
        "filename": file.filename,
        "total_chunks": len(chunks),
        "faiss_total_vectors": vector_store.get_total_vectors()
    }


# ---------- QUERY — With Source Citations ----------
@app.post("/query")
async def ask_question(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    if request.search_method == "embedding":
        
        if request.document_ids:
            all_results = []
            for doc_id in request.document_ids:
                doc_results = await retriever_service.retrieve(
                    query=request.question,
                    doc_id=doc_id,
                    top_k=request.top_k
                )
                all_results.extend(doc_results)
            
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            results = all_results[:request.top_k]
        else:
            results = await retriever_service.retrieve(
                query=request.question,
                doc_id=None,
                top_k=request.top_k
            )
        
        # 🆕 Get document titles for sources
        doc_titles = {}
        if results:
            for r in results[:5]:
                if r["doc_id"] not in doc_titles:
                    doc = db.query(Document).filter(Document.id == uuid.UUID(r["doc_id"])).first()
                    doc_titles[r["doc_id"]] = doc.title if doc else "Unknown"
        
        if not results:
            best_answer = "Sorry, no relevant content found."
            best_score = 0.0
            llm_info = {}
        else:
            from services.llm import generate_answer
            llm_response = await generate_answer(
                results[:3], 
                request.question,
                request.chat_history
            )
            best_answer = llm_response["answer"]
            best_score = results[0]["score"]
            llm_info = {
                "model": llm_response["model"],
                "sources_used": llm_response.get("sources_used", [])
            }
        
        primary_doc_id = request.document_ids[0] if request.document_ids else None
        conv = Conversation(
            user_id=current_user.id,
            document_id=uuid.UUID(primary_doc_id) if primary_doc_id else None,
            question=request.question,
            answer=best_answer,
            sources=str([{"doc_id": r["doc_id"], "chunk_id": r["chunk_id"]} for r in results])
        )
        db.add(conv)
        db.commit()
        
        return {
            "question": request.question,
            "search_method": "embedding (FAISS) + LLM",
            "documents_searched": len(request.document_ids) if request.document_ids else "all",
            "best_score": best_score,
            "answer": best_answer,
            "llm_info": llm_info,
            "retrieved_chunks": [
                {
                    "doc_id": r["doc_id"],
                    "doc_title": doc_titles.get(r["doc_id"], "Unknown"),  # 🆕
                    "chunk_id": r["chunk_id"],
                    "score": round(r["score"], 3),
                    "text_preview": r["text"][:150] + "..."
                }
                for r in results[:5]
            ]
        }
    
    else:
        if not request.document_ids:
            return JSONResponse(status_code=400, content={"error": "document_ids required"})
        
        all_chunks = []
        for doc_id in request.document_ids:
            chunks = await get_chunks_by_doc_id(doc_id)
            all_chunks.extend(chunks)
        
        from matcher import search_chunks
        results = search_chunks(request.question, all_chunks, method="tfidf", top_k=request.top_k)
        
        valid = [r for r in results if r["score"] > 0.01]
        best_answer = valid[0]["text"] if valid else "No relevant content found."
        
        conv = Conversation(
            user_id=current_user.id,
            document_id=uuid.UUID(request.document_ids[0]),
            question=request.question,
            answer=best_answer,
            sources=str([r["chunk_id"] for r in valid])
        )
        db.add(conv)
        db.commit()
        
        return {
            "question": request.question,
            "search_method": "tfidf",
            "documents_searched": len(request.document_ids),
            "answer": best_answer
        }


# ---------- LIST DOCUMENTS ----------
@app.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    docs = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.upload_date.desc()).all()
    
    return {
        "total": len(docs),
        "documents": [
            {
                "id": str(doc.id),
                "title": doc.title,
                "total_chunks": doc.total_chunks,
                "upload_date": str(doc.upload_date)
            }
            for doc in docs
        ]
    }


# ---------- PROFILE ----------
@app.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "created_at": str(current_user.created_at)
    }


# ---------- FAISS STATS ----------
@app.get("/faiss-stats")
def faiss_stats():
    return {
        "total_vectors": vector_store.get_total_vectors(),
        "dimension": embedding_service.dimension,
        "model_name": "all-MiniLM-L6-v2"
    }