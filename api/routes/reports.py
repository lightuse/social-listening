from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import sqlite3
import json
import logging
import random
from pathlib import Path

from core.database import get_db
from models.database import Post, Keyword, SentimentAnalysis
from services.bedrock_engine import BedrockSentimentEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# データベースパス
DB_PATH = "data/social_listening.db"

@router.get("/comprehensive-report")
async def get_comprehensive_report(
    days: Optional[int] = Query(7, description="過去何日間のデータを含めるか", ge=1, le=365),
    platform: Optional[str] = Query(None, description="特定のプラットフォーム (twitter, youtube, reddit)"),
    keyword: Optional[str] = Query(None, description="特定のキーワードでフィルタ"),
    db: Session = Depends(get_db)
):
    """包括的レポートを生成"""
    try:
        logger.info(f"Generating comprehensive report for {days} days, platform: {platform}, keyword: {keyword}")
        
        # プラットフォームの検証
        valid_platforms = ["twitter", "youtube", "reddit", "instagram", "facebook"]
        if platform and platform not in valid_platforms:
            logger.warning(f"Invalid platform provided: {platform}")
            platform = None  # 無効なプラットフォームは無視
        
        # 日付範囲の計算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 基本クエリを作成
        query = db.query(Post).filter(
            Post.collected_at >= start_date,
            Post.collected_at <= end_date
        )
        
        # フィルタを適用
        if platform:
            query = query.filter(Post.platform == platform)
        
        if keyword:
            # キーワードでフィルタ（コンテンツまたはハッシュタグに含まれる）
            query = query.filter(
                Post.content.contains(keyword)
            )
        
        posts = query.all()        # レポートの基本構造を作成
        logger.info("Creating report structure...")
        
        try:
            summary = _generate_summary(posts)
            logger.info("Summary generated successfully")
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            summary = {}
        try:
            sentiment_analysis = _analyze_sentiment_trends(posts, db)
            logger.info("Sentiment analysis completed")
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            sentiment_analysis = {}
            
        try:
            platform_breakdown = _analyze_platforms(posts)
            logger.info(f"Platform breakdown completed: {platform_breakdown}")
        except Exception as e:
            logger.error(f"Error in platform analysis: {e}")
            platform_breakdown = {}
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "filters": {
                "platform": platform,
                "keyword": keyword
            },
            "summary": summary,
            "sentiment_analysis": sentiment_analysis,
            "platform_breakdown": platform_breakdown,
            "platform_data": platform_breakdown,  # フロントエンド互換性（同じデータを使用）
            "trending_topics": _extract_trending_topics(posts),
            "engagement_metrics": _calculate_engagement_metrics(posts),
            "time_series": _generate_time_series(posts, days),
            "insights": []
        }
        # インサイトを生成
        report["insights"] = _generate_insights(report)
        
        logger.info(f"Report generated successfully with {len(posts)} posts")
        return report
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"レポート生成エラー: {str(e)}")
        
        # トレンドトピック（ハッシュタグ分析）
        trending_query = """
        SELECT 
            hashtags,
            COUNT(*) as frequency,
            AVG(CASE WHEN sa.sentiment_label = 'positive' THEN 1 ELSE 0 END) * 100 as positive_rate
        FROM posts p
        LEFT JOIN sentiment_analyses sa ON p.id = sa.post_id
        WHERE p.collected_at >= ? AND p.collected_at <= ? AND p.hashtags IS NOT NULL
        """
        
        params = [start_date.isoformat(), end_date.isoformat()]
        if platform:
            trending_query += " AND p.platform = ?"
            params.append(platform)
        trending_query += " GROUP BY p.hashtags ORDER BY frequency DESC LIMIT 10"
        
        cursor.execute(trending_query, params)
        trending_data = cursor.fetchall()
        
        trending_topics = []
        for row in trending_data:
            if row[0]:  # ハッシュタグが存在する場合
                trending_topics.append({
                    "hashtags": row[0],
                    "frequency": row[1],
                    "positive_rate": round(row[2] or 0, 2)
                })
        
        report["trending_topics"] = trending_topics
        
        # インサイト生成
        insights = []
        
        # 感情分析インサイト
        if report["summary"]["total_posts"] > 0:
            sentiment_dist = report["summary"]["sentiment_distribution"]
            dominant_sentiment = max(sentiment_dist, key=sentiment_dist.get)
            insights.append({
                "type": "sentiment",
                "title": f"感情分析: {dominant_sentiment}が優勢",
                "description": f"過去{days}日間で{dominant_sentiment}な投稿が{sentiment_dist[dominant_sentiment]}%を占めています。",
                "priority": "high" if sentiment_dist[dominant_sentiment] > 60 else "medium"
            })
        
        # エンゲージメントインサイト
        if platform_breakdown:
            best_platform = max(platform_breakdown.items(), key=lambda x: x[1]["average_engagement"])
            insights.append({
                "type": "engagement",
                "title": f"最高エンゲージメント: {best_platform[0]}",
                "description": f"{best_platform[0]}で平均エンゲージメントスコア{best_platform[1]['average_engagement']}を記録",
                "priority": "medium"
            })
        
        # トレンドインサイト
        if trending_topics:
            top_trend = trending_topics[0]
            insights.append({
                "type": "trend",
                "title": f"トレンドハッシュタグ: {top_trend['hashtags']}",
                "description": f"'{top_trend['hashtags']}'が{top_trend['frequency']}回言及され、{top_trend['positive_rate']}%がポジティブ",
                "priority": "high"
            })
        
        report["insights"] = insights
        
        conn.close()
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レポート生成エラー: {str(e)}")

