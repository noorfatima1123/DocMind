from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    APP_NAME: str = "AI Learning Assistant"
    VERSION: str = "1.0.0"
    
    # PostgreSQL
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "ai_learning_db")
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_learning_db")
    
    # Upload
    UPLOAD_FOLDER: str = "uploads"

settings = Settings()