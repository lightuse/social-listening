"""
Social Media API接続テストスクリプト（簡易版）
TwitterのレートリミットをスキップしてYouTubeとRedditのみテスト
"""

import asyncio
import sys
import os
from datetime import datetime
import logging
import pytest

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from services.data_collector import YouTubeCollector, RedditCollector

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_youtube_api():
    """YouTube API接続テスト"""
    print("\n=== YouTube API 接続テスト ===")
    
    # 設定確認
    if not settings.YOUTUBE_API_KEY:
        print("❌ YOUTUBE_API_KEY が設定されていません")
        return False
    
    print(f"✓ API Key: {'*' * 10}...{settings.YOUTUBE_API_KEY[-4:] if len(settings.YOUTUBE_API_KEY) > 4 else 'N/A'}")
    
    try:
        collector = YouTubeCollector()
        
        # テスト用キーワードで検索
        test_keywords = ["Python プログラミング"]
        print(f"テストキーワード: {test_keywords}")
        
        comments = await collector.collect_comments(test_keywords, max_results=5)
        
        if comments:
            print(f"✅ YouTube API 接続成功: {len(comments)}件のコメントを取得")
            for i, comment in enumerate(comments[:2]):
                print(f"  {i+1}. {comment['author']}: {comment['content'][:100]}...")
            return True
        else:
            print("⚠️  YouTube API接続は成功しましたが、データが取得できませんでした")
            return True
            
    except Exception as e:
        print(f"❌ YouTube API 接続エラー: {e}")
        return False


@pytest.mark.asyncio
async def test_reddit_api():
    """Reddit API接続テスト"""
    print("\n=== Reddit API 接続テスト ===")
    
    # 設定確認
    if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
        print("❌ REDDIT_CLIENT_ID または REDDIT_CLIENT_SECRET が設定されていません")
        return False
    
    print(f"✓ Client ID: {'*' * 10}...{settings.REDDIT_CLIENT_ID[-4:] if len(settings.REDDIT_CLIENT_ID) > 4 else 'N/A'}")
    print(f"✓ Client Secret: {'*' * 10}...{settings.REDDIT_CLIENT_SECRET[-4:] if len(settings.REDDIT_CLIENT_SECRET) > 4 else 'N/A'}")
    
    try:
        collector = RedditCollector()
        await collector.initialize()
        
        # テスト用キーワードで検索
        test_keywords = ["Python"]
        test_subreddits = ["Python", "programming"]
        print(f"テストキーワード: {test_keywords}")
        print(f"テストサブレディット: {test_subreddits}")
        
        posts = await collector.collect_posts(test_keywords, subreddits=test_subreddits, max_results=5)
        
        if posts:
            print(f"✅ Reddit API 接続成功: {len(posts)}件の投稿を取得")
            for i, post in enumerate(posts[:2]):
                print(f"  {i+1}. u/{post['author']}: {post['content'][:100]}...")
            return True
        else:
            print("⚠️  Reddit API接続は成功しましたが、データが取得できませんでした")
            return True
            
    except Exception as e:
        print(f"❌ Reddit API 接続エラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("🔍 Social Media API 接続テスト開始（簡易版 - TwitterのレートリミットをスキップDue to rate limit）")
    print(f"テスト実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 各API接続テスト
    results = {}
    
    print("\n" + "="*50)
    print("API接続テスト実行中...")
    
    # Twitter は スキップ（レートリミットのため）
    print("\n=== Twitter API 接続テスト ===")
    print("⏭️  Twitter APIテストをスキップ（レートリミットのため）")
    results['twitter'] = None  # スキップを示すためにNone
    
    # YouTube
    results['youtube'] = await test_youtube_api()
    
    # Reddit
    results['reddit'] = await test_reddit_api()
    
    # 結果サマリー
    print("\n" + "="*50)
    print("=== テスト結果サマリー ===")
    
    success_count = sum(1 for result in results.values() if result is True)
    skipped_count = sum(1 for result in results.values() if result is None)
    failed_count = sum(1 for result in results.values() if result is False)
    total_count = len(results)
    
    for platform, success in results.items():
        if success is True:
            status = "✅ 成功"
        elif success is None:
            status = "⏭️  スキップ"
        else:
            status = "❌ 失敗"
        print(f"{platform.capitalize()}: {status}")
    
    print(f"\n成功: {success_count}/{total_count} プラットフォーム")
    print(f"スキップ: {skipped_count}/{total_count} プラットフォーム")
    print(f"失敗: {failed_count}/{total_count} プラットフォーム")
    
    if success_count + skipped_count == total_count:
        print("🎉 テストしたAPIは正常に動作しています！")
    elif success_count > 0:
        print("⚠️  一部のAPIで問題があります。設定を確認してください。")
    else:
        print("❌ テストしたすべてのAPI接続に問題があります。設定を確認してください。")
    
    # 推奨事項
    print("\n=== 推奨事項 ===")
    
    if results.get('twitter') is None:
        print("• Twitter: レートリミットのためテストをスキップしました。しばらく時間をおいてから再テストしてください")
    
    if not results.get('youtube'):
        print("• YouTube: Google Cloud ConsoleでYouTube Data API v3が有効になっているか確認してください")
        print("  - https://console.cloud.google.com/")
    
    if not results.get('reddit'):
        print("• Reddit: アプリケーションがScript typeで作成されているか確認してください")
        print("  - https://www.reddit.com/prefs/apps")
    
    print("\n詳細な設定手順: README.md を参照")


if __name__ == "__main__":
    asyncio.run(main())