@router.get("/export-report")
async def export_report(
    format: str = Query("json", description="エクスポート形式 (json, csv)"),
    days: Optional[int] = Query(7, description="過去何日間のデータを含めるか"),
    platform: Optional[str] = Query(None, description="特定のプラットフォーム"),
    db: Session = Depends(get_db)
):
    """レポートをエクスポート"""
    try:
        # 包括的レポートを取得
        report_data = await get_comprehensive_report(days=days, platform=platform, db=db)
        
        if format.lower() == "csv":
            # CSV形式での出力
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # ヘッダー
            writer.writerow(["Category", "Metric", "Value"])
            
            # サマリーデータ
            summary = report_data.get("summary", {})
            sentiment_dist = summary.get("sentiment_distribution", {})
            
            writer.writerow(["Summary", "Total Posts", summary.get("total_posts", 0)])
            writer.writerow(["Summary", "Platforms Monitored", summary.get("platforms_monitored", 0)])
            writer.writerow(["Sentiment", "Positive %", sentiment_dist.get("positive", 0)])
            writer.writerow(["Sentiment", "Negative %", sentiment_dist.get("negative", 0)])
            writer.writerow(["Sentiment", "Neutral %", sentiment_dist.get("neutral", 0)])
            
            # プラットフォーム別データ
            platform_breakdown = report_data.get("platform_breakdown", {})
            for platform, data in platform_breakdown.items():
                writer.writerow(["Platform", f"{platform} - Posts", data.get("post_count", 0)])
                writer.writerow(["Platform", f"{platform} - Avg Engagement", data.get("average_engagement", 0)])
            
            return {"format": "csv", "data": output.getvalue()}
        
        return report_data
        
    except Exception as e:
        logger.error(f"Error exporting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"エクスポートエラー: {str(e)}")

@router.get("/detailed-analytics")
async def get_detailed_analytics(
    metric: str = Query("sentiment", description="分析メトリック (sentiment, engagement, keywords)"),
    days: Optional[int] = Query(7, description="過去何日間のデータを含めるか"),
    platform: Optional[str] = Query(None, description="特定のプラットフォーム"),
    db: Session = Depends(get_db)
):
    """詳細分析データを取得"""
    try:
        logger.info(f"Getting detailed analytics for metric: {metric}, days: {days}, platform: {platform}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 基本クエリ
        query = db.query(Post).filter(
            Post.collected_at >= start_date,
            Post.collected_at <= end_date
        )
        
        if platform:
            query = query.filter(Post.platform == platform)
        
        posts = query.all()
        
        if metric == "sentiment":
            # 時系列感情分析
            result_data = _analyze_sentiment_time_series(posts)
            
        elif metric == "engagement":
            # エンゲージメント分析
            result_data = _analyze_engagement_details(posts)
            
        else:  # keywords
            # キーワード/ハッシュタグ分析
            result_data = _analyze_keywords_details(posts)
        
        return {
            "metric": metric,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "filters": {
                "platform": platform
            },
            "data": result_data,
            "total_posts": len(posts)
        }
        
    except Exception as e:
        logger.error(f"Error in detailed analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"詳細分析エラー: {str(e)}")


def _analyze_sentiment_time_series(posts: List[Post]) -> List[Dict[str, Any]]:
    """感情分析の時系列データを生成"""
    from collections import defaultdict
    
    daily_sentiment = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0, "total": 0})
    
    for post in posts:
        if not post.collected_at or not post.analyses:
            continue
            
        date_key = post.collected_at.date().isoformat()
        latest_analysis = max(post.analyses, key=lambda x: x.analyzed_at)
        sentiment = latest_analysis.sentiment_label
        
        if sentiment in daily_sentiment[date_key]:
            daily_sentiment[date_key][sentiment] += 1
        daily_sentiment[date_key]["total"] += 1
    
    # パーセンテージを計算
    result = []
    for date, sentiments in sorted(daily_sentiment.items()):
        total = sentiments["total"]
        result.append({
            "date": date,
            "positive": round((sentiments["positive"] / total) * 100, 2) if total > 0 else 0,
            "negative": round((sentiments["negative"] / total) * 100, 2) if total > 0 else 0,
            "neutral": round((sentiments["neutral"] / total) * 100, 2) if total > 0 else 0,
            "total_posts": total
        })
    
    return result


def _analyze_engagement_details(posts: List[Post]) -> List[Dict[str, Any]]:
    """エンゲージメント詳細分析"""
    from collections import defaultdict
    
    platform_engagement = defaultdict(lambda: {
        "total_posts": 0,
        "total_likes": 0,
        "total_shares": 0,
        "total_comments": 0,
        "daily_breakdown": defaultdict(lambda: {"posts": 0, "engagement": 0})
    })
    
    for post in posts:
        platform = post.platform
        platform_engagement[platform]["total_posts"] += 1
        platform_engagement[platform]["total_likes"] += (post.likes or 0)
        platform_engagement[platform]["total_shares"] += (post.shares or 0)
        platform_engagement[platform]["total_comments"] += (post.comments or 0)
        
        if post.collected_at:
            date_key = post.collected_at.date().isoformat()
            platform_engagement[platform]["daily_breakdown"][date_key]["posts"] += 1
            engagement = (post.likes or 0) + (post.shares or 0) + (post.comments or 0)
            platform_engagement[platform]["daily_breakdown"][date_key]["engagement"] += engagement
    
    result = []
    for platform, data in platform_engagement.items():
        total_posts = data["total_posts"]
        total_engagement = data["total_likes"] + data["total_shares"] + data["total_comments"]
        
        result.append({
            "platform": platform,
            "total_posts": total_posts,
            "average_engagement": round(total_engagement / total_posts, 2) if total_posts > 0 else 0,
            "engagement_breakdown": {
                "likes": data["total_likes"],
                "shares": data["total_shares"],
                "comments": data["total_comments"]
            },
            "daily_data": [
                {
                    "date": date,
                    "posts": daily_data["posts"],
                    "average_engagement": round(daily_data["engagement"] / daily_data["posts"], 2) if daily_data["posts"] > 0 else 0
                }
                for date, daily_data in sorted(data["daily_breakdown"].items())
            ]
        })
    
    return result


def _analyze_keywords_details(posts: List[Post]) -> List[Dict[str, Any]]:
    """キーワード/ハッシュタグ詳細分析"""
    hashtag_analysis = {}
    
    for post in posts:
        if not post.hashtags:
            continue
            
        for hashtag in post.hashtags:
            if hashtag not in hashtag_analysis:
                hashtag_analysis[hashtag] = {
                    "frequency": 0,
                    "platforms": set(),
                    "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
                    "total_engagement": 0
                }
            
            hashtag_analysis[hashtag]["frequency"] += 1
            hashtag_analysis[hashtag]["platforms"].add(post.platform)
            
            # エンゲージメント
            engagement = (post.likes or 0) + (post.shares or 0) + (post.comments or 0)
            hashtag_analysis[hashtag]["total_engagement"] += engagement
            
            # 感情分析
            if post.analyses:
                latest_analysis = max(post.analyses, key=lambda x: x.analyzed_at)
                sentiment = latest_analysis.sentiment_label
                if sentiment in hashtag_analysis[hashtag]["sentiment_counts"]:
                    hashtag_analysis[hashtag]["sentiment_counts"][sentiment] += 1
    
    # 結果を整形
    result = []
    for hashtag, data in sorted(hashtag_analysis.items(), key=lambda x: x[1]["frequency"], reverse=True)[:20]:
        total_sentiment = sum(data["sentiment_counts"].values())
        
        result.append({
            "keyword": hashtag,
            "frequency": data["frequency"],
            "platforms": list(data["platforms"]),
            "average_engagement": round(data["total_engagement"] / data["frequency"], 2) if data["frequency"] > 0 else 0,
            "sentiment_distribution": {
                sentiment: round((count / total_sentiment) * 100, 2) if total_sentiment > 0 else 0
                for sentiment, count in data["sentiment_counts"].items()
            },
            "dominant_sentiment": max(data["sentiment_counts"].keys(), key=lambda k: data["sentiment_counts"][k]) if data["sentiment_counts"] else "neutral"
        })
    
    return result

def _generate_summary(posts: List[Post]) -> Dict[str, Any]:
    """投稿データからサマリーを生成"""
    if not posts:
        return {
            "total_posts": 0,
            "platforms_monitored": 0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "date_range": {"earliest": None, "latest": None}
        }
    
    # 感情分析結果を取得
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    platforms = set()
    dates = []
    
    for post in posts:
        platforms.add(post.platform)
        if post.collected_at:
            dates.append(post.collected_at)
        
        # 感情分析結果を取得（最新の分析結果を使用）
        if post.analyses:
            latest_analysis = max(post.analyses, key=lambda x: x.analyzed_at)
            sentiment = latest_analysis.sentiment_label
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
    
    total = len(posts)
    sentiment_percentages = {
        sentiment: round((count / total) * 100, 2) if total > 0 else 0
        for sentiment, count in sentiment_counts.items()
    }
    
    return {
        "total_posts": total,
        "platforms_monitored": len(platforms),
        "sentiment_distribution": sentiment_percentages,
        "date_range": {
            "earliest": min(dates).isoformat() if dates else None,
            "latest": max(dates).isoformat() if dates else None
        },
        "platforms": list(platforms)
    }


def _analyze_sentiment_trends(posts: List[Post], db: Session) -> Dict[str, Any]:
    """感情分析のトレンドを分析"""
    sentiment_data = {}
    daily_trends = {}
    
    for post in posts:
        if not post.analyses:
            continue
            
        latest_analysis = max(post.analyses, key=lambda x: x.analyzed_at)
        sentiment = latest_analysis.sentiment_label
        confidence = latest_analysis.confidence
        
        # 全体の感情データ
        if sentiment not in sentiment_data:
            sentiment_data[sentiment] = {
                "count": 0,
                "total_confidence": 0,
                "average_confidence": 0
            }
        
        sentiment_data[sentiment]["count"] += 1
        sentiment_data[sentiment]["total_confidence"] += (confidence or 0)
    
    # 平均信頼度を計算
    for sentiment, data in sentiment_data.items():
        if data["count"] > 0:
            data["average_confidence"] = round(data["total_confidence"] / data["count"], 2)
    
    return {
        "overall_sentiment": sentiment_data,
        "daily_trends": daily_trends,
        "dominant_sentiment": max(sentiment_data.keys(), key=lambda k: sentiment_data[k]["count"]) if sentiment_data else "neutral"
    }


def _analyze_platforms(posts: List[Post]) -> Dict[str, Any]:
    """プラットフォーム別の分析"""
    logger.info(f"Analyzing {len(posts)} posts for platform breakdown")
    if not posts:
        logger.warning("No posts provided to _analyze_platforms")
        return {}
    
    platform_data = {}
    for i, post in enumerate(posts):
        platform = post.platform
        logger.debug(f"Processing post {i+1}/{len(posts)} from platform: {platform}")
        
        if platform not in platform_data:
            logger.info(f"Adding new platform: {platform}")
            platform_data[platform] = {
                "post_count": 0,
                "total_engagement": 0,
                "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0}
            }
        
        platform_data[platform]["post_count"] += 1
        
        # エンゲージメント計算
        engagement = (post.likes or 0) + (post.shares or 0) + (post.comments or 0)
        platform_data[platform]["total_engagement"] += engagement
        # 感情分析
        if post.analyses:
            latest_analysis = max(post.analyses, key=lambda x: x.analyzed_at)
            sentiment = latest_analysis.sentiment_label
            if sentiment in platform_data[platform]["sentiment_counts"]:
                platform_data[platform]["sentiment_counts"][sentiment] += 1

    # 平均値を計算
    for platform, data in platform_data.items():
        count = data["post_count"]
        data["posts_count"] = data["post_count"]  # フロントエンド互換性
        data["average_engagement"] = round(data["total_engagement"] / count, 2) if count > 0 else 0
        # 感情分析の割合を計算
        total_analyzed = sum(data["sentiment_counts"].values())
        data["sentiment_percentages"] = {
            sentiment: round((count / total_analyzed) * 100, 2) if total_analyzed > 0 else 0
            for sentiment, count in data["sentiment_counts"].items()
        }
        data["positive_rate"] = data["sentiment_percentages"]["positive"]  # フロントエンド互換性
    
    logger.info(f"Platform analysis completed: {list(platform_data.keys())}")
    return platform_data


def _extract_trending_topics(posts: List[Post]) -> List[Dict[str, Any]]:
    """トレンドトピックを抽出"""
    hashtag_counts = {}
    keyword_sentiment = {}
    
    for post in posts:
        # ハッシュタグの処理
        if post.hashtags:
            for hashtag in post.hashtags:
                if hashtag not in hashtag_counts:
                    hashtag_counts[hashtag] = 0
                    keyword_sentiment[hashtag] = {"positive": 0, "negative": 0, "neutral": 0}
                
                hashtag_counts[hashtag] += 1
                
                # 感情分析
                if post.analyses:
                    latest_analysis = max(post.analyses, key=lambda x: x.analyzed_at)
                    sentiment = latest_analysis.sentiment_label
                    if sentiment in keyword_sentiment[hashtag]:
                        keyword_sentiment[hashtag][sentiment] += 1
    
    # 上位トピックを作成
    trending = []
    for hashtag, count in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        sentiment_data = keyword_sentiment[hashtag]
        total = sum(sentiment_data.values())
        
        trending.append({
            "topic": hashtag,
            "frequency": count,
            "sentiment_breakdown": {
                sentiment: round((cnt / total) * 100, 2) if total > 0 else 0
                for sentiment, cnt in sentiment_data.items()
            },
            "dominant_sentiment": max(sentiment_data.keys(), key=lambda k: sentiment_data[k]) if sentiment_data else "neutral"
        })
    
    return trending


def _calculate_engagement_metrics(posts: List[Post]) -> Dict[str, Any]:
    """エンゲージメント指標を計算"""
    if not posts:
        return {
            "total_engagement": 0,
            "average_engagement": 0,
            "engagement_breakdown": {"likes": 0, "shares": 0, "comments": 0}
        }
    
    total_likes = sum(post.likes or 0 for post in posts)
    total_shares = sum(post.shares or 0 for post in posts)
    total_comments = sum(post.comments or 0 for post in posts)
    total_engagement = total_likes + total_shares + total_comments
    
    return {
        "total_engagement": total_engagement,
        "average_engagement": round(total_engagement / len(posts), 2),
        "engagement_breakdown": {
            "likes": total_likes,
            "shares": total_shares,
            "comments": total_comments
        },
        "engagement_rate_by_platform": _calculate_platform_engagement_rates(posts)
    }


def _calculate_platform_engagement_rates(posts: List[Post]) -> Dict[str, float]:
    """プラットフォーム別エンゲージメント率を計算"""
    platform_engagement = {}
    
    for post in posts:
        platform = post.platform
        if platform not in platform_engagement:
            platform_engagement[platform] = {"total": 0, "count": 0}
        
        engagement = (post.likes or 0) + (post.shares or 0) + (post.comments or 0)
        platform_engagement[platform]["total"] += engagement
        platform_engagement[platform]["count"] += 1
    
    return {
        platform: round(data["total"] / data["count"], 2) if data["count"] > 0 else 0
        for platform, data in platform_engagement.items()
    }


def _generate_time_series(posts: List[Post], days: int) -> Dict[str, Any]:
    """時系列データを生成"""
    from collections import defaultdict
    
    daily_data = defaultdict(lambda: {
        "post_count": 0,
        "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
        "engagement": 0
    })
    
    for post in posts:
        if not post.collected_at:
            continue
            
        date_key = post.collected_at.date().isoformat()
        daily_data[date_key]["post_count"] += 1
        
        # エンゲージメント
        engagement = (post.likes or 0) + (post.shares or 0) + (post.comments or 0)
        daily_data[date_key]["engagement"] += engagement
        
        # 感情分析
        if post.analyses:
            latest_analysis = max(post.analyses, key=lambda x: x.analyzed_at)
            sentiment = latest_analysis.sentiment_label
            if sentiment in daily_data[date_key]["sentiment_counts"]:
                daily_data[date_key]["sentiment_counts"][sentiment] += 1
    
    # 日付順にソート
    sorted_data = dict(sorted(daily_data.items()))
    
    return {
        "daily_breakdown": sorted_data,
        "total_days_with_data": len(sorted_data),
        "average_posts_per_day": round(sum(d["post_count"] for d in sorted_data.values()) / len(sorted_data), 2) if sorted_data else 0
    }


def _generate_insights(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """レポートからインサイトを生成"""
    insights = []
    summary = report.get("summary", {})
    sentiment_analysis = report.get("sentiment_analysis", {})
    platform_breakdown = report.get("platform_breakdown", {})
    trending_topics = report.get("trending_topics", [])
    
    # 投稿量インサイト
    total_posts = summary.get("total_posts", 0)
    if total_posts > 0:
        insights.append({
            "type": "volume",
            "title": f"投稿量分析",
            "description": f"期間中に{total_posts}件の投稿を収集しました。",
            "priority": "medium",
            "value": total_posts
        })
    
    # 感情分析インサイト
    sentiment_dist = summary.get("sentiment_distribution", {})
    if sentiment_dist:
        dominant_sentiment = max(sentiment_dist.keys(), key=lambda k: sentiment_dist[k])
        percentage = sentiment_dist[dominant_sentiment]
        
        priority = "high" if percentage > 60 else "medium" if percentage > 40 else "low"
        insights.append({
            "type": "sentiment",
            "title": f"感情分析: {dominant_sentiment}が優勢",
            "description": f"{dominant_sentiment}な投稿が{percentage}%を占めています。",
            "priority": priority,
            "value": percentage
        })
    
    # プラットフォームインサイト
    if platform_breakdown:
        best_platform = max(platform_breakdown.items(), key=lambda x: x[1].get("average_engagement", 0))
        if best_platform[1].get("average_engagement", 0) > 0:
            insights.append({
                "type": "platform",
                "title": f"最高エンゲージメント: {best_platform[0]}",
                "description": f"{best_platform[0]}で平均エンゲージメント{best_platform[1]['average_engagement']}を記録",
                "priority": "medium",
                "value": best_platform[1]["average_engagement"]
            })
    
    # トレンドインサイト
    if trending_topics:
        top_trend = trending_topics[0]
        insights.append({
            "type": "trend",
            "title": f"トレンドトピック: {top_trend['topic']}",
            "description": f"'{top_trend['topic']}'が{top_trend['frequency']}回言及されました。",
            "priority": "high",
            "value": top_trend['frequency']
        })
    
    return insights

@router.post("/generate-sample-data")
async def generate_sample_data(
    count: int = Query(50, description="生成するサンプル投稿数", ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """デモ用のサンプルデータを生成"""
    try:
        logger.info(f"Generating {count} sample posts")
        
        import random
        from datetime import datetime, timedelta
        
        # デフォルトキーワードを取得または作成
        default_keyword = db.query(Keyword).filter(Keyword.term == "sample").first()
        if not default_keyword:
            default_keyword = Keyword(
                term="sample",
                category="demo",
                platforms=["twitter", "youtube", "reddit"],
                language="ja"
            )
            db.add(default_keyword)
            db.commit()
            db.refresh(default_keyword)
        
        # サンプルデータのテンプレート
        sample_contents = [
            "この新しいAI技術は本当に革新的ですね！",
            "最新のアップデートには少し不満があります...",
            "素晴らしい機能追加ありがとうございます",
            "使いにくいインターフェースを改善してほしい",
            "期待していた通りの品質でした",
            "価格に見合った価値があるかわからない",
            "カスタマーサポートの対応が良かった",
            "バグが多すぎて困っています",
            "デザインがとても美しい",
            "もう少し機能を増やしてほしい"
        ]
        
        sample_hashtags = [
            ["#AI", "#技術"],
            ["#レビュー", "#製品"],
            ["#アップデート", "#新機能"],
            ["#デザイン", "#UI"],
            ["#サポート", "#カスタマー"]
        ]
        
        platforms = ["twitter", "youtube", "reddit"]
        sentiments = ["positive", "negative", "neutral"]
        
        created_posts = []
        
        for i in range(count):
            # ランダムな日時を生成（過去30日以内）
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            posted_time = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
            
            # 投稿を作成
            post = Post(
                external_id=f"sample_{i}_{int(datetime.now().timestamp())}",
                platform=random.choice(platforms),
                content=random.choice(sample_contents),
                author=f"user_{random.randint(1000, 9999)}",
                author_followers=random.randint(10, 10000),
                url=f"https://example.com/post/{i}",
                posted_at=posted_time,
                collected_at=datetime.now(),                
                likes=random.randint(0, 100),
                shares=random.randint(0, 50),
                comments=random.randint(0, 30),
                hashtags=random.choice(sample_hashtags)
            )
            
            db.add(post)
            db.flush()  # IDを取得するために一時保存
            
            # 感情分析結果を作成
            sentiment_analysis = SentimentAnalysis(
                post_id=post.id,
                keyword_id=default_keyword.id,
                sentiment_label=random.choice(sentiments),
                sentiment_score=random.uniform(-1.0, 1.0),
                confidence=random.uniform(0.5, 0.95),
                emotions={"joy": random.uniform(0, 1), "anger": random.uniform(0, 1)},
                topics=["sample_topic"],
                keywords_found=["sample", "keyword"],
                reasoning="サンプルデータとして生成された分析結果",
                model_used="sample_model",
                analysis_version="1.0",
                analyzed_at=datetime.now()
            )
            
            db.add(sentiment_analysis)
            created_posts.append(post)
        
        db.commit()
        
        logger.info(f"Successfully generated {len(created_posts)} sample posts")
        
        return {
            "message": f"{len(created_posts)}件のサンプルデータを生成しました",
            "generated_count": len(created_posts),
            "platforms": list(set(post.platform for post in created_posts)),
            "date_range": {
                "earliest": min(post.posted_at for post in created_posts if post.posted_at).isoformat(),
                "latest": max(post.posted_at for post in created_posts if post.posted_at).isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error generating sample data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"サンプルデータ生成エラー: {str(e)}")


@router.delete("/clear-sample-data")
async def clear_sample_data(db: Session = Depends(get_db)):
    """サンプルデータを削除"""
    try:
        # サンプルデータの投稿を削除（external_idが"sample_"で始まるもの）
        sample_posts = db.query(Post).filter(Post.external_id.like("sample_%")).all()
        
        # 関連する感情分析データも削除
        for post in sample_posts:
            db.query(SentimentAnalysis).filter(SentimentAnalysis.post_id == post.id).delete()
            db.delete(post)
        
        db.commit()
        
        return {
            "message": f"{len(sample_posts)}件のサンプルデータを削除しました",
            "deleted_count": len(sample_posts)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing sample data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"サンプルデータ削除エラー: {str(e)}")
