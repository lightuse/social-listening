#!/usr/bin/env python3
"""
Database initialization script for Social Listening System
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import SessionLocal
from models.database import Keyword
from datetime import datetime


def create_sample_keywords():
    """Create sample keywords for testing"""
    
    sample_keywords = [
        {
            "term": "AI人工知能",
            "category": "テクノロジー",
            "platforms": ["twitter", "youtube", "reddit"],
            "language": "ja"
        },
        {
            "term": "機械学習",
            "category": "テクノロジー", 
            "platforms": ["twitter", "youtube", "reddit"],
            "language": "ja"
        },
        {
            "term": "ChatGPT",
            "category": "AI製品",
            "platforms": ["twitter", "youtube", "reddit"],
            "language": "ja"
        },
        {
            "term": "データサイエンス",
            "category": "テクノロジー",
            "platforms": ["twitter", "youtube", "reddit"],
            "language": "ja"
        },
        {
            "term": "Python",
            "category": "プログラミング",
            "platforms": ["twitter", "youtube", "reddit"],
            "language": "ja"
        }
    ]
    
    db = SessionLocal()
    try:
        for keyword_data in sample_keywords:
            # Check if keyword already exists
            existing = db.query(Keyword).filter(Keyword.term == keyword_data["term"]).first()
            if not existing:
                keyword = Keyword(**keyword_data)
                db.add(keyword)
        
        db.commit()
        print("✅ Sample keywords created successfully")
        
    except Exception as e:
        print(f"❌ Error creating sample keywords: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main initialization function"""
    print("🚀 Initializing Social Listening Database...")
    
    # Create data directory if it doesn't exist
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize database
        from core.database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Create sample keywords
        create_sample_keywords()
        
        print("🎉 Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Configure your .env file with API keys")
        print("2. Run: python main.py")
        print("3. Visit: http://localhost:8001")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
