#!/usr/bin/env python3
"""
Quick test to verify the database setup for tests is working correctly.
"""
import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # Test imports
    from core.database import Base
    from models.database import Post, Keyword, SentimentAnalysis, Report, CollectionTask
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    print("✅ All imports successful")
    
    # Test database creation
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    test_db_url = f"sqlite:///{db_path}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    
    # Test session creation
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    # Test basic database operations
    test_keyword = Keyword(
        term="test_keyword",
        category="test",
        platforms=["twitter"],
        language="ja"
    )
    session.add(test_keyword)
    session.commit()
    
    # Query the keyword back
    result = session.query(Keyword).filter(Keyword.term == "test_keyword").first()
    assert result is not None
    assert result.term == "test_keyword"
    
    print("✅ Database operations working correctly")
    
    # Cleanup
    session.close()
    engine.dispose()
    if os.path.exists(db_path):
        os.unlink(db_path)
    
    print("✅ Test database setup is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
