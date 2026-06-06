# db/mongo.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_learning_db")

# MongoDB async client
client = AsyncIOMotorClient(MONGO_URI)
database = client[MONGO_DB_NAME]

# Collections
documents_collection = database["documents"]
chunks_collection = database["chunks"]


async def check_mongo_connection():
    """Check MongoDB connection"""
    try:
        await client.admin.command("ping")
        print("✅ MongoDB connected successfully!")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")


async def store_document_chunks(doc_id: str, chunks: list):
    """
    Document ke chunks MongoDB mein store karo.
    Structure:
    {
        "doc_id": "uuid",
        "chunks": [
            {"chunk_id": 0, "text": "...", "word_count": 200},
            ...
        ]
    }
    """
    document = {
        "doc_id": doc_id,
        "chunks": chunks
    }
    result = await documents_collection.insert_one(document)
    print(f"✅ Stored {len(chunks)} chunks for document {doc_id}")
    return result.inserted_id


async def get_chunks_by_doc_id(doc_id: str) -> list:
    """Document ke saare chunks retrieve karo"""
    doc = await documents_collection.find_one({"doc_id": doc_id})
    if doc:
        return doc.get("chunks", [])
    return []


async def get_chunk_by_id(doc_id: str, chunk_id: int) -> dict:
    """Specific chunk retrieve karo"""
    doc = await documents_collection.find_one(
        {"doc_id": doc_id, "chunks.chunk_id": chunk_id},
        {"chunks.$": 1}
    )
    if doc and doc.get("chunks"):
        return doc["chunks"][0]
    return None