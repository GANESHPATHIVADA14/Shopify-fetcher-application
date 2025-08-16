from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Import the centralized settings object which reads from your .env file
from app.core.config import settings

# --- Database Configuration ---

# 1. Get the database connection string from our settings.
#    Example for MySQL: "mysql+pymysql://user:password@host:port/dbname"
DATABASE_URL = settings.DATABASE_URL

# 2. Initialize engine, SessionLocal, and Base as None initially.
engine = None
SessionLocal = None
Base = declarative_base() # Base is created regardless, models need to inherit from it.

# 3. Only configure the engine and session if a DATABASE_URL is actually provided.
#    This allows the app to run without a database for non-DB features.
if DATABASE_URL:
    # The SQLAlchemy engine is the entry point to the database.
    # pool_pre_ping=True helps prevent errors from stale database connections.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # The SessionLocal class is a "factory" for creating new database sessions.
    # Each instance of SessionLocal will be a database session.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    print("WARNING: DATABASE_URL not set. Database features will be disabled.")


# --- FastAPI Dependency ---

def get_db():
    """
    This is a FastAPI dependency that creates a new database session for each
    incoming request and ensures it's properly closed afterward.
    """
    # If the database is not configured, do nothing.
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        # 'yield' provides the database session to the API endpoint.
        yield db
    finally:
        # This 'finally' block ensures the session is closed after the
        # request is finished, even if an error occurred.
        db.close()