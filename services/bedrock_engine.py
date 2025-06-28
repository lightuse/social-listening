import boto3
import json
from typing import Dict, List, Any, Optional
from core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


class BedrockSentimentEngine:
    """AWS Bedrock AI Engine for sentiment analysis and social listening"""

    def __init__(self):
        self.bedrock_client = None
        self.bedrock_runtime = None
        self.mock_mode = False

    async def initialize(self):
        """Initialize AWS Bedrock clients with fallback to mock mode"""
        try:
            # AWS認証情報の準備
            auth_kwargs = {
                "region_name": settings.AWS_REGION,
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            }
            
            # AWS_SESSION_TOKENが設定されている場合は追加
            aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
            if aws_session_token:
                auth_kwargs["aws_session_token"] = aws_session_token
                logger.info("Using temporary AWS credentials with session token")
            else:
                logger.info("Using permanent AWS IAM credentials")

            self.bedrock_client = boto3.client("bedrock", **auth_kwargs)
            self.bedrock_runtime = boto3.client("bedrock-runtime", **auth_kwargs)
            
            # Test connection with timeout
            try:
                # Quick test to verify permissions
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("Bedrock connection timeout")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(5)  # 5 second timeout
                
                self.bedrock_client.list_foundation_models()
                signal.alarm(0)
                
                logger.info("✅ AWS Bedrock clients initialized successfully")
                self.mock_mode = False
                
            except (TimeoutError, Exception) as test_error:
                signal.alarm(0)
                logger.warning(f"⚠️ Bedrock connection failed: {test_error}")
                logger.warning("🔄 Switching to MOCK MODE for development")
                self.mock_mode = True
                
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock clients: {e}")
            logger.warning("🔄 Falling back to MOCK MODE")
            self.mock_mode = True

    async def analyze_sentiment(
        self, text: str, keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment of social media post using Claude or mock response"""
        
        # Return mock response if in mock mode
        if self.mock_mode:
            return self._get_mock_sentiment_analysis(text, keywords)

        keywords_text = f"特に以下のキーワードに注目して分析してください: {', '.join(keywords)}" if keywords else ""

        prompt = f"""
        以下のソーシャルメディア投稿を分析し、感情分析を行ってください。

        【投稿内容】
        {text}

        {keywords_text}

        以下の観点で分析し、JSON形式で回答してください：
        1. sentiment_label: "positive", "negative", "neutral" のいずれか
        2. sentiment_score: -1.0（非常にネガティブ）から1.0（非常にポジティブ）までの数値
        3. confidence: 0.0から1.0までの確信度
        4. emotions: 感情の詳細分析（joy, anger, fear, sadness, surprise, disgust, anticipation, trustなど）
        5. topics: 抽出されたトピック・テーマ
        6. keywords_found: 投稿に含まれる重要なキーワード
        7. reasoning: 分析の根拠

        回答例：
        {{
            "sentiment_label": "positive",
            "sentiment_score": 0.7,
            "confidence": 0.85,
            "emotions": {{
                "joy": 0.8,
                "trust": 0.6,
                "anticipation": 0.5
            }},
            "topics": ["商品レビュー", "顧客満足"],
            "keywords_found": ["素晴らしい", "おすすめ", "満足"],
            "reasoning": "投稿は明らかにポジティブな表現を使用しており、商品に対する高い満足度を示している"
        }}
        """

        try:
            # Different request format for Nova vs Claude models
            if "nova" in settings.DEFAULT_MODEL.lower():
                # Nova Lite uses content as an array of content blocks
                body = {
                    "messages": [{"role": "user", "content": [{"text": prompt}]}],
                    "inferenceConfig": {
                        "maxTokens": 2000,
                        "temperature": 0.1,
                        "topP": 0.9
                    }
                }
            else:
                # Claude format
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }

            response = self.bedrock_runtime.invoke_model(
                modelId=settings.DEFAULT_MODEL, body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())
            
            # Parse response based on model type
            if "nova" in settings.DEFAULT_MODEL.lower():
                # Nova format - response has output.message.content array
                output = response_body.get("output", {})
                message = output.get("message", {})
                content = message.get("content", [])
                if content and len(content) > 0:
                    text_response = content[0].get("text", "")
                else:
                    text_response = ""
            else:
                # Claude format
                text_response = response_body["content"][0]["text"]
            
            result = self._parse_sentiment_response(text_response)
            
            # Add metadata
            result["model_used"] = settings.DEFAULT_MODEL
            result["analysis_version"] = "1.0"
            
            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._get_fallback_sentiment_analysis(text)

    async def analyze_batch_sentiment(
        self, posts: List[Dict[str, Any]], keywords: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple posts"""
        results = []
        
        for post in posts:
            try:
                analysis = await self.analyze_sentiment(post.get("content", ""), keywords)
                analysis["post_id"] = post.get("external_id")
                results.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze post {post.get('external_id')}: {e}")
                fallback = self._get_fallback_sentiment_analysis(post.get("content", ""))
                fallback["post_id"] = post.get("external_id")
                results.append(fallback)
        
        return results

    async def generate_summary_report(
        self, analyses: List[Dict[str, Any]], keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Generate summary report from sentiment analyses or mock response"""
        
        if self.mock_mode:
            return self._get_mock_summary_report(analyses, keywords or [])

        # Prepare analysis summary
        total_posts = len(analyses)
        positive_count = sum(1 for a in analyses if a.get("sentiment_label") == "positive")
        negative_count = sum(1 for a in analyses if a.get("sentiment_label") == "negative")
        neutral_count = total_posts - positive_count - negative_count

        # Get most common topics and emotions
        all_topics = []
        all_emotions = {}
        
        for analysis in analyses:
            if analysis.get("topics"):
                all_topics.extend(analysis["topics"])
            if analysis.get("emotions"):
                for emotion, score in analysis["emotions"].items():
                    all_emotions[emotion] = all_emotions.get(emotion, []) + [score]

        # Calculate average emotions
        avg_emotions = {
            emotion: sum(scores) / len(scores) 
            for emotion, scores in all_emotions.items() 
            if scores
        }

        keywords_text = f"キーワード「{', '.join(keywords)}」に関する" if keywords else ""

        prompt = f"""
        {keywords_text}ソーシャルメディア分析結果をもとに、包括的なレポートを生成してください。

        【分析データ】
        - 総投稿数: {total_posts}
        - ポジティブ: {positive_count} ({positive_count/total_posts*100:.1f}%)
        - ネガティブ: {negative_count} ({negative_count/total_posts*100:.1f}%)
        - 中立: {neutral_count} ({neutral_count/total_posts*100:.1f}%)
        - 主要な感情: {avg_emotions}
        - 頻出トピック: {all_topics[:20]}

        以下の形式でレポートを生成してください：

        {{
            "executive_summary": "全体の要約と主要な洞察",
            "sentiment_insights": {{
                "overall_tone": "全体的なトーン",
                "positive_drivers": ["ポジティブな要因"],
                "negative_drivers": ["ネガティブな要因"],
                "neutral_factors": ["中立的な要因"]
            }},
            "key_findings": [
                "主要な発見1",
                "主要な発見2",
                "主要な発見3"
            ],
            "recommendations": [
                "推奨アクション1",
                "推奨アクション2",
                "推奨アクション3"
            ],
            "trending_topics": ["トレンドトピック"],
            "risk_alerts": ["注意すべきリスク"]
        }}
        """

        try:
            # Different request format for Nova vs Claude models
            if "nova" in settings.DEFAULT_MODEL.lower():
                # Nova Lite uses content as an array of content blocks
                body = {
                    "messages": [{"role": "user", "content": [{"text": prompt}]}],
                    "inferenceConfig": {
                        "maxTokens": 3000,
                        "temperature": 0.3,
                        "topP": 0.9
                    }
                }
            else:
                # Claude format
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 3000,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }

            response = self.bedrock_runtime.invoke_model(
                modelId=settings.DEFAULT_MODEL, body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())
            
            # Parse response based on model type
            if "nova" in settings.DEFAULT_MODEL.lower():
                # Nova format - response has output.message.content array
                output = response_body.get("output", {})
                message = output.get("message", {})
                content = message.get("content", [])
                if content and len(content) > 0:
                    text_response = content[0].get("text", "")
                else:
                    text_response = ""
            else:
                # Claude format
                text_response = response_body["content"][0]["text"]
                
            return self._parse_report_response(text_response)

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return self._get_fallback_report(analyses)

    async def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        
        prompt = f"""
        以下のテキストから重要なキーワードを抽出してください。
        ブランド名、商品名、感情表現、特徴的な表現を中心に抽出してください。

        【テキスト】
        {text}

        JSON配列形式で回答してください：
        ["キーワード1", "キーワード2", "キーワード3"]
        """

        try:
            # Different request format for Nova vs Claude models
            if "nova" in settings.DEFAULT_MODEL.lower():
                # Nova Lite uses content as an array of content blocks
                body = {
                    "messages": [{"role": "user", "content": [{"text": prompt}]}],
                    "inferenceConfig": {
                        "maxTokens": 1000,
                        "temperature": 0.1,
                        "topP": 0.9
                    }
                }
            else:
                # Claude format
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }

            response = self.bedrock_runtime.invoke_model(
                modelId=settings.DEFAULT_MODEL, body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())
            
            # Parse response based on model type
            if "nova" in settings.DEFAULT_MODEL.lower():
                # Nova format - response has output.message.content array
                output = response_body.get("output", {})
                message = output.get("message", {})
                content = message.get("content", [])
                if content and len(content) > 0:
                    result = content[0].get("text", "")
                else:
                    result = ""
            else:
                # Claude format
                result = response_body["content"][0]["text"]
            
            # Try to parse as JSON
            import re
            json_match = re.search(r'\[([^\]]+)\]', result)
            if json_match:
                return json.loads(json_match.group())
            
            return []

        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []

    def _parse_sentiment_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI sentiment analysis response"""
        try:
            # Attempt to parse the entire response as JSON
            result = json.loads(response_text)
            # Validate required fields
            if all(key in result for key in ["sentiment_label", "sentiment_score", "confidence"]):
                return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse response as JSON. Attempting substring extraction.")
            # Attempt to extract JSON-like substrings and parse them
            for potential_json in self._extract_json_substrings(response_text):
                try:
                    result = json.loads(potential_json)
                    if all(key in result for key in ["sentiment_label", "sentiment_score", "confidence"]):
                        return result
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.error(f"Unexpected error during sentiment response parsing: {e}")

        # Fallback parsing
        return self._get_fallback_sentiment_analysis(response_text)

    def _extract_json_substrings(self, text: str) -> List[str]:
        """Extract valid JSON objects from text using a streaming JSON parser"""
        from json import JSONDecoder
        decoder = JSONDecoder()
        pos = 0
        json_objects = []
        while pos < len(text):
            try:
                obj, index = decoder.raw_decode(text, pos)
                json_objects.append(obj)
                pos = index
            except ValueError:
                # Move to the next character if no valid JSON is found
                pos += 1
        return json_objects
    def _parse_report_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI report generation response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Failed to parse report response: {e}")

        return {
            "executive_summary": "レポート生成中にエラーが発生しました",
            "sentiment_insights": {},
            "key_findings": [],
            "recommendations": [],
            "trending_topics": [],
            "risk_alerts": []
        }

    def _get_fallback_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback sentiment analysis when AI fails"""
        # Simple keyword-based fallback
        positive_words = ["良い", "素晴らしい", "最高", "おすすめ", "満足", "嬉しい", "楽しい"]
        negative_words = ["悪い", "最悪", "ひどい", "不満", "残念", "怒り", "問題"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = 0.6
        elif negative_count > positive_count:
            sentiment = "negative" 
            score = -0.6
        else:
            sentiment = "neutral"
            score = 0.0

        return {
            "sentiment_label": sentiment,
            "sentiment_score": score,
            "confidence": 0.5,
            "emotions": {},
            "topics": [],
            "keywords_found": [],
            "reasoning": "Fallback analysis used",
            "model_used": "fallback",
            "analysis_version": "1.0"
        }

    def _get_fallback_report(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback report when AI fails"""
        total_posts = len(analyses)
        positive_count = sum(1 for a in analyses if a.get("sentiment_label") == "positive")
        negative_count = sum(1 for a in analyses if a.get("sentiment_label") == "negative")
        
        return {
            "executive_summary": f"分析対象投稿数: {total_posts}件。ポジティブ: {positive_count}件、ネガティブ: {negative_count}件",
            "sentiment_insights": {
                "overall_tone": "中立" if positive_count == negative_count else ("ポジティブ" if positive_count > negative_count else "ネガティブ"),
                "positive_drivers": [],
                "negative_drivers": [],
                "neutral_factors": []
            },
            "key_findings": ["詳細分析が必要です"],
            "recommendations": ["データ収集を継続してください"],
            "trending_topics": [],
            "risk_alerts": []
        }

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding using Amazon Titan or mock response"""
        if self.mock_mode:
            return self._get_mock_embedding(text)
            
        if not self.bedrock_runtime:
            await self.initialize()
        
        try:
            body = json.dumps({
                "inputText": text
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId=settings.EMBEDDING_MODEL,
                body=body
            )
            
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            logger.info(f"Generated {len(embedding)}-dimensional embedding for text")
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        
        for text in texts:
            try:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to generate embedding for text: {e}")
                embeddings.append([])
        
        return embeddings

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            import math
            
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            
            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in embedding1))
            magnitude2 = math.sqrt(sum(a * a for a in embedding2))
            
            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = dot_product / (magnitude1 * magnitude2)
            return similarity
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0

    async def find_similar_posts(
        self, 
        target_text: str, 
        post_texts: List[str], 
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find posts similar to target text using embeddings"""
        
        try:
            # Generate embedding for target text
            target_embedding = await self.generate_embedding(target_text)
            
            # Generate embeddings for all posts
            post_embeddings = await self.generate_batch_embeddings(post_texts)
            
            similar_posts = []
            
            for i, post_embedding in enumerate(post_embeddings):
                if not post_embedding:  # Skip empty embeddings
                    continue
                    
                similarity = self.calculate_similarity(target_embedding, post_embedding)
                
                if similarity >= threshold:
                    similar_posts.append({
                        "index": i,
                        "text": post_texts[i],
                        "similarity": similarity
                    })
            
            # Sort by similarity (descending)
            similar_posts.sort(key=lambda x: x["similarity"], reverse=True)
            
            logger.info(f"Found {len(similar_posts)} similar posts (threshold: {threshold})")
            return similar_posts
            
        except Exception as e:
            logger.error(f"Similar posts search failed: {e}")
            return []

    async def cluster_posts_by_similarity(
        self, 
        post_texts: List[str], 
        similarity_threshold: float = 0.8
    ) -> List[List[int]]:
        """Cluster posts by semantic similarity"""
        
        # Return simple clustering if in mock mode
        if self.mock_mode:
            return self._get_mock_clustering(post_texts, similarity_threshold)
        
        try:
            # Generate embeddings for all posts
            embeddings = await self.generate_batch_embeddings(post_texts)
            
            # Simple clustering based on similarity threshold
            clusters = []
            used_indices = set()
            
            for i, embedding1 in enumerate(embeddings):
                if i in used_indices or not embedding1:
                    continue
                
                cluster = [i]
                used_indices.add(i)
                
                for j, embedding2 in enumerate(embeddings):
                    if j in used_indices or not embedding2 or i == j:
                        continue
                    
                    similarity = self.calculate_similarity(embedding1, embedding2)
                    if similarity >= similarity_threshold:
                        cluster.append(j)
                        used_indices.add(j)
                
                clusters.append(cluster)
            
            logger.info(f"Created {len(clusters)} clusters from {len(post_texts)} posts")
            return clusters
            
        except Exception as e:
            logger.error(f"Post clustering failed: {e}")
            return []

    # Mock implementations for development without AWS Bedrock access
    def _get_mock_sentiment_analysis(self, text: str, keywords: List[str] = None) -> Dict[str, Any]:
        """Generate mock sentiment analysis for development"""
        import random
        import hashlib
        
        # Use text hash for consistent results
        text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        random.seed(text_hash)
        
        # Simple sentiment detection based on keywords
        positive_words = ['良い', '素晴らしい', '最高', 'good', 'great', 'awesome', '好き', 'おすすめ']
        negative_words = ['悪い', '最悪', 'bad', 'terrible', 'awful', '嫌い', 'ダメ']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment_label = "positive"
            sentiment_score = random.uniform(0.3, 0.9)
        elif negative_count > positive_count:
            sentiment_label = "negative"
            sentiment_score = random.uniform(-0.9, -0.3)
        else:
            sentiment_label = "neutral"
            sentiment_score = random.uniform(-0.2, 0.2)
        
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": sentiment_score,
            "confidence": random.uniform(0.7, 0.95),
            "emotions": {
                "joy": random.uniform(0.1, 0.8) if sentiment_label == "positive" else random.uniform(0.0, 0.3),
                "anger": random.uniform(0.1, 0.8) if sentiment_label == "negative" else random.uniform(0.0, 0.3),
                "trust": random.uniform(0.2, 0.7),
                "sadness": random.uniform(0.1, 0.6) if sentiment_label == "negative" else random.uniform(0.0, 0.2),
            },
            "topics": keywords[:2] if keywords else ["一般的な話題"],
            "keywords_found": keywords[:3] if keywords else [],
            "reasoning": f"Mock分析: {sentiment_label}の感情を検出 (開発モード)",
            "_mock_mode": True
        }
    
    def _get_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding vector for development"""
        import hashlib
        import random
        
        # Use text hash for consistent results
        text_hash = hashlib.md5(text.encode()).hexdigest()
        random.seed(int(text_hash[:8], 16))
        
        # Generate 1536-dimension vector (same as Titan)
        vector = [random.uniform(-1, 1) for _ in range(1536)]
        
        # Normalize the vector
        magnitude = sum(x**2 for x in vector) ** 0.5
        return [x / magnitude for x in vector]
    
    def _get_mock_clustering(self, post_texts: List[str], similarity_threshold: float) -> List[List[int]]:
        """Generate mock clustering for development"""
        import random
        
        # Simple random clustering
        clusters = []
        remaining_indices = list(range(len(post_texts)))
        
        while remaining_indices:
            cluster_size = random.randint(1, min(5, len(remaining_indices)))
            cluster = []
            for _ in range(cluster_size):
                if remaining_indices:
                    idx = remaining_indices.pop(random.randint(0, len(remaining_indices) - 1))
                    cluster.append(idx)
            if cluster:
                clusters.append(cluster)
        
        return clusters

    def _get_mock_summary_report(self, analyses: List[Dict], keywords: List[str]) -> Dict[str, Any]:
        """Generate mock summary report for development"""
        import random
        
        total_posts = len(analyses)
        positive_count = sum(1 for a in analyses if a.get('sentiment_label') == 'positive')
        negative_count = sum(1 for a in analyses if a.get('sentiment_label') == 'negative')
        
        return {
            "executive_summary": f"分析した{total_posts}件の投稿のうち、{positive_count}件がポジティブ、{negative_count}件がネガティブでした。(開発モード)",
            "sentiment_insights": {
                "overall_tone": "ポジティブ傾向" if positive_count > negative_count else "ネガティブ傾向" if negative_count > positive_count else "中立的",
                "positive_drivers": random.choice([["品質", "サービス"], ["価格", "利便性"], ["デザイン", "機能"]]),
                "negative_drivers": random.choice([["対応速度", "サポート"], ["価格", "複雑さ"], ["バグ", "不安定性"]]),
                "neutral_factors": ["一般的な使用感", "平均的な評価"]
            },
            "key_findings": [
                f"キーワード「{keywords[0] if keywords else 'サンプル'}」が頻繁に言及されています",
                "感情の変化に季節性が見られます",
                "特定の時間帯にポジティブな投稿が増加しています"
            ],
            "recommendations": [
                "ポジティブなフィードバックを活用した マーケティング戦略の検討",
                "ネガティブな問題への迅速な対応",
                "顧客エンゲージメントの向上"
            ],
            "trending_topics": keywords[:3] if keywords else ["AI", "技術", "サービス"],
            "risk_alerts": [
                "特定の問題に関する不満の増加を注視",
                "競合他社との比較での劣勢"
            ] if negative_count > positive_count else [],
            "_mock_mode": True
        }
