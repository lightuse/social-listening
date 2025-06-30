from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import logging
import json
from collections import Counter, defaultdict
import re

from core.database import get_db
from models.database import Post, Keyword, SentimentAnalysis, Report, CollectionTask
from services.bedrock_engine import BedrockSentimentEngine
from services.data_collector import SocialMediaCollector
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
sentiment_engine = BedrockSentimentEngine()
data_collector = SocialMediaCollector()


class KeywordCreate(BaseModel):
    term: str
    category: Optional[str] = None
    platforms: Optional[List[str]] = ["twitter", "youtube", "reddit"]
    language: Optional[str] = "ja"


class AnalysisRequest(BaseModel):
    keywords: List[str]
    platforms: Optional[List[str]] = ["twitter", "youtube", "reddit"]
    max_posts_per_platform: Optional[int] = 100
    start_date: Optional[datetime] = None


class ReportRequest(BaseModel):
    keywords: List[str]
    platforms: Optional[List[str]] = ["twitter", "youtube", "reddit"]
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@router.post("/keywords")
async def create_keyword(keyword: KeywordCreate, db: Session = Depends(get_db)):
    """Create a new keyword to monitor"""
    try:
        logger.info(f"Creating keyword: {keyword.term}")
        
        # Check if keyword already exists
        existing = db.query(Keyword).filter(Keyword.term == keyword.term).first()
        if existing:
            logger.warning(f"Keyword already exists: {keyword.term}")
            raise HTTPException(status_code=400, detail=f"Keyword '{keyword.term}' already exists")
        
        db_keyword = Keyword(
            term=keyword.term,
            category=keyword.category,
            platforms=keyword.platforms,
            language=keyword.language
        )
        db.add(db_keyword)
        db.commit()
        db.refresh(db_keyword)
        
        logger.info(f"Keyword created successfully: {keyword.term} (ID: {db_keyword.id})")
        return {"message": "Keyword created successfully", "keyword_id": db_keyword.id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating keyword: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/keywords")
async def list_keywords(db: Session = Depends(get_db)):
    """List all keywords"""
    keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
    return [
        {
            "id": k.id,
            "term": k.term,
            "category": k.category,
            "platforms": k.platforms,
            "language": k.language,
            "created_at": k.created_at
        }
        for k in keywords
    ]


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """Delete a keyword"""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    keyword.is_active = False
    db.commit()
    
    return {"message": "Keyword deleted successfully"}


@router.post("/analyze")
async def start_analysis(
    request: AnalysisRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start sentiment analysis for keywords"""
    try:
        logger.info(f"Starting analysis for keywords: {request.keywords}, platforms: {request.platforms}")
        
        # Validate platforms
        available_platforms = data_collector.get_available_platforms()
        requested_platforms = request.platforms or available_platforms
        valid_platforms = [p for p in requested_platforms if p in available_platforms]
        
        if not valid_platforms:
            raise HTTPException(
                status_code=400, 
                detail=f"No valid platforms available. Requested: {requested_platforms}, Available: {available_platforms}"
            )
        
        # Warn about unavailable platforms
        unavailable_platforms = [p for p in requested_platforms if p not in available_platforms]
        if unavailable_platforms:
            logger.warning(f"Unavailable platforms skipped: {unavailable_platforms}")
        
        # Create collection task
        task = CollectionTask(
            platform=",".join(valid_platforms),
            keywords=request.keywords,
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Calculate estimated time based on platforms
        estimated_minutes = len(valid_platforms) * len(request.keywords) * 2  # 2 minutes per platform per keyword
        estimated_time = f"{min(estimated_minutes, 15)} minutes"
        
        logger.info(f"Created analysis task {task.id} for platforms: {valid_platforms}")
        
        # Start background task
        background_tasks.add_task(
            run_analysis_task, 
            task.id, 
            request.keywords, 
            valid_platforms,
            request.max_posts_per_platform
        )
        
        return {
            "message": "Analysis started",
            "task_id": task.id,
            "platforms": valid_platforms,
            "estimated_time": estimated_time,
            "keywords_count": len(request.keywords)
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/analysis/status/{task_id}")
async def get_analysis_status(task_id: int, db: Session = Depends(get_db)):
    """Get analysis task status"""
    task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.id,
        "status": task.status,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "posts_collected": task.posts_collected,
        "errors": task.errors
    }


@router.get("/posts")
async def get_posts(
    keyword: Optional[str] = None,
    platform: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get collected posts with filtering"""
    query = db.query(Post).outerjoin(SentimentAnalysis)
    
    if keyword:
        # Search in both registered keywords and post content
        keyword_filter = or_(
            Post.content.contains(keyword),
            Post.content.like(f"%{keyword}%")
        )
        query = query.filter(keyword_filter)
    
    if platform:
        query = query.filter(Post.platform == platform)
    
    if sentiment:
        query = query.filter(SentimentAnalysis.sentiment_label == sentiment)
    
    posts = query.order_by(Post.posted_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for post in posts:
        post_data = {
            "id": post.id,
            "platform": post.platform,
            "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
            "author": post.author,
            "posted_at": post.posted_at,
            "likes": post.likes,
            "shares": post.shares,
            "comments": post.comments,
            "url": post.url
        }
        
        # Add sentiment data if available
        if post.analyses:
            analysis = post.analyses[0]  # Get latest analysis
            post_data["sentiment"] = {
                "label": analysis.sentiment_label,
                "score": analysis.sentiment_score,
                "confidence": analysis.confidence
            }
        
        result.append(post_data)
    
    return {"posts": result, "total": len(result)}


@router.get("/sentiment/summary")
async def get_sentiment_summary(
    keywords: Optional[str] = None,
    platform: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get sentiment analysis summary"""
    try:
        logger.info(f"Getting sentiment summary for keywords: {keywords}, platform: {platform}, days: {days}")
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Build query - start with SentimentAnalysis table
        query = db.query(SentimentAnalysis).join(Post).filter(
            Post.collected_at >= start_date,
            Post.collected_at <= end_date
        )
        
        # Filter by keywords if provided
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",")]
            # Search in post content or hashtags for keywords
            keyword_filters = []
            for keyword in keyword_list:
                keyword_filters.append(Post.content.contains(keyword))
                keyword_filters.append(Post.hashtags.contains(keyword))
            
            # Use OR condition for any keyword match
            from sqlalchemy import or_
            query = query.filter(or_(*keyword_filters))
        
        # Filter by platform if provided
        if platform:
            query = query.filter(Post.platform == platform)
        
        analyses = query.all()
        
        logger.info(f"Found {len(analyses)} analyses matching criteria")
        
        if not analyses:
            return {
                "total_posts": 0,
                "sentiment_breakdown": {
                    "positive": {"count": 0, "percentage": 0},
                    "negative": {"count": 0, "percentage": 0},
                    "neutral": {"count": 0, "percentage": 0}
                },
                "average_sentiment": 0,
                "period": f"{days} days",
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "filters": {
                    "keywords": keywords,
                    "platform": platform
                }
            }
        
        # Calculate sentiment breakdown
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        sentiment_scores = []
        
        for analysis in analyses:
            if analysis.sentiment_label in sentiment_counts:
                sentiment_counts[analysis.sentiment_label] += 1
            if analysis.sentiment_score is not None:
                sentiment_scores.append(analysis.sentiment_score)
        
        total = len(analyses)
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        return {
            "total_posts": total,
            "sentiment_breakdown": {
                "positive": {
                    "count": sentiment_counts["positive"], 
                    "percentage": round(sentiment_counts["positive"]/total*100, 1)
                },
                "negative": {
                    "count": sentiment_counts["negative"], 
                    "percentage": round(sentiment_counts["negative"]/total*100, 1)
                },
                "neutral": {
                    "count": sentiment_counts["neutral"], 
                    "percentage": round(sentiment_counts["neutral"]/total*100, 1)
                }
            },
            "average_sentiment": round(avg_sentiment, 3),
            "average_confidence": round(sum(a.confidence or 0 for a in analyses) / total, 3) if total > 0 else 0,
            "period": f"{days} days",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "filters": {
                "keywords": keywords,
                "platform": platform
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"感情分析サマリー取得エラー: {str(e)}")


@router.post("/analysis/reports")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate a comprehensive analysis report"""
    try:
        # Create report record
        report = Report(
            title=f"Social Listening Report - {', '.join(request.keywords)}",
            description=f"Analysis of {', '.join(request.platforms)} platforms",
            keywords=request.keywords,
            platforms=request.platforms,
            date_from=request.date_from or datetime.now(timezone.utc) - timedelta(days=7),
            date_to=request.date_to or datetime.now(timezone.utc),
            status="pending"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Start background report generation
        background_tasks.add_task(generate_report_task, report.id)
        
        return {
            "message": "Report generation started",
            "report_id": report.id,
            "estimated_time": "10-20 minutes"
        }
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/reports/{report_id}")
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get generated report"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": report.id,
        "title": report.title,
        "status": report.status,
        "generated_at": report.generated_at,
        "summary": report.summary,
        "sentiment_summary": report.sentiment_summary,
        "key_insights": report.key_insights,
        "charts_data": report.charts_data
    }


@router.get("/analysis/reports")
async def list_reports(db: Session = Depends(get_db)):
    """List all reports"""
    reports = db.query(Report).order_by(Report.generated_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "title": r.title,
            "status": r.status,
            "generated_at": r.generated_at,
            "keywords": r.keywords,
            "platforms": r.platforms
        }
        for r in reports
    ]


@router.get("/debug/keywords")
async def debug_keywords(db: Session = Depends(get_db)):
    """Debug endpoint to check keyword table"""
    try:
        keywords = db.query(Keyword).all()
        return {
            "total_keywords": len(keywords),
            "keywords": [
                {
                    "id": k.id,
                    "term": k.term,
                    "category": k.category,
                    "platforms": k.platforms,
                    "language": k.language,
                    "is_active": k.is_active,
                    "created_at": k.created_at.isoformat() if k.created_at else None
                }
                for k in keywords
            ]
        }
    except Exception as e:
        logger.error(f"Debug keywords error: {e}", exc_info=True)
        return {"error": str(e)}


# Background task functions
async def run_analysis_task(
    task_id: int, 
    keywords: List[str], 
    platforms: List[str],
    max_posts_per_platform: int
):
    """Background task to run sentiment analysis"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Update task status
        task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return
            
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"Starting analysis task {task_id} for platforms: {platforms}, keywords: {keywords}")
        
        # Initialize services
        await sentiment_engine.initialize()
        
        # Check which platforms are actually available
        available_platforms = data_collector.get_available_platforms()
        valid_platforms = [p for p in platforms if p in available_platforms]
        
        if not valid_platforms:
            raise Exception(f"No valid platforms available from requested: {platforms}")
        
        # Log platform availability
        for platform in platforms:
            if platform in available_platforms:
                logger.info(f"Platform {platform}: API credentials available")
            else:
                logger.warning(f"Platform {platform}: API credentials not available, skipping")
        
        # Collect posts with platform-specific error handling
        logger.info(f"Collecting posts from {len(valid_platforms)} platforms: {valid_platforms}")
        posts = await data_collector.collect_all_platforms(
            keywords, valid_platforms, max_posts_per_platform
        )
        
        logger.info(f"Collected {len(posts)} total posts from all platforms")
        
        # Platform-specific collection summary
        platform_counts = {}
        for post in posts:
            platform = post.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        for platform, count in platform_counts.items():
            logger.info(f"Platform {platform}: {count} posts collected")
        
        # Save posts to database
        posts_saved = 0
        for post_data in posts:
            # Check if post already exists
            existing = db.query(Post).filter(Post.external_id == post_data['external_id']).first()
            if existing:
                logger.debug(f"Post {post_data['external_id']} already exists, skipping")
                continue
            
            # Save post
            post = Post(**post_data)
            db.add(post)
            db.flush()
            
            # Analyze sentiment
            analysis_result = await sentiment_engine.analyze_sentiment(
                post_data['content'], keywords
            )
            
            # Save analysis for each keyword
            for keyword in keywords:
                keyword_obj = db.query(Keyword).filter(Keyword.term == keyword).first()
                if not keyword_obj:
                    keyword_obj = Keyword(term=keyword, platforms=valid_platforms)
                    db.add(keyword_obj)
                    db.flush()
                
                analysis = SentimentAnalysis(
                    post_id=post.id,
                    keyword_id=keyword_obj.id,
                    sentiment_label=analysis_result.get('sentiment_label'),
                    sentiment_score=analysis_result.get('sentiment_score'),
                    confidence=analysis_result.get('confidence'),
                    emotions=analysis_result.get('emotions'),
                    topics=analysis_result.get('topics'),
                    keywords_found=analysis_result.get('keywords_found'),
                    model_used=analysis_result.get('model_used'),
                    analysis_version=analysis_result.get('analysis_version')
                )
                db.add(analysis)
            
            posts_saved += 1
        
        db.commit()
        
        # Update task completion
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        task.posts_collected = posts_saved
        task.platforms_used = ",".join(valid_platforms)
        db.commit()
        
        logger.info(f"Analysis task {task_id} completed successfully. Processed {posts_saved} new posts from platforms: {valid_platforms}")
        
    except Exception as e:
        logger.error(f"Analysis task {task_id} failed: {e}", exc_info=True)
        if 'task' in locals():
            task.status = "failed"
            task.errors = [str(e)]
            task.completed_at = datetime.now(timezone.utc)
            db.commit()
    
    finally:
        db.close()


async def generate_report_task(report_id: int):
    """Background task to generate report"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        report.status = "generating"
        db.commit()
        
        # Get analyses for the report
        query = db.query(SentimentAnalysis).join(Post).join(Keyword)
        
        if report.keywords:
            query = query.filter(Keyword.term.in_(report.keywords))
        
        if report.date_from and report.date_to:
            query = query.filter(
                Post.posted_at >= report.date_from,
                Post.posted_at <= report.date_to
            )
        
        analyses = query.all()
        
        if analyses:
            # Initialize sentiment engine
            await sentiment_engine.initialize()
            
            # Generate summary report
            analysis_data = [
                {
                    "sentiment_label": a.sentiment_label,
                    "sentiment_score": a.sentiment_score,
                    "confidence": a.confidence,
                    "emotions": a.emotions,
                    "topics": a.topics,
                    "keywords_found": a.keywords_found
                }
                for a in analyses
            ]
            
            summary_report = await sentiment_engine.generate_summary_report(
                analysis_data, report.keywords
            )
            
            # Update report
            report.summary = summary_report.get("executive_summary")
            report.sentiment_summary = summary_report.get("sentiment_insights")
            report.key_insights = summary_report.get("key_findings")
            report.charts_data = {
                "sentiment_breakdown": _calculate_sentiment_breakdown(analyses),
                "timeline": _calculate_timeline_data(analyses),
                "platform_breakdown": _calculate_platform_breakdown(analyses)
            }
        
        report.status = "completed"
        db.commit()
        
        logger.info(f"Report {report_id} generated successfully")
        
    except Exception as e:
        logger.error(f"Report generation {report_id} failed: {e}")
        report.status = "failed"
        db.commit()
    
    finally:
        db.close()


def _calculate_sentiment_breakdown(analyses):
    """Calculate sentiment breakdown for charts"""
    positive = len([a for a in analyses if a.sentiment_label == "positive"])
    negative = len([a for a in analyses if a.sentiment_label == "negative"])
    neutral = len([a for a in analyses if a.sentiment_label == "neutral"])
    
    total = len(analyses)
    if total == 0:
        return {}
    
    return {
        "positive": round(positive/total*100, 1),
        "negative": round(negative/total*100, 1),
        "neutral": round(neutral/total*100, 1)
    }


def _calculate_timeline_data(analyses):
    """Calculate timeline data for charts"""
    # Group by date
    from collections import defaultdict
    timeline = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    
    for analysis in analyses:
        if analysis.post and analysis.post.posted_at:
            # タイムゾーン対応
            post_time = analysis.post.posted_at
            if post_time.tzinfo is None:
                post_time = post_time.replace(tzinfo=timezone.utc)
            
            date_key = post_time.strftime("%Y-%m-%d")
            sentiment = analysis.sentiment_label or "neutral"
            timeline[date_key][sentiment] += 1
    
    return dict(timeline)


def _calculate_platform_breakdown(analyses):
    """Calculate platform breakdown for charts"""
    from collections import defaultdict
    platforms = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    
    for analysis in analyses:
        if analysis.post and analysis.post.platform:
            platform = analysis.post.platform
            sentiment = analysis.sentiment_label or "neutral"
            platforms[platform][sentiment] += 1
    
    return dict(platforms)


@router.post("/research-report")
async def generate_research_report(
    background_tasks: BackgroundTasks,
    query: str = Query(..., description="調査したいテーマやキーワード"),
    days: Optional[int] = Query(7, description="過去何日間のデータを含めるか"),
    db: Session = Depends(get_db)
):
    """研究用の統合レポートを生成（要件対応）"""
    try:
        logger.info(f"Generating research report for query: {query}")
        
        # 1. キーワードを自動解析・展開
        keywords = _extract_keywords_from_query(query)
        logger.info(f"Extracted keywords: {keywords}")
        
        # 2. データ収集・分析タスクを開始
        task = CollectionTask(
            platform="twitter,youtube,reddit",
            keywords=keywords,
            status="pending",
            description=f"Research report: {query}"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # 3. バックグラウンドで統合レポート生成
        background_tasks.add_task(
            generate_integrated_research_report,
            task.id,
            query,
            keywords,
            days
        )
        
        return {
            "message": "研究レポート生成を開始しました",
            "task_id": task.id,
            "query": query,
            "keywords": keywords,
            "estimated_time": "15-20分",
            "status_check_url": f"/api/v1/research-report/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Error generating research report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"研究レポート生成エラー: {str(e)}")


@router.get("/research-report/status/{task_id}")
async def get_research_report_status(task_id: int, db: Session = Depends(get_db)):
    """研究レポートの生成状況を確認"""
    task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    
    response = {
        "task_id": task.id,
        "status": task.status,
        "query": task.description,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "progress": _calculate_progress(task)
    }
    
    # 完了していればレポートデータも含める
    if task.status == "completed" and task.report_data:
        response["report"] = json.loads(task.report_data)
    
    return response


@router.get("/research-report/{task_id}")
async def get_research_report(task_id: int, db: Session = Depends(get_db)):
    """完成した研究レポートを取得"""
    task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="レポートはまだ生成中です")
    
    if not task.report_data:
        raise HTTPException(status_code=404, detail="レポートデータが見つかりません")
    
    return json.loads(task.report_data)


def _extract_keywords_from_query(query: str) -> List[str]:
    """クエリからキーワードを自動抽出・展開"""
    # シンプルな実装（将来的にはNLPライブラリを使用）
    base_keywords = []
    
    # 基本的なキーワード抽出
    if "AIエージェント" in query or "AI" in query:
        base_keywords.extend(["AI", "AIエージェント", "人工知能", "AI技術"])
    
    if "雇用" in query:
        base_keywords.extend(["雇用", "就職", "転職", "労働", "仕事"])
    
    if "影響" in query:
        base_keywords.extend(["影響", "変化", "効果"])
    
    # 重複を除去
    return list(set(base_keywords))


def _calculate_progress(task: CollectionTask) -> Dict[str, Any]:
    """タスクの進捗を計算"""
    if task.status == "pending":
        return {"percentage": 0, "stage": "待機中"}
    elif task.status == "running":
        return {"percentage": 50, "stage": "データ収集・分析中"}
    elif task.status == "completed":
        return {"percentage": 100, "stage": "完了"}
    else:
        return {"percentage": 0, "stage": "エラー"}


async def generate_integrated_research_report(
    task_id: int,
    query: str, 
    keywords: List[str],
    days: int
):
    """統合研究レポートを生成（バックグラウンド処理）"""
    from core.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        # タスク状態を更新
        task = db.query(CollectionTask).filter(CollectionTask.id == task_id).first()
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        db.commit()
        
        # 1. データ収集
        await sentiment_engine.initialize()
        collected_posts = await data_collector.collect_all_platforms(
            keywords, ["twitter", "youtube", "reddit"], 100
        )
        
        # 2. 感情分析実行
        analyzed_posts = []
        for post_data in collected_posts:
            # 投稿を保存
            post = Post(**post_data)
            db.add(post)
            db.flush()
            
            # 感情分析
            analysis_result = await sentiment_engine.analyze_sentiment(
                post_data['content'], keywords
            )
            
            # 分析結果を保存
            analysis = SentimentAnalysis(
                post_id=post.id,
                keyword_id=1,  # デフォルトキーワードID
                sentiment_label=analysis_result.get('sentiment_label'),
                sentiment_score=analysis_result.get('sentiment_score'),
                confidence=analysis_result.get('confidence'),
                emotions=analysis_result.get('emotions'),
                topics=analysis_result.get('topics'),
                keywords_found=analysis_result.get('keywords_found'),
                reasoning=analysis_result.get('reasoning'),
                model_used=analysis_result.get('model_used'),
                analysis_version=analysis_result.get('analysis_version')
            )
            db.add(analysis)
            
            analyzed_posts.append({
                "post": post_data,
                "analysis": analysis_result
            })
        
        db.commit()
        
        # 3. 統合レポート生成
        report = await _generate_integrated_report(query, keywords, analyzed_posts, db)
        
        # 4. タスク完了
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        task.posts_collected = len(analyzed_posts)
        task.report_data = json.dumps(report, ensure_ascii=False, default=str)
        db.commit()
        
        logger.info(f"Research report {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Research report generation failed: {e}", exc_info=True)
        task.status = "failed"
        task.errors = [str(e)]
        task.completed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


async def _generate_integrated_report(
    query: str,
    keywords: List[str], 
    analyzed_posts: List[Dict],
    db: Session
) -> Dict[str, Any]:
    """統合レポートの内容を生成"""
    
    # 感情分析集計
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    positive_posts = []
    negative_posts = []
    
    for item in analyzed_posts:
        sentiment = item["analysis"].get("sentiment_label", "neutral")
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        
        # 代表的な投稿を収集（信頼度の高いもの）
        confidence = item["analysis"].get("confidence", 0)
        post_data = {
            "content": item["post"]["content"][:200] + "..." if len(item["post"]["content"]) > 200 else item["post"]["content"],
            "platform": item["post"]["platform"],
            "author": "匿名ユーザー",  # 匿名化
            "posted_at": item["post"]["posted_at"],
            "url": item["post"]["url"],
            "confidence": confidence,
            "reasoning": item["analysis"].get("reasoning", "")
        }
        
        if sentiment == "positive" and len(positive_posts) < 5:
            positive_posts.append(post_data)
        elif sentiment == "negative" and len(negative_posts) < 5:
            negative_posts.append(post_data)
    
    total_posts = len(analyzed_posts)
    
    # レポート構造
    report = {
        "query": query,
        "keywords": keywords,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_analyzed_posts": total_posts,
            "data_collection_period": f"過去{7}日間",
            "platforms": ["Twitter", "YouTube", "Reddit"]
        },
        "sentiment_analysis": {
            "overview": f"「{query}」に関する{total_posts}件の投稿を分析",
            "positive": {
                "count": sentiment_counts["positive"],
                "percentage": round((sentiment_counts["positive"] / total_posts) * 100, 1) if total_posts > 0 else 0,
                "sample_posts": positive_posts
            },
            "negative": {
                "count": sentiment_counts["negative"], 
                "percentage": round((sentiment_counts["negative"] / total_posts) * 100, 1) if total_posts > 0 else 0,
                "sample_posts": negative_posts
            },
            "neutral": {
                "count": sentiment_counts["neutral"],
                "percentage": round((sentiment_counts["neutral"] / total_posts) * 100, 1) if total_posts > 0 else 0
            }
        },
        "key_insights": await _generate_key_insights(query, sentiment_counts, analyzed_posts),
        "methodology": {
            "data_sources": "Twitter API, YouTube API, Reddit API",
            "analysis_engine": "AWS Bedrock (Amazon Nova Lite)",
            "keywords_used": keywords,
            "collection_time": "15-20分",
            "anonymization": "ユーザー情報は匿名化済み"
        }
    }
    
    return report


async def _generate_key_insights(
    query: str,
    sentiment_counts: Dict[str, int],
    analyzed_posts: List[Dict]
) -> List[str]:
    """主要な洞察を生成"""
    insights = []
    total = sum(sentiment_counts.values())
    
    if total == 0:
        return ["分析対象となる投稿が見つかりませんでした。"]
    
    # 感情分布の洞察
    pos_pct = (sentiment_counts["positive"] / total) * 100
    neg_pct = (sentiment_counts["negative"] / total) * 100
    
    if pos_pct > neg_pct:
        insights.append(f"全体的にポジティブな意見が多く、ポジティブ意見が{pos_pct:.1f}%を占めています。")
    elif neg_pct > pos_pct:
        insights.append(f"ネガティブな意見が優勢で、{neg_pct:.1f}%がネガティブな反応を示しています。")
    else:
        insights.append("ポジティブとネガティブの意見がほぼ拮抗しています。")
    
    # 極端な意見の確認
    if pos_pct > 70:
        insights.append("圧倒的にポジティブな反応が多く、一般的に好意的に受け止められています。")
    elif neg_pct > 70:
        insights.append("強い懸念や批判的な意見が大多数を占めており、慎重な対応が必要です。")
    
    # プラットフォーム別の傾向（簡易）
    platform_sentiment = {}
    for item in analyzed_posts:
        platform = item["post"]["platform"]
        sentiment = item["analysis"].get("sentiment_label", "neutral")
        
        if platform not in platform_sentiment:
            platform_sentiment[platform] = {"positive": 0, "negative": 0, "neutral": 0}
        platform_sentiment[platform][sentiment] += 1
    
    # 主要なプラットフォームの傾向
    for platform, sentiments in platform_sentiment.items():
        total_platform = sum(sentiments.values())
        if total_platform > 5:  # 十分なデータがある場合のみ
            dominant = max(sentiments, key=sentiments.get)
            percentage = (sentiments[dominant] / total_platform) * 100
            insights.append(f"{platform}では{dominant}な意見が{percentage:.1f}%を占めています。")
    
    return insights


@router.get("/trending-topics")
async def get_trending_topics(
    days: Optional[int] = Query(7, description="過去何日間のデータを分析するか"),
    limit: Optional[int] = Query(10, description="取得するトレンドトピック数"),
    platform: Optional[str] = Query(None, description="特定のプラットフォームに絞り込み"),
    db: Session = Depends(get_db)
):
    """トレンドトピックを分析して返す"""
    try:
        logger.info(f"Getting trending topics for {days} days")
        
        # 指定期間の投稿を取得
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        end_date = datetime.now(timezone.utc)
        
        query = db.query(Post).filter(
            Post.posted_at >= start_date,
            Post.posted_at <= end_date
        )
        
        if platform:
            query = query.filter(Post.platform == platform)
        
        posts = query.all()
        
        if not posts:
            return {
                "trending_topics": [],
                "summary": {
                    "period": f"{days} days",
                    "total_posts": 0,
                    "analyzed_platforms": []
                }
            }
        
        # トピック抽出と分析
        topic_analysis = await _analyze_trending_topics(posts, db)
        
        # 上位トピックを取得
        trending_topics = topic_analysis["topics"][:limit]
        
        return {
            "trending_topics": trending_topics,
            "summary": {
                "period": f"{days} days",
                "total_posts": len(posts),
                "analyzed_platforms": list(set(p.platform for p in posts if p.platform)),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            },
            "methodology": {
                "analysis_method": "キーワード頻度分析 + 感情分析",
                "ranking_criteria": "出現頻度、感情スコア、最近の活動度"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"トレンドトピック取得エラー: {str(e)}")


@router.get("/trending-topics/details/{topic}")
async def get_trending_topic_details(
    topic: str,
    days: Optional[int] = Query(7, description="過去何日間のデータを分析するか"),
    db: Session = Depends(get_db)
):
    """特定のトレンドトピックの詳細分析"""
    try:
        logger.info(f"Getting detailed analysis for topic: {topic}")
        
        # 指定期間の関連投稿を取得
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        end_date = datetime.now(timezone.utc)
        
        # トピックに関連する投稿を検索（簡易的な実装）
        posts = db.query(Post).filter(
            Post.posted_at >= start_date,
            Post.posted_at <= end_date,
            or_(
                Post.content.contains(topic),
                Post.content.contains(topic.lower()),
                Post.content.contains(topic.upper())
            )
        ).all()
        
        if not posts:
            raise HTTPException(status_code=404, detail="指定されたトピックに関する投稿が見つかりません")
        
        # 詳細分析を実行
        topic_details = await _analyze_topic_details(topic, posts, db)
        
        return topic_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"トピック詳細分析エラー: {str(e)}")


async def _analyze_trending_topics(posts: List[Post], db: Session) -> Dict[str, Any]:
    """投稿からトレンドトピックを分析"""
    
    logger.info(f"Analyzing trending topics from {len(posts)} posts")
    
    # 1. キーワード抽出と頻度カウント
    all_keywords = []
    platform_breakdown = defaultdict(lambda: defaultdict(int))
    
    for post in posts:
        if not post.content:
            continue
            
        # シンプルなキーワード抽出（日本語対応）
        keywords = _extract_keywords_from_content(post.content)
        all_keywords.extend(keywords)
        logger.debug(f"Extracted keywords from post {post.id}: {keywords}")
        
        # プラットフォーム別の分析
        for keyword in keywords:
            platform_breakdown[keyword][post.platform or "unknown"] += 1
    
    logger.info(f"Total keywords extracted: {len(all_keywords)}")
    
    # 2. キーワード頻度分析
    keyword_counts = Counter(all_keywords)
    logger.info(f"Top 10 keywords: {keyword_counts.most_common(10)}")
    
    # 3. 感情分析結果との関連付け
    sentiment_by_keyword = await _get_sentiment_by_keywords(posts, db)
    
    # 4. トピックランキング生成
    topics = []
    for keyword, count in keyword_counts.most_common(50):  # 上位50個を分析
        if count < 1:  # 最小出現回数を1に変更（より多くのトピックを検出）
            continue
            
        sentiment_data = sentiment_by_keyword.get(keyword, {})
        
        # 感情データが空の場合はデフォルト値を設定
        if not sentiment_data:
            sentiment_data = {"positive": 0, "negative": 0, "neutral": count, "average_score": 0}
        
        topic_data = {
            "topic": keyword,
            "mention_count": count,
            "platforms": dict(platform_breakdown[keyword]),
            "sentiment": {
                "positive": sentiment_data.get("positive", 0),
                "negative": sentiment_data.get("negative", 0),
                "neutral": sentiment_data.get("neutral", count),  # デフォルトをcountに設定
                "average_score": sentiment_data.get("average_score", 0)
            },
            "trend_score": _calculate_trend_score(count, sentiment_data),
            "recent_activity": _calculate_recent_activity(keyword, posts)
        }
        topics.append(topic_data)
        logger.debug(f"Added topic: {keyword} with count {count} and trend score {topic_data['trend_score']}")
    
    # トレンドスコアでソート
    topics.sort(key=lambda x: x["trend_score"], reverse=True)
    
    logger.info(f"Generated {len(topics)} trending topics")
    
    return {"topics": topics}


async def _analyze_topic_details(topic: str, posts: List[Post], db: Session) -> Dict[str, Any]:
    """特定トピックの詳細分析"""
    
    # 1. 基本統計
    total_posts = len(posts)
    platforms = list(set(p.platform for p in posts if p.platform))
    
    # 2. 時系列データ
    timeline_data = _calculate_topic_timeline(topic, posts)
    
    # 3. プラットフォーム別分布
    platform_distribution = _calculate_platform_distribution(posts)
    
    # 4. 感情分析
    sentiment_analysis = await _get_detailed_sentiment_for_topic(topic, posts, db)
    
    # 5. 代表的な投稿サンプル
    sample_posts = _get_sample_posts(posts, limit=5)
    
    # 6. 関連キーワード
    related_keywords = _find_related_keywords(topic, posts)
    
    return {
        "topic": topic,
        "summary": {
            "total_mentions": total_posts,
            "platforms": platforms,
            "analysis_period": f"過去7日間",
            "peak_date": timeline_data.get("peak_date"),
            "trend_direction": _determine_trend_direction(timeline_data)
        },
        "timeline": timeline_data["daily_counts"],
        "platform_distribution": platform_distribution,
        "sentiment_analysis": sentiment_analysis,
        "sample_posts": sample_posts,
        "related_keywords": related_keywords,
        "insights": _generate_topic_insights(topic, posts, sentiment_analysis)
    }


def _extract_keywords_from_content(content: str) -> List[str]:
    """投稿内容からキーワードを抽出"""
    if not content:
        return []
    
    # 基本的なクリーニング
    content = re.sub(r'https?://\S+', '', content)  # URL除去
    content = re.sub(r'@\w+', '', content)  # メンション除去
    content = re.sub(r'#(\w+)', r'\1', content)  # ハッシュタグからキーワード抽出
    
    # 日本語と英語のキーワード抽出（簡易実装）
    keywords = []
    
    # 日本語キーワード（2文字以上のひらがな・カタカナ・漢字）
    jp_pattern = r'[あ-んア-ン一-龯]{2,}'
    jp_keywords = re.findall(jp_pattern, content)
    keywords.extend(jp_keywords)
    
    # 英語キーワード（3文字以上）
    en_pattern = r'\b[A-Za-z]{3,}\b'
    en_keywords = re.findall(en_pattern, content)
    keywords.extend([kw.lower() for kw in en_keywords])
    
    # よくある無意味な単語を除外
    stop_words = {'です', 'ます', 'する', 'した', 'ある', 'ない', 'れる', 'られる', 
                  'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    
    filtered_keywords = [kw for kw in keywords if kw not in stop_words and len(kw) >= 2]
    
    return filtered_keywords


async def _get_sentiment_by_keywords(posts: List[Post], db: Session) -> Dict[str, Dict]:
    """キーワード別の感情分析結果を取得"""
    sentiment_by_keyword = defaultdict(lambda: {
        "positive": 0, "negative": 0, "neutral": 0, 
        "scores": [], "average_score": 0
    })
    
    for post in posts:
        # 投稿の感情分析結果を取得
        analyses = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.post_id == post.id
        ).all()
        
        if not analyses:
            continue
            
        # 投稿からキーワードを抽出
        keywords = _extract_keywords_from_content(post.content or "")
        
        for analysis in analyses:
            sentiment = analysis.sentiment_label or "neutral"
            score = analysis.sentiment_score or 0
            
            for keyword in keywords:
                sentiment_by_keyword[keyword][sentiment] += 1
                sentiment_by_keyword[keyword]["scores"].append(score)
    
    # 平均スコアを計算
    for keyword_data in sentiment_by_keyword.values():
        if keyword_data["scores"]:
            keyword_data["average_score"] = sum(keyword_data["scores"]) / len(keyword_data["scores"])
    
    return dict(sentiment_by_keyword)


def _calculate_trend_score(mention_count: int, sentiment_data: Dict) -> float:
    """トレンドスコアを計算"""
    # 基本スコア（出現回数ベース）
    base_score = min(mention_count / 10.0, 10.0)  # 最大10点
    
    # 感情スコア調整
    total_sentiment = sentiment_data.get("positive", 0) + sentiment_data.get("negative", 0) + sentiment_data.get("neutral", 0)
    if total_sentiment > 0:
        positive_ratio = sentiment_data.get("positive", 0) / total_sentiment
        engagement_bonus = positive_ratio * 2.0  # ポジティブな反応にボーナス
    else:
        engagement_bonus = 0
    
    # 最終スコア
    final_score = base_score + engagement_bonus
    return round(final_score, 2)


def _calculate_recent_activity(keyword: str, posts: List[Post]) -> Dict[str, Any]:
    """最近の活動度を計算"""
    now = datetime.now(timezone.utc)
    recent_posts = []
    
    for post in posts:
        if not post.content or keyword not in post.content:
            continue
        
        try:
            # タイムゾーン対応
            post_time = post.posted_at
            if post_time is None:
                continue
                
            if post_time.tzinfo is None:
                post_time = post_time.replace(tzinfo=timezone.utc)
                
            hours_ago = (now - post_time).total_seconds() / 3600
            if hours_ago <= 24:  # 過去24時間
                recent_posts.append(post)
        except Exception as e:
            # エラーが発生した場合はスキップ
            logger.warning(f"Error calculating recent activity for post {post.id}: {e}")
            continue
    
    return {
        "last_24h_mentions": len(recent_posts),
        "activity_level": "high" if len(recent_posts) > 5 else "medium" if len(recent_posts) > 2 else "low"
    }


def _calculate_topic_timeline(topic: str, posts: List[Post]) -> Dict[str, Any]:
    """トピックの時系列データを計算"""
    daily_counts = defaultdict(int)
    
    for post in posts:
        if not post.content or topic not in post.content:
            continue
        
        # タイムゾーン対応
        post_time = post.posted_at
        if post_time.tzinfo is None:
            post_time = post_time.replace(tzinfo=timezone.utc)
            
        date_key = post_time.strftime("%Y-%m-%d")
        daily_counts[date_key] += 1
    
    # ピーク日を特定
    peak_date = max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else None
    
    return {
        "daily_counts": dict(daily_counts),
        "peak_date": peak_date
    }


def _calculate_platform_distribution(posts: List[Post]) -> Dict[str, int]:
    """プラットフォーム別分布を計算"""
    platform_counts = defaultdict(int)
    
    for post in posts:
        platform = post.platform or "unknown"
        platform_counts[platform] += 1
    
    return dict(platform_counts)


async def _get_detailed_sentiment_for_topic(topic: str, posts: List[Post], db: Session) -> Dict[str, Any]:
    """トピックの詳細感情分析"""
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    sentiment_scores = []
    
    for post in posts:
        analyses = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.post_id == post.id
        ).all()
        
        for analysis in analyses:
            sentiment = analysis.sentiment_label or "neutral"
            sentiment_counts[sentiment] += 1
            
            if analysis.sentiment_score is not None:
                sentiment_scores.append(analysis.sentiment_score)
    
    total = sum(sentiment_counts.values())
    average_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
    return {
        "distribution": {
            "positive": {
                "count": sentiment_counts["positive"],
                "percentage": round(sentiment_counts["positive"] / total * 100, 1) if total > 0 else 0
            },
            "negative": {
                "count": sentiment_counts["negative"],
                "percentage": round(sentiment_counts["negative"] / total * 100, 1) if total > 0 else 0
            },
            "neutral": {
                "count": sentiment_counts["neutral"],
                "percentage": round(sentiment_counts["neutral"] / total * 100, 1) if total > 0 else 0
            }
        },
        "average_score": round(average_score, 3),
        "total_analyzed": total
    }


def _get_sample_posts(posts: List[Post], limit: int = 5) -> List[Dict[str, Any]]:
    """代表的な投稿サンプルを取得"""
    # 投稿をランダムサンプリング（実際には多様性を考慮した選択が望ましい）
    import random
    
    sample_posts = random.sample(posts, min(len(posts), limit))
    
    return [
        {
            "content": post.content[:200] + "..." if len(post.content or "") > 200 else post.content,
            "platform": post.platform,
            "posted_at": (post.posted_at.replace(tzinfo=timezone.utc) if post.posted_at.tzinfo is None else post.posted_at).isoformat(),
            "url": post.url
        }
        for post in sample_posts
    ]


def _find_related_keywords(topic: str, posts: List[Post]) -> List[Dict[str, Any]]:
    """関連キーワードを検索"""
    related_keywords = defaultdict(int)
    
    for post in posts:
        if not post.content or topic not in post.content:
            continue
            
        keywords = _extract_keywords_from_content(post.content)
        for keyword in keywords:
            if keyword != topic and len(keyword) >= 2:
                related_keywords[keyword] += 1
    
    # 上位10個の関連キーワード
    top_related = sorted(related_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return [
        {"keyword": keyword, "co_occurrence_count": count}
        for keyword, count in top_related
    ]


def _determine_trend_direction(timeline_data: Dict) -> str:
    """トレンドの方向性を判定"""
    daily_counts = timeline_data.get("daily_counts", {})
    if len(daily_counts) < 2:
        return "insufficient_data"
    
    # 最近の日付順にソート
    sorted_dates = sorted(daily_counts.keys())
    recent_half = sorted_dates[len(sorted_dates)//2:]
    early_half = sorted_dates[:len(sorted_dates)//2]
    
    recent_avg = sum(daily_counts[date] for date in recent_half) / len(recent_half)
    early_avg = sum(daily_counts[date] for date in early_half) / len(early_half)
    
    if recent_avg > early_avg * 1.2:
        return "rising"
    elif recent_avg < early_avg * 0.8:
        return "declining"
    else:
        return "stable"


def _generate_topic_insights(topic: str, posts: List[Post], sentiment_analysis: Dict) -> List[str]:
    """トピックに関する洞察を生成"""
    insights = []
    
    total_posts = len(posts)
    sentiment_dist = sentiment_analysis.get("distribution", {})
    
    # 基本的な洞察
    insights.append(f"「{topic}」について{total_posts}件の投稿が分析されました。")
    
    # 感情分析に基づく洞察
    pos_pct = sentiment_dist.get("positive", {}).get("percentage", 0)
    neg_pct = sentiment_dist.get("negative", {}).get("percentage", 0)
    
    if pos_pct > neg_pct:
        insights.append(f"全体的にポジティブな反応が多く、{pos_pct}%がポジティブな意見です。")
    elif neg_pct > pos_pct:
        insights.append(f"ネガティブな意見が優勢で、{neg_pct}%がネガティブな反応を示しています。")
    else:
        insights.append("ポジティブとネガティブの意見がバランスよく分布しています。")
    
    # プラットフォーム固有の洞察
    platforms = list(set(p.platform for p in posts if p.platform))
    if len(platforms) > 1:
        insights.append(f"複数のプラットフォーム（{', '.join(platforms)}）で話題になっています。")
    
    return insights


@router.get("/sentiment/platform-breakdown")
async def get_platform_sentiment_breakdown(
    keywords: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get sentiment breakdown by platform"""
    try:
        logger.info(f"Getting platform sentiment breakdown for keywords: {keywords}, days: {days}")
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Build query - start with SentimentAnalysis table
        query = db.query(SentimentAnalysis, Post.platform).join(Post).filter(
            Post.collected_at >= start_date,
            Post.collected_at <= end_date
        )
        
        # Filter by keywords if provided
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",")]
            keyword_filters = []
            for keyword in keyword_list:
                keyword_filters.append(Post.content.contains(keyword))
                keyword_filters.append(Post.hashtags.contains(keyword))
            
            from sqlalchemy import or_
            query = query.filter(or_(*keyword_filters))
        
        results = query.all()
        
        logger.info(f"Found {len(results)} analyses for platform breakdown")
        
        # Group by platform and sentiment
        platform_stats = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
        
        for analysis, platform in results:
            if analysis.sentiment_label in platform_stats[platform]:
                platform_stats[platform][analysis.sentiment_label] += 1
        
        # Convert to the format expected by the frontend
        platform_data = {}
        for platform, sentiments in platform_stats.items():
            platform_data[platform] = {
                "positive": sentiments["positive"],
                "negative": sentiments["negative"], 
                "neutral": sentiments["neutral"],
                "total": sum(sentiments.values())
            }
        
        return {
            "platforms": platform_data,
            "period": f"{days} days",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "filters": {
                "keywords": keywords
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting platform sentiment breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting platform breakdown: {str(e)}")
