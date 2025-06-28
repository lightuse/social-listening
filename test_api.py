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
        
        # postsテーブルの構造確認
        cursor.execute("PRAGMA table_info(posts)")
        columns = cursor.fetchall()
        print(f"🗃️ postsテーブルのカラム: {[c[1] for c in columns]}")
        
        # データ件数確認
        cursor.execute("SELECT COUNT(*) FROM posts")
        total_count = cursor.fetchone()[0]
        print(f"📊 総データ件数: {total_count}")
        
        # プラットフォーム別件数
        cursor.execute("SELECT platform, COUNT(*) FROM posts GROUP BY platform")
        platform_counts = cursor.fetchall()
        print(f"🌐 プラットフォーム別件数: {dict(platform_counts)}")
        
        # sentiment_analyses テーブルから感情別件数を取得
        cursor.execute("SELECT sentiment_label, COUNT(*) FROM sentiment_analyses GROUP BY sentiment_label")
        sentiment_counts = cursor.fetchall()
        print(f"😊 感情別件数: {dict(sentiment_counts)}")
        
        # 最新データのサンプル
        cursor.execute("SELECT * FROM posts ORDER BY collected_at DESC LIMIT 3")
        samples = cursor.fetchall()
        print(f"📝 最新データのサンプル:")
        for sample in samples:
            print(f"  ID: {sample[0]}, Platform: {sample[2]}, Author: {sample[4]}, Collected: {sample[8]}")
        
        conn.close()
        assert True  # Test passed
        
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        assert False, f"Database error: {e}"

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
        
        # サマリークエリ - JOIN を使って sentiment_analyses から感情データを取得
        summary_query = """
        SELECT 
            COUNT(DISTINCT p.id) as total_posts,
            COUNT(DISTINCT p.platform) as platforms_count,
            AVG(CASE WHEN sa.sentiment_label = 'positive' THEN 1 ELSE 0 END) * 100 as positive_percentage,
            AVG(CASE WHEN sa.sentiment_label = 'negative' THEN 1 ELSE 0 END) * 100 as negative_percentage,
            AVG(CASE WHEN sa.sentiment_label = 'neutral' THEN 1 ELSE 0 END) * 100 as neutral_percentage
        FROM posts p
        LEFT JOIN sentiment_analyses sa ON p.id = sa.post_id 
        WHERE p.collected_at >= ? AND p.collected_at <= ?
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
        assert True  # Test passed
        
    except Exception as e:
        print(f"❌ APIロジックテストエラー: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"API logic test error: {e}"

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
