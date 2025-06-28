"""
Simple API Settings Check
"""

import sys
import os

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.config import settings
    print("✅ 設定モジュールの読み込み成功")
    
    # API設定の確認
    print("\n=== API設定確認 ===")
    
    # Twitter
    print("\nTwitter:")
    print(f"  BEARER_TOKEN: {'✓ 設定済み' if settings.TWITTER_BEARER_TOKEN else '❌ 未設定'}")
    print(f"  API_KEY: {'✓ 設定済み' if settings.TWITTER_API_KEY else '❌ 未設定'}")
    print(f"  API_SECRET: {'✓ 設定済み' if settings.TWITTER_API_SECRET else '❌ 未設定'}")
    
    # YouTube
    print("\nYouTube:")
    print(f"  API_KEY: {'✓ 設定済み' if settings.YOUTUBE_API_KEY else '❌ 未設定'}")
    
    # Reddit
    print("\nReddit:")
    print(f"  CLIENT_ID: {'✓ 設定済み' if settings.REDDIT_CLIENT_ID else '❌ 未設定'}")
    print(f"  CLIENT_SECRET: {'✓ 設定済み' if settings.REDDIT_CLIENT_SECRET else '❌ 未設定'}")
    
    # データベース
    print(f"\nDatabase URL: {settings.DATABASE_URL}")
    
    print("\n✅ 設定確認完了")
    
except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback
    traceback.print_exc()
