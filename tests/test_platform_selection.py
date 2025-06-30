"""Test platform selection logic for social listening dashboard"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from main import app
from api.routes.analysis import AnalysisRequest
from services.data_collector import SocialMediaCollector


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_data_collector():
    with patch('api.routes.analysis.data_collector') as mock:
        yield mock


@pytest.fixture
def mock_sentiment_engine():
    with patch('api.routes.analysis.sentiment_engine') as mock:
        mock.initialize = AsyncMock()
        mock.analyze_sentiment = AsyncMock(return_value={
            'sentiment_label': 'positive',
            'sentiment_score': 0.8,
            'confidence': 0.9,
            'emotions': {'joy': 0.7},
            'topics': ['test'],
            'keywords_found': ['test'],
            'model_used': 'claude',
            'analysis_version': '1.0'
        })
        yield mock


class TestPlatformSelection:
    """Test platform selection logic in analysis endpoints"""
    
    def test_analyze_with_valid_platforms(self, client, override_get_db, mock_data_collector, mock_sentiment_engine):
        """Test analysis with valid platform selection"""
        # Mock available platforms
        mock_data_collector.get_available_platforms.return_value = ['youtube', 'reddit']
        mock_data_collector.collect_all_platforms = AsyncMock(return_value=[])
        
        # Request with valid platforms
        response = client.post("/api/v1/analyze", json={
            "keywords": ["test"],
            "platforms": ["youtube", "reddit"],
            "max_posts_per_platform": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["platforms"] == ["youtube", "reddit"]
        assert "task_id" in data
        
    def test_analyze_with_invalid_platforms(self, client, override_get_db, mock_data_collector):
        """Test analysis with invalid platform selection"""
        # Mock available platforms (Twitter not available)
        mock_data_collector.get_available_platforms.return_value = ['youtube', 'reddit']
        
        # Request with invalid platform
        response = client.post("/api/v1/analyze", json={
            "keywords": ["test"],
            "platforms": ["twitter", "facebook"],  # Both unavailable
            "max_posts_per_platform": 10
        })
        
        assert response.status_code == 400
        assert "No valid platforms available" in response.json()["detail"]
        
    def test_analyze_with_mixed_platforms(self, client, override_get_db, mock_data_collector, mock_sentiment_engine):
        """Test analysis with mix of valid and invalid platforms"""
        # Mock available platforms
        mock_data_collector.get_available_platforms.return_value = ['youtube', 'reddit']
        mock_data_collector.collect_all_platforms = AsyncMock(return_value=[])
        
        # Request with mix of valid and invalid platforms
        response = client.post("/api/v1/analyze", json={
            "keywords": ["test"],
            "platforms": ["twitter", "youtube", "facebook", "reddit"],  # twitter and facebook unavailable
            "max_posts_per_platform": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        # Should only include valid platforms
        assert set(data["platforms"]) == {"youtube", "reddit"}
        
    def test_analyze_without_platforms(self, client, override_get_db, mock_data_collector, mock_sentiment_engine):
        """Test analysis without specifying platforms (should use all available)"""
        # Mock available platforms
        mock_data_collector.get_available_platforms.return_value = ['youtube', 'reddit']
        mock_data_collector.collect_all_platforms = AsyncMock(return_value=[])
        
        # Request without platforms specified
        response = client.post("/api/v1/analyze", json={
            "keywords": ["test"],
            "max_posts_per_platform": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        # Should use all available platforms
        assert set(data["platforms"]) == {"youtube", "reddit"}
        
    def test_analyze_with_twitter_unavailable(self, client, override_get_db, mock_data_collector, mock_sentiment_engine):
        """Test that Twitter API is not called when Twitter is not available"""
        # Mock available platforms (Twitter not available due to API issues)
        mock_data_collector.get_available_platforms.return_value = ['youtube', 'reddit']
        mock_data_collector.collect_all_platforms = AsyncMock(return_value=[])
        
        # Request specifically for Twitter (which should be filtered out)
        response = client.post("/api/v1/analyze", json={
            "keywords": ["test"],
            "platforms": ["twitter"],
            "max_posts_per_platform": 10
        })
        
        # Should fail because no valid platforms
        assert response.status_code == 400
        assert "No valid platforms available" in response.json()["detail"]
        
    def test_analyze_with_all_platforms_available(self, client, override_get_db, mock_data_collector, mock_sentiment_engine):
        """Test analysis when all platforms are available"""
        # Mock all platforms as available
        mock_data_collector.get_available_platforms.return_value = ['twitter', 'youtube', 'reddit']
        mock_data_collector.collect_all_platforms = AsyncMock(return_value=[])
        
        # Request with all platforms
        response = client.post("/api/v1/analyze", json={
            "keywords": ["test"],
            "platforms": ["twitter", "youtube", "reddit"],
            "max_posts_per_platform": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        # Should include all platforms
        assert set(data["platforms"]) == {"twitter", "youtube", "reddit"}
        
    def test_analyze_platform_validation_logging(self, client, override_get_db, mock_data_collector, mock_sentiment_engine):
        """Test that platform validation is properly logged"""
        # Mock available platforms
        mock_data_collector.get_available_platforms.return_value = ['youtube', 'reddit']
        mock_data_collector.collect_all_platforms = AsyncMock(return_value=[])
        
        with patch('api.routes.analysis.logger') as mock_logger:
            # Request with mix of valid and invalid platforms
            response = client.post("/api/v1/analyze", json={
                "keywords": ["test"],
                "platforms": ["twitter", "youtube", "facebook"],
                "max_posts_per_platform": 10
            })
            
            assert response.status_code == 200
            
            # Check that warning was logged for unavailable platforms
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Unavailable platforms skipped" in warning_call
            assert "twitter" in warning_call or "facebook" in warning_call


class TestDataCollectorPlatforms:
    """Test data collector platform availability"""
    
    def test_get_available_platforms_integration(self):
        """Test that get_available_platforms works correctly"""
        collector = SocialMediaCollector()
        platforms = collector.get_available_platforms()
        
        # Should return a list of strings
        assert isinstance(platforms, list)
        for platform in platforms:
            assert isinstance(platform, str)
            assert platform in ['twitter', 'youtube', 'reddit']
            
    @patch('services.data_collector.settings.TWITTER_BEARER_TOKEN', None)
    @patch('services.data_collector.settings.YOUTUBE_API_KEY', 'test_key')  
    @patch('services.data_collector.settings.REDDIT_CLIENT_ID', 'test_id')
    @patch('services.data_collector.settings.REDDIT_CLIENT_SECRET', 'test_secret')
    def test_platform_availability_based_on_credentials(self):
        """Test platform availability based on credential checks"""
        collector = SocialMediaCollector()
        platforms = collector.get_available_platforms()
        
        # Should only include platforms with valid credentials
        assert 'youtube' in platforms
        assert 'reddit' in platforms
        assert 'twitter' not in platforms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
