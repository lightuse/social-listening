"""Simple unit tests for platform selection logic"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from api.routes.analysis import AnalysisRequest
from services.data_collector import SocialMediaCollector


class TestPlatformLogicUnit:
    """Unit tests for platform selection logic"""
    
    def test_platform_filtering_logic(self):
        """Test the core platform filtering logic"""
        # Mock available platforms
        available_platforms = ['youtube', 'reddit']
        requested_platforms = ['twitter', 'youtube', 'facebook', 'reddit']
        
        # Test the filtering logic
        valid_platforms = [p for p in requested_platforms if p in available_platforms]
        unavailable_platforms = [p for p in requested_platforms if p not in available_platforms]
        
        assert valid_platforms == ['youtube', 'reddit']
        assert unavailable_platforms == ['twitter', 'facebook']
        
    def test_platform_filtering_no_valid_platforms(self):
        """Test when no valid platforms are available"""
        available_platforms = ['youtube', 'reddit']
        requested_platforms = ['twitter', 'facebook']
        
        valid_platforms = [p for p in requested_platforms if p in available_platforms]
        
        assert valid_platforms == []
        
    def test_platform_filtering_all_valid(self):
        """Test when all requested platforms are valid"""
        available_platforms = ['twitter', 'youtube', 'reddit']
        requested_platforms = ['twitter', 'youtube', 'reddit']
        
        valid_platforms = [p for p in requested_platforms if p in available_platforms]
        
        assert valid_platforms == ['twitter', 'youtube', 'reddit']
        
    def test_platform_filtering_empty_request(self):
        """Test when no platforms are requested (should use all available)"""
        available_platforms = ['youtube', 'reddit']
        requested_platforms = []
        
        # Logic: if no platforms requested, use all available
        valid_platforms = requested_platforms or available_platforms
        
        assert valid_platforms == ['youtube', 'reddit']


class TestDataCollectorUnit:
    """Unit tests for data collector platform availability"""
    
    @patch('services.data_collector.settings')
    def test_get_available_platforms_with_credentials(self, mock_settings):
        """Test platform availability based on credential presence"""
        # Mock settings with some credentials available
        mock_settings.TWITTER_BEARER_TOKEN = None  # Twitter unavailable
        mock_settings.YOUTUBE_API_KEY = 'test_key'  # YouTube available
        mock_settings.REDDIT_CLIENT_ID = 'test_id'  # Reddit available
        mock_settings.REDDIT_CLIENT_SECRET = 'test_secret'
        
        collector = SocialMediaCollector()
        platforms = collector.get_available_platforms()
        
        # Should include platforms with credentials
        assert 'youtube' in platforms
        assert 'reddit' in platforms
        # Should not include platforms without credentials
        assert 'twitter' not in platforms
        
    @patch('services.data_collector.settings')
    def test_get_available_platforms_no_credentials(self, mock_settings):
        """Test when no credentials are available"""
        # Mock settings with no credentials
        mock_settings.TWITTER_BEARER_TOKEN = None
        mock_settings.YOUTUBE_API_KEY = None
        mock_settings.REDDIT_CLIENT_ID = None
        mock_settings.REDDIT_CLIENT_SECRET = None
        
        collector = SocialMediaCollector()
        platforms = collector.get_available_platforms()
        
        # Should return empty list or handle gracefully
        assert isinstance(platforms, list)


class TestAnalysisRequestValidation:
    """Unit tests for analysis request validation"""
    
    def test_analysis_request_valid(self):
        """Test valid analysis request"""
        request = AnalysisRequest(
            keywords=["test", "example"],
            platforms=["youtube", "reddit"],
            max_posts_per_platform=50
        )
        
        assert request.keywords == ["test", "example"]
        assert request.platforms == ["youtube", "reddit"]
        assert request.max_posts_per_platform == 50
        
    def test_analysis_request_defaults(self):
        """Test analysis request with default values"""
        request = AnalysisRequest(keywords=["test"])
        
        assert request.keywords == ["test"]
        assert request.platforms == ["twitter", "youtube", "reddit"]  # default
        assert request.max_posts_per_platform == 100  # default
        
    def test_analysis_request_empty_keywords(self):
        """Test analysis request with empty keywords"""
        # Empty keywords should be allowed, validation happens at API level
        request = AnalysisRequest(keywords=[])
        assert request.keywords == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
