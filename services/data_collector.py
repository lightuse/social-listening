import asyncio
import httpx
import tweepy
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class TwitterCollector:
    """Twitter data collector using API v2"""
    
    def __init__(self):
        self.client = None
        self.api = None
        
    async def initialize(self):
        """Initialize Twitter API clients"""
        try:
            # Check if Bearer Token is available
            if not settings.TWITTER_BEARER_TOKEN:
                raise ValueError("TWITTER_BEARER_TOKEN is required")
            
            # Twitter API v2 client
            self.client = tweepy.Client(
                bearer_token=settings.TWITTER_BEARER_TOKEN,
                consumer_key=settings.TWITTER_API_KEY if settings.TWITTER_API_KEY else None,
                consumer_secret=settings.TWITTER_API_SECRET if settings.TWITTER_API_SECRET else None,
                access_token=settings.TWITTER_ACCESS_TOKEN if settings.TWITTER_ACCESS_TOKEN else None,
                access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET if settings.TWITTER_ACCESS_TOKEN_SECRET else None,
                wait_on_rate_limit=True
            )
            
            logger.info("Twitter API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            raise

    async def collect_tweets(
        self, 
        keywords: List[str], 
        max_results: int = 100,
        start_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Collect tweets based on keywords"""
        
        if not self.client:
            await self.initialize()
        
        tweets = []
        query = " OR ".join([f'"{keyword}"' for keyword in keywords])
        
        # Add language filter for Japanese
        query += " lang:ja"
        
        try:
            # Use start_time if provided, otherwise last 7 days
            if not start_time:
                start_time = datetime.utcnow() - timedelta(days=7)
            
            # Search tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),  # API limit
                start_time=start_time,
                tweet_fields=['public_metrics', 'created_at', 'author_id', 'context_annotations'],
                expansions=['author_id'],
                user_fields=['public_metrics', 'username', 'name']
            )
            
            if not response.data:
                logger.info("No tweets found for the given keywords")
                return tweets
            
            # Process tweets
            users = {user.id: user for user in response.includes.get('users', [])}
            
            for tweet in response.data:
                author = users.get(tweet.author_id)
                
                tweet_data = {
                    'external_id': str(tweet.id),
                    'platform': 'twitter',
                    'content': tweet.text,
                    'author': author.username if author else 'unknown',
                    'author_followers': author.public_metrics['followers_count'] if author else 0,
                    'url': f"https://twitter.com/{author.username}/status/{tweet.id}" if author else '',
                    'posted_at': tweet.created_at,
                    'collected_at': datetime.utcnow(),
                    'likes': tweet.public_metrics.get('like_count', 0),
                    'shares': tweet.public_metrics.get('retweet_count', 0),
                    'comments': tweet.public_metrics.get('reply_count', 0),
                    'hashtags': self._extract_hashtags(tweet.text),
                    'mentions': self._extract_mentions(tweet.text),
                    'media_urls': []
                }
                
                tweets.append(tweet_data)
                
            logger.info(f"Collected {len(tweets)} tweets for keywords: {keywords}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error collecting tweets: {e}")
            return []

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from tweet text"""
        import re
        hashtags = re.findall(r'#(\w+)', text)
        return hashtags

    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from tweet text"""
        import re
        mentions = re.findall(r'@(\w+)', text)
        return mentions


class YouTubeCollector:
    """YouTube data collector"""
    
    def __init__(self):
        if not settings.YOUTUBE_API_KEY:
            logger.warning("YOUTUBE_API_KEY is not set. YouTube data collection will be disabled.")
        self.api_key = settings.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def collect_comments(
        self, 
        keywords: List[str], 
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Collect YouTube comments based on keywords"""
        
        if not self.api_key:
            logger.warning("YouTube API key not available. Skipping YouTube data collection.")
            return []
        
        comments = []
        
        try:
            # First, search for videos
            video_ids = await self._search_videos(keywords, max_results=10)
            
            if not video_ids:
                logger.info("No videos found for the given keywords")
                return comments
            
            # Collect comments from videos
            async with httpx.AsyncClient() as client:
                for video_id in video_ids:
                    video_comments = await self._get_video_comments(client, video_id, max_results//len(video_ids))
                    comments.extend(video_comments)
                    
                    # Rate limiting
                    await asyncio.sleep(settings.RATE_LIMIT_DELAY)
            
            logger.info(f"Collected {len(comments)} YouTube comments")
            return comments
            
        except Exception as e:
            logger.error(f"Error collecting YouTube comments: {e}")
            return []

    async def _search_videos(self, keywords: List[str], max_results: int = 10) -> List[str]:
        """Search for YouTube videos"""
        query = " ".join(keywords)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                params={
                    'key': self.api_key,
                    'q': query,
                    'part': 'id',
                    'type': 'video',
                    'maxResults': max_results,
                    'order': 'relevance'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return [item['id']['videoId'] for item in data.get('items', [])]
            
            return []

    async def _get_video_comments(
        self, 
        client: httpx.AsyncClient, 
        video_id: str, 
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get comments for a specific video"""
        
        comments = []
        
        try:
            response = await client.get(
                f"{self.base_url}/commentThreads",
                params={
                    'key': self.api_key,
                    'videoId': video_id,
                    'part': 'snippet',
                    'maxResults': max_results,
                    'order': 'time'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    
                    comment_data = {
                        'external_id': item['id'],
                        'platform': 'youtube',
                        'content': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'author_followers': 0,  # Not available in API
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'posted_at': datetime.fromisoformat(comment['publishedAt'].replace('Z', '+00:00')),
                        'collected_at': datetime.utcnow(),
                        'likes': comment.get('likeCount', 0),
                        'shares': 0,
                        'comments': 0,
                        'hashtags': [],
                        'mentions': [],
                        'media_urls': []
                    }
                    
                    comments.append(comment_data)
            
        except Exception as e:
            logger.error(f"Error getting comments for video {video_id}: {e}")
        
        return comments


class RedditCollector:
    """Reddit data collector"""
    
    def __init__(self):
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            logger.warning("Reddit API credentials not set. Reddit data collection will be disabled.")
        self.client_id = settings.REDDIT_CLIENT_ID
        self.client_secret = settings.REDDIT_CLIENT_SECRET
        self.user_agent = "SocialListening/1.0"
        self.access_token = None

    async def initialize(self):
        """Initialize Reddit API access"""
        if not self.client_id or not self.client_secret:
            raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are required")
            
        try:
            async with httpx.AsyncClient() as client:
                auth_data = {
                    'grant_type': 'client_credentials'
                }
                
                response = await client.post(
                    'https://www.reddit.com/api/v1/access_token',
                    data=auth_data,
                    auth=(self.client_id, self.client_secret),
                    headers={'User-Agent': self.user_agent}
                )
                
                if response.status_code == 200:
                    self.access_token = response.json()['access_token']
                    logger.info("Reddit API initialized")
                else:
                    raise Exception(f"Reddit auth failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise

    async def collect_posts(
        self, 
        keywords: List[str], 
        subreddits: List[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Collect Reddit posts based on keywords"""
        
        if not self.access_token:
            await self.initialize()
        
        posts = []
        
        # Default subreddits if none provided
        if not subreddits:
            subreddits = ['all']
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'User-Agent': self.user_agent
                }
                
                for subreddit in subreddits:
                    for keyword in keywords:
                        subreddit_posts = await self._search_subreddit(
                            client, headers, subreddit, keyword, max_results//len(subreddits)//len(keywords)
                        )
                        posts.extend(subreddit_posts)
                        
                        # Rate limiting
                        await asyncio.sleep(settings.RATE_LIMIT_DELAY)
            
            logger.info(f"Collected {len(posts)} Reddit posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error collecting Reddit posts: {e}")
            return []

    async def _search_subreddit(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        subreddit: str,
        keyword: str,
        max_results: int = 25
    ) -> List[Dict[str, Any]]:
        """Search for posts in a specific subreddit"""
        
        posts = []
        
        try:
            response = await client.get(
                f'https://oauth.reddit.com/r/{subreddit}/search',
                params={
                    'q': keyword,
                    'sort': 'new',
                    'limit': max_results,
                    'restrict_sr': 'true'
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get('data', {}).get('children', []):
                    post = item['data']
                    
                    post_data = {
                        'external_id': post['id'],
                        'platform': 'reddit',
                        'content': post['title'] + '\n' + post.get('selftext', ''),
                        'author': post['author'],
                        'author_followers': 0,
                        'url': f"https://reddit.com{post['permalink']}",
                        'posted_at': datetime.fromtimestamp(post['created_utc']),
                        'collected_at': datetime.utcnow(),
                        'likes': post.get('ups', 0),
                        'shares': 0,
                        'comments': post.get('num_comments', 0),
                        'hashtags': [],
                        'mentions': [],
                        'media_urls': []
                    }
                    
                    posts.append(post_data)
                    
        except Exception as e:
            logger.error(f"Error searching subreddit {subreddit}: {e}")
        
        return posts


class SocialMediaCollector:
    """Main social media data collector"""
    
    def __init__(self):
        self.twitter = TwitterCollector()
        self.youtube = YouTubeCollector()
        self.reddit = RedditCollector()

    def get_available_platforms(self) -> List[str]:
        """Get list of platforms with valid API configurations"""
        available = []
        
        # Check Twitter
        if settings.TWITTER_BEARER_TOKEN:
            available.append('twitter')
        
        # Check YouTube
        if settings.YOUTUBE_API_KEY:
            available.append('youtube')
        
        # Check Reddit
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            available.append('reddit')
        
        return available

    async def collect_all_platforms(
        self, 
        keywords: List[str], 
        platforms: List[str] = None,
        max_results_per_platform: int = 100
    ) -> List[Dict[str, Any]]:
        """Collect data from all enabled platforms"""
        
        # Filter platforms to only include available ones
        available_platforms = self.get_available_platforms()
        
        if not platforms:
            platforms = available_platforms
        else:
            # Only use platforms that are both requested and available
            platforms = [p for p in platforms if p in available_platforms]
        
        if not platforms:
            logger.warning("No platforms available for data collection. Please check API configurations.")
            return []
        
        logger.info(f"Collecting data from platforms: {platforms}")
        all_posts = []
        
        # Collect from Twitter
        if 'twitter' in platforms:
            try:
                tweets = await self.twitter.collect_tweets(keywords, max_results_per_platform)
                all_posts.extend(tweets)
            except Exception as e:
                logger.error(f"Twitter collection failed: {e}")
        
        # Collect from YouTube
        if 'youtube' in platforms:
            try:
                youtube_comments = await self.youtube.collect_comments(keywords, max_results_per_platform)
                all_posts.extend(youtube_comments)
            except Exception as e:
                logger.error(f"YouTube collection failed: {e}")
        
        # Collect from Reddit
        if 'reddit' in platforms:
            try:
                reddit_posts = await self.reddit.collect_posts(keywords, max_results=max_results_per_platform)
                all_posts.extend(reddit_posts)
            except Exception as e:
                logger.error(f"Reddit collection failed: {e}")
        
        logger.info(f"Total collected posts: {len(all_posts)} from platforms: {platforms}")
        return all_posts
