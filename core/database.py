from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create metadata
metadata = MetaData()

# Create base class for models
Base = declarative_base(metadata=metadata)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)
