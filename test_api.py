"""
APIエンドポイントのテストスクリプト
"""
import sqlite3
import json
from datetime import datetime, timedelta
import os

def test_database():
    """データベースの内容を確認"""
    db_path = "data/social_listening.db"
    
    if not os.path.exists(db_path):
        print(f"❌ データベースファイルが見つかりません: {db_path}")
        return False
    
    print(f"✅ データベースファイル: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル一覧を確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 テーブル一覧: {[t[0] for t in tables]}")
        
        # social_postsテーブルの構造確認
        cursor.execute("PRAGMA table_info(social_posts)")
        columns = cursor.fetchall()
        print(f"🗃️ social_postsテーブルのカラム: {[c[1] for c in columns]}")
        
        # データ件数確認
        cursor.execute("SELECT COUNT(*) FROM social_posts")
        total_count = cursor.fetchone()[0]
        print(f"📊 総データ件数: {total_count}")
        
        # プラットフォーム別件数
        cursor.execute("SELECT platform, COUNT(*) FROM social_posts GROUP BY platform")
        platform_counts = cursor.fetchall()
        print(f"🌐 プラットフォーム別件数: {dict(platform_counts)}")
        
        # 感情別件数
        cursor.execute("SELECT sentiment, COUNT(*) FROM social_posts GROUP BY sentiment")
        sentiment_counts = cursor.fetchall()
        print(f"😊 感情別件数: {dict(sentiment_counts)}")
        
        # 最新データのサンプル
        cursor.execute("SELECT * FROM social_posts ORDER BY created_at DESC LIMIT 3")
        samples = cursor.fetchall()
        print(f"📝 最新データのサンプル:")
        for sample in samples:
            print(f"  ID: {sample[0]}, Platform: {sample[2]}, Sentiment: {sample[4]}, Created: {sample[8]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return False

def test_api_logic():
    """APIロジックを直接テスト"""
    try:
        db_path = "data/social_listening.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 日付範囲の計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"📅 日付範囲: {start_date} ～ {end_date}")
        
        # サマリークエリ
        summary_query = """
        SELECT 
            COUNT(*) as total_posts,
            COUNT(DISTINCT platform) as platforms_count,
            AVG(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) * 100 as positive_percentage,
            AVG(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) * 100 as negative_percentage,
            AVG(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) * 100 as neutral_percentage
        FROM social_posts 
        WHERE created_at >= ? AND created_at <= ?
        """
        
        params = [start_date.isoformat(), end_date.isoformat()]
        
        print(f"🔍 実行するクエリ: {summary_query}")
        print(f"📊 パラメータ: {params}")
        
        cursor.execute(summary_query, params)
        summary_data = cursor.fetchone()
        
        print(f"✅ クエリ結果: {summary_data}")
        
        if summary_data:
            report_summary = {
                "total_posts": summary_data[0] or 0,
                "platforms_monitored": summary_data[1] or 0,
                "sentiment_distribution": {
                    "positive": round(summary_data[2] or 0, 2),
                    "negative": round(summary_data[3] or 0, 2),
                    "neutral": round(summary_data[4] or 0, 2)
                }
            }
            print(f"📈 レポートサマリー: {json.dumps(report_summary, indent=2, ensure_ascii=False)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ APIロジックテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 API動作テスト開始")
    print("=" * 50)
    
    # データベーステスト
    print("\n1️⃣ データベース確認")
    db_ok = test_database()
    
    if db_ok:
        print("\n2️⃣ APIロジックテスト")
        api_ok = test_api_logic()
        
        if api_ok:
            print("\n✅ 全てのテストが成功しました！")
        else:
            print("\n❌ APIロジックテストに失敗しました")
    else:
        print("\n❌ データベーステストに失敗しました")
    
    print("=" * 50)
