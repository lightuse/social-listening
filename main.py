from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
import sqlite3
import os

from core.config import settings
from core.database import init_db
from api.routes import analysis
from api.routes import reports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Social Listening System")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Social Listening System")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered social media sentiment analysis and monitoring system using AWS Bedrock",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])


@app.get("/")
async def root():
    """Root endpoint - redirect to dashboard"""
    with open("static/dashboard.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/dashboard")
async def dashboard():
    """Dashboard endpoint"""
    with open("static/dashboard.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/reports")
async def comprehensive_reports():
    """Comprehensive reports page"""
    with open("static/comprehensive-report.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/faq")
async def faq_page():
    """FAQ page"""
    with open("static/faq.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer and ECS"""
    return {
        "status": "healthy", 
        "service": settings.APP_NAME,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/system/status")
async def system_status():
    """System status endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database": "connected",
        "ai_engine": "aws_bedrock",
        "supported_platforms": ["twitter", "youtube", "reddit"]
    }


@app.get("/api/v1/reports/comprehensive-report")
async def get_comprehensive_report(
    days: int = Query(7, description="過去何日間のデータを含めるか", ge=1, le=365),
    platform: Optional[str] = Query(None, description="特定のプラットフォーム")
):
    """包括的レポートを生成"""
    try:
        logger.info(f"Generating comprehensive report for {days} days, platform: {platform}")
        
        # プラットフォームの検証
        valid_platforms = ["twitter", "youtube", "reddit", "instagram", "facebook"]
        if platform and platform not in valid_platforms:
            logger.warning(f"Invalid platform provided: {platform}")
            platform = None  # 無効なプラットフォームは無視
        
        # データベース接続
        db_path = "data/social_listening.db"
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            # データベースファイルが存在しない場合、空のレポートを返す
            return {
                "generated_at": datetime.now().isoformat(),
                "period": {
                    "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "days": days
                },
                "filters": {
                    "platform": platform
                },
                "summary": {
                    "total_posts": 0,
                    "platforms_monitored": 0,
                    "sentiment_distribution": {
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0
                    }
                },
                "sentiment_analysis": {},
                "platform_breakdown": {},
                "trending_topics": [],
                "insights": [
                    {
                        "title": "データなし",
                        "description": "現在、分析対象のデータがありません。データを収集してから再度お試しください。",
                        "priority": "high"
                    }
                ]
            }
            
        # 日付範囲の計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # 基本的なレポートデータを生成
        report = {
            "generated_at": end_date.isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "filters": {
                "platform": platform
            },
            "summary": {
                "total_posts": 0,
                "platforms_monitored": 0,
                "sentiment_distribution": {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0
                }
            },
            "sentiment_analysis": {},
            "platform_breakdown": {},
            "trending_topics": [],
            "insights": []
        }
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # サマリー統計
        try:
            # まずテーブルの存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                logger.warning("Table 'posts' does not exist")
                report["insights"].append({
                    "title": "データベース設定",
                    "description": "postsテーブルが見つかりません。初期化が必要です。",
                    "priority": "high"
                })
                conn.close()
                return report
            
            # Check if the new table structure exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            posts_table_exists = cursor.fetchone() is not None
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sentiment_analyses'")
            sentiment_table_exists = cursor.fetchone() is not None
            
            # Use new table structure if available, fall back to old structure
            if posts_table_exists and sentiment_table_exists:
                # New table structure
                cursor.execute("""
                    SELECT COUNT(*) FROM posts p 
                    LEFT JOIN sentiment_analyses sa ON p.id = sa.post_id
                """)
                total_records = cursor.fetchone()[0]
                logger.info(f"Total records in posts (new structure): {total_records}")
                table_structure = "new"
            else:
                logger.warning("Required tables not found")
                report["insights"].append({
                    "title": "データベースエラー",
                    "description": "テーブル構造が見つかりません。データベースの初期化が必要です。",
                    "priority": "high"
                })
                conn.close()
                return report
            
            if total_records == 0:
                logger.warning("No records found in database")
                report["insights"].append({
                    "title": "データなし",
                    "description": "データベースにデータがありません。データ収集を開始してください。",
                    "priority": "high"
                })
                conn.close()
                return report
            
            # Build summary query based on table structure
            if table_structure == "new":
                summary_query = """
                SELECT 
                    COUNT(DISTINCT p.id) as total_posts,
                    COUNT(DISTINCT p.platform) as platforms_count,
                    SUM(CASE WHEN sa.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sa.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sa.sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                FROM posts p
                LEFT JOIN sentiment_analyses sa ON p.id = sa.post_id
                """
            else:
                summary_query = """
                SELECT 
                    COUNT(*) as total_posts,
                    COUNT(DISTINCT platform) as platforms_count,
                    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                FROM social_posts
                """
            
            params = []
            if platform:
                if table_structure == "new":
                    summary_query += " WHERE p.platform = ?"
                else:
                    summary_query += " WHERE platform = ?"
                params.append(platform)
            
            logger.info(f"Executing summary query: {summary_query}")
            logger.info(f"Query params: {params}")
                
            cursor.execute(summary_query, params)
            summary_data = cursor.fetchone()
            
            logger.info(f"Summary query result: {summary_data}")
            
            if summary_data and summary_data[0] > 0:
                total_posts = summary_data[0]
                positive_count = summary_data[2] or 0
                negative_count = summary_data[3] or 0
                neutral_count = summary_data[4] or 0
                
                report["summary"] = {
                    "total_posts": total_posts,
                    "platforms_monitored": summary_data[1] or 0,
                    "sentiment_distribution": {
                        "positive": round((positive_count / total_posts * 100), 2) if total_posts > 0 else 0,
                        "negative": round((negative_count / total_posts * 100), 2) if total_posts > 0 else 0,
                        "neutral": round((neutral_count / total_posts * 100), 2) if total_posts > 0 else 0
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in summary query: {e}")
            report["insights"].append({
                "title": "データ取得エラー",
                "description": f"サマリーデータの取得中にエラーが発生しました: {str(e)}",
                "priority": "high"
            })
        
        # 感情分析の詳細
        try:
            if table_structure == "new":
                sentiment_query = """
                SELECT 
                    sa.sentiment_label as sentiment,
                    COUNT(*) as count,
                    AVG(sa.confidence) as avg_confidence
                FROM posts p
                LEFT JOIN sentiment_analyses sa ON p.id = sa.post_id
                WHERE sa.sentiment_label IS NOT NULL
                """
            else:
                sentiment_query = """
                SELECT 
                    sentiment,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence
                FROM social_posts 
                WHERE sentiment IS NOT NULL
                """
            
            params = []
            if platform:
                if table_structure == "new":
                    sentiment_query += " AND p.platform = ?"
                else:
                    sentiment_query += " AND platform = ?"
                params.append(platform)
            
            if table_structure == "new":
                sentiment_query += " GROUP BY sa.sentiment_label"
            else:
                sentiment_query += " GROUP BY sentiment"
            
            cursor.execute(sentiment_query, params)
            sentiment_data = cursor.fetchall()
            
            sentiment_details = {}
            for row in sentiment_data:
                if row[0]:
                    sentiment_details[row[0]] = {
                        "count": row[1],
                        "average_confidence": round(row[2] or 0, 2)
                    }
            
            report["sentiment_analysis"] = sentiment_details
        except Exception as e:
            logger.error(f"Error in sentiment query: {e}")
        
        # プラットフォーム別分析
        try:
            if table_structure == "new":
                platform_query = """
                SELECT 
                    p.platform,
                    COUNT(DISTINCT p.id) as count,
                    AVG(CASE WHEN sa.sentiment_label = 'positive' THEN 1 ELSE 0 END) * 100 as positive_rate,
                    AVG(sa.confidence) as avg_confidence
                FROM posts p
                LEFT JOIN sentiment_analyses sa ON p.id = sa.post_id
                """
            else:
                platform_query = """
                SELECT 
                    platform,
                    COUNT(*) as count,
                    AVG(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) * 100 as positive_rate,
                    AVG(confidence_score) as avg_confidence
                FROM social_posts
                """
            
            params = []
            if platform:
                if table_structure == "new":
                    platform_query += " WHERE p.platform = ?"
                else:
                    platform_query += " WHERE platform = ?"
                params.append(platform)
            
            if table_structure == "new":
                platform_query += " GROUP BY p.platform"
            else:
                platform_query += " GROUP BY platform"
            
            cursor.execute(platform_query, params)
            platform_data = cursor.fetchall()
            
            platform_breakdown = {}
            for row in platform_data:
                if row[0]:
                    platform_breakdown[row[0]] = {
                        "posts_count": row[1],
                        "positive_rate": round(row[2] or 0, 2),
                        "average_confidence": round(row[3] or 0, 2)
                    }
            
            report["platform_breakdown"] = platform_breakdown
        except Exception as e:
            logger.error(f"Error in platform query: {e}")
        
        # 基本的なインサイト生成
        try:
            if report["summary"]["total_posts"] > 0:
                pos_rate = report["summary"]["sentiment_distribution"]["positive"]
                neg_rate = report["summary"]["sentiment_distribution"]["negative"]
                
                if pos_rate > 60:
                    report["insights"].append({
                        "title": "ポジティブな反応",
                        "description": f"全体の{pos_rate}%がポジティブな感情を示しており、良好な反応を得ています。",
                        "priority": "low"
                    })
                elif neg_rate > 40:
                    report["insights"].append({
                        "title": "ネガティブな反応に注意",
                        "description": f"全体の{neg_rate}%がネガティブな感情を示しています。改善が必要かもしれません。",
                        "priority": "high"
                    })
                else:
                    report["insights"].append({
                        "title": "バランスの取れた反応",
                        "description": "感情分布がバランス良く分散しています。",
                        "priority": "medium"
                    })
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        conn.close()
        logger.info("Report generation completed successfully")
        return report
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}")
        # エラー時も基本的なレスポンスを返す
        return {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "days": days
            },
            "filters": {
                "platform": platform
            },
            "summary": {
                "total_posts": 0,
                "platforms_monitored": 0,
                "sentiment_distribution": {
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0
                }
            },
            "sentiment_analysis": {},
            "platform_breakdown": {},
            "trending_topics": [],
            "insights": [
                {
                    "title": "レポート生成エラー",
                    "description": f"レポートの生成中にエラーが発生しました: {str(e)}",
                    "priority": "high"
                }
            ]
        }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
