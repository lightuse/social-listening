from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class Post(Base):
    """Social media post model"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    platform = Column(String(50), nullable=False)  # twitter, youtube, reddit, etc.
    content = Column(Text, nullable=False)
    author = Column(String(255))
    author_followers = Column(Integer, default=0)
    url = Column(String(500))
    posted_at = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Engagement metrics
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    
    # Metadata
    hashtags = Column(JSON)
    mentions = Column(JSON)
    media_urls = Column(JSON)
    
    # Analysis results
    analyses = relationship("SentimentAnalysis", back_populates="post")


class Keyword(Base):
    """Keywords/themes to monitor"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(255), nullable=False, unique=True)
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Monitoring settings
    platforms = Column(JSON)  # List of platforms to monitor
    language = Column(String(10), default="ja")
    
    # Related analyses
    analyses = relationship("SentimentAnalysis", back_populates="keyword")


class SentimentAnalysis(Base):
    """Sentiment analysis results"""
    __tablename__ = "sentiment_analyses"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False)
    
    # Sentiment scores
    sentiment_label = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1.0 to 1.0
    confidence = Column(Float)  # 0.0 to 1.0
    
    # Detailed analysis
    emotions = Column(JSON)  # joy, anger, fear, sadness, surprise, etc.
    topics = Column(JSON)  # extracted topics/themes
    keywords_found = Column(JSON)  # specific keywords found in post
    reasoning = Column(Text)  # analysis reasoning/explanation
    
    # AI analysis metadata
    model_used = Column(String(100))
    analysis_version = Column(String(20))
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="analyses")
    keyword = relationship("Keyword", back_populates="analyses")


class Report(Base):
    """Generated reports"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Report parameters
    keywords = Column(JSON)  # keywords included in report
    platforms = Column(JSON)  # platforms analyzed
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    
    # Report content
    summary = Column(Text)
    sentiment_summary = Column(JSON)  # overall sentiment breakdown
    key_insights = Column(JSON)  # key findings
    charts_data = Column(JSON)  # data for visualizations
    
    # Metadata
    status = Column(String(20), default="pending")  # pending, completed, failed
    generated_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(500))  # path to generated report file


class CollectionTask(Base):
    """Data collection tasks"""
    __tablename__ = "collection_tasks"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    keywords = Column(JSON)
    description = Column(Text)  # Task description/query
    
    # Task status
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    posts_collected = Column(Integer, default=0)
    errors = Column(JSON)
    report_data = Column(Text)  # Generated report data (JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_for = Column(DateTime)
