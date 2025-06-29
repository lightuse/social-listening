"""
pytest共通設定とフィクスチャ
"""

import pytest
import asyncio
from pathlib import Path
import sys
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのパスを追加
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from core.database import Base, get_db
from models.database import Post, Keyword, SentimentAnalysis, Report, CollectionTask  # Import specific models


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で使用するイベントループ"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_engine():
    """テスト用データベースエンジンを作成"""
    # Create a temporary database file for testing
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create test database URL
    test_db_url = f"sqlite:///{db_path}"
    
    # Create engine for test database
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_db_session(test_db_engine):
    """テスト用データベースセッション"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_db_engine
    )
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(test_db_session):
    """データベース依存関係をテスト用にオーバーライド"""
    from core.database import get_db
    from main import app
    
    def _get_test_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def aws_credentials():
    """AWS認証情報のフィクスチャ"""
    auth_kwargs = {
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    }
    
    aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
    if aws_session_token:
        auth_kwargs["aws_session_token"] = aws_session_token
    
    return auth_kwargs


@pytest.fixture
async def bedrock_engine():
    """BedrockSentimentEngineのフィクスチャ"""
    from services.bedrock_engine import BedrockSentimentEngine
    
    engine = BedrockSentimentEngine()
    await engine.initialize()
    yield engine
    # クリーンアップは特に不要


@pytest.fixture
def sample_sentiment_data():
    """テスト用感情分析データ"""
    return [
        {
            "sentiment_label": "positive",
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "emotions": {"joy": 0.8, "trust": 0.7},
            "topics": ["AI技術", "イノベーション"]
        },
        {
            "sentiment_label": "negative", 
            "sentiment_score": -0.6,
            "confidence": 0.8,
            "emotions": {"anger": 0.7, "sadness": 0.5},
            "topics": ["サービス不満", "対応遅延"]
        },
        {
            "sentiment_label": "neutral",
            "sentiment_score": 0.1,
            "confidence": 0.7,
            "emotions": {"trust": 0.4},
            "topics": ["日常", "情報共有"]
        }
    ]


def pytest_collection_modifyitems(config, items):
    """テストアイテムの自動マーキング"""
    for item in items:
        # AWS関連のテストにマーカーを自動追加
        if "aws" in item.name.lower() or "bedrock" in item.name.lower():
            item.add_marker(pytest.mark.aws)
        
        # 統合テストのマーカー
        if "integration" in item.name.lower() or "full" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # 遅いテストのマーカー
        if "slow" in item.name.lower() or "report" in item.name.lower():
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """テスト実行前のセットアップ"""
    # AWS関連のテストは認証情報をチェック
    if "aws" in [mark.name for mark in item.iter_markers()]:
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            pytest.skip("AWS credentials not configured")


def pytest_configure(config):
    """pytest設定"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "aws: marks tests that require AWS credentials"
    )
    config.addinivalue_line(
        "markers", "bedrock: marks tests that require AWS Bedrock access"
    )
