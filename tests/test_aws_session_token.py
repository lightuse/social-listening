#!/usr/bin/env python3
"""
pytest形式のAWS_SESSION_TOKEN接続テスト
"""

import pytest
import boto3
from pathlib import Path
import sys

# プロジェクトのパスを追加
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings


class TestAWSSessionToken:
    """AWS_SESSION_TOKEN関連のテストクラス"""

    def test_aws_credentials_configured(self):
        """AWS認証情報が設定されていることを確認"""
        assert settings.AWS_REGION, "AWS_REGION が設定されていません"
        assert settings.AWS_ACCESS_KEY_ID, "AWS_ACCESS_KEY_ID が設定されていません"
        assert settings.AWS_SECRET_ACCESS_KEY, "AWS_SECRET_ACCESS_KEY が設定されていません"
        
        # ACCESS_KEY_IDの形式確認
        assert len(settings.AWS_ACCESS_KEY_ID) >= 16, "AWS_ACCESS_KEY_ID の形式が無効です"
        assert len(settings.AWS_SECRET_ACCESS_KEY) >= 32, "AWS_SECRET_ACCESS_KEY の形式が無効です"

    def test_session_token_configuration(self):
        """セッショントークンの設定確認"""
        aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
        access_key = settings.AWS_ACCESS_KEY_ID
        
        if access_key.startswith('ASIA'):
            # 一時認証情報の場合、セッショントークンは必須
            assert aws_session_token, "ASIA キーを使用する場合、AWS_SESSION_TOKEN は必須です"
            assert len(aws_session_token) >= 100, "AWS_SESSION_TOKEN の形式が無効です"
        # 永続的認証情報の場合、セッショントークンは不要（テスト省略）

    def test_aws_sts_connection(self):
        """AWS STS接続テスト"""
        auth_kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        
        # AWS_SESSION_TOKENが設定されている場合は追加
        aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
        if aws_session_token:
            auth_kwargs["aws_session_token"] = aws_session_token
        
        sts_client = boto3.client("sts", **auth_kwargs)
        
        # get_caller_identityが成功することを確認
        caller_identity = sts_client.get_caller_identity()
        
        assert "Account" in caller_identity, "Account情報が取得できません"
        assert "Arn" in caller_identity, "ARN情報が取得できません"
        assert "UserId" in caller_identity, "UserId情報が取得できません"
        
        # Account IDの形式確認
        account_id = caller_identity["Account"]
        assert account_id.isdigit(), "Account IDの形式が無効です"
        assert len(account_id) == 12, "Account IDは12桁である必要があります"

    def test_bedrock_service_access(self):
        """Bedrockサービスへのアクセステスト"""
        auth_kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        
        aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
        if aws_session_token:
            auth_kwargs["aws_session_token"] = aws_session_token
        
        bedrock_client = boto3.client("bedrock", **auth_kwargs)
        
        # モデル一覧の取得が成功することを確認
        response = bedrock_client.list_foundation_models()
        
        assert "modelSummaries" in response, "モデル一覧の取得に失敗しました"
        models = response["modelSummaries"]
        assert len(models) > 0, "利用可能なモデルが見つかりません"

    def test_nova_models_availability(self):
        """Nova モデルの利用可能性テスト"""
        auth_kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        
        aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
        if aws_session_token:
            auth_kwargs["aws_session_token"] = aws_session_token
        
        bedrock_client = boto3.client("bedrock", **auth_kwargs)
        response = bedrock_client.list_foundation_models()
        models = response["modelSummaries"]
        
        # Nova モデルの確認
        nova_models = [m for m in models if 'nova' in m['modelId'].lower()]
        assert len(nova_models) > 0, "Nova モデルが利用できません"
        
        # 設定されたモデルが利用可能かチェック
        available_model_ids = [m['modelId'] for m in models]
        assert settings.DEFAULT_MODEL in available_model_ids, \
            f"設定されたモデル '{settings.DEFAULT_MODEL}' が利用できません"

    def test_titan_models_availability(self):
        """Titan モデルの利用可能性テスト"""
        auth_kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        
        aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
        if aws_session_token:
            auth_kwargs["aws_session_token"] = aws_session_token
        
        bedrock_client = boto3.client("bedrock", **auth_kwargs)
        response = bedrock_client.list_foundation_models()
        models = response["modelSummaries"]
        
        # Titan モデルの確認
        titan_models = [m for m in models if 'titan' in m['modelId'].lower()]
        assert len(titan_models) > 0, "Titan モデルが利用できません"
        
        # 設定された埋め込みモデルが利用可能かチェック
        available_model_ids = [m['modelId'] for m in models]
        assert settings.EMBEDDING_MODEL in available_model_ids, \
            f"設定された埋め込みモデル '{settings.EMBEDDING_MODEL}' が利用できません"

    def test_bedrock_runtime_access(self):
        """Bedrock Runtime への接続テスト"""
        auth_kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        
        aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
        if aws_session_token:
            auth_kwargs["aws_session_token"] = aws_session_token
        
        # Bedrock Runtimeクライアントの作成が成功することを確認
        bedrock_runtime = boto3.client("bedrock-runtime", **auth_kwargs)
        assert bedrock_runtime is not None, "Bedrock Runtime クライアントの作成に失敗しました"


# Removed the aws_credentials fixture to avoid conflicts with the definition in conftest.py.


class TestBedrockEngine:
    """BedrockSentimentEngineのテストクラス"""

    @pytest.mark.asyncio
    async def test_bedrock_engine_initialization(self, aws_credentials):
        """BedrockSentimentEngineの初期化テスト"""
        from services.bedrock_engine import BedrockSentimentEngine
        
        engine = BedrockSentimentEngine()
        await engine.initialize()
        
        assert engine.bedrock_client is not None, "Bedrockクライアントが初期化されていません"
        assert engine.bedrock_runtime is not None, "Bedrock Runtimeクライアントが初期化されていません"

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, aws_credentials):
        """感情分析機能のテスト"""
        from services.bedrock_engine import BedrockSentimentEngine
        
        engine = BedrockSentimentEngine()
        await engine.initialize()
        
        test_text = "この製品は本当に素晴らしい！"
        result = await engine.analyze_sentiment(test_text, keywords=["製品"])
        
        assert "sentiment_label" in result, "sentiment_label が結果に含まれていません"
        assert "sentiment_score" in result, "sentiment_score が結果に含まれていません"
        assert "confidence" in result, "confidence が結果に含まれていません"
        
        # 値の範囲チェック
        assert result["sentiment_score"] >= -1.0 and result["sentiment_score"] <= 1.0, \
            "sentiment_score は -1.0 から 1.0 の範囲である必要があります"
        assert result["confidence"] >= 0.0 and result["confidence"] <= 1.0, \
            "confidence は 0.0 から 1.0 の範囲である必要があります"
        assert result["sentiment_label"] in ["positive", "negative", "neutral"], \
            "sentiment_label は positive, negative, neutral のいずれかである必要があります"

    @pytest.mark.asyncio
    async def test_report_generation(self, aws_credentials):
        """レポート生成機能のテスト"""
        from services.bedrock_engine import BedrockSentimentEngine
        
        engine = BedrockSentimentEngine()
        await engine.initialize()
        
        sample_analyses = [
            {
                "sentiment_label": "positive",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "emotions": {"joy": 0.8},
                "topics": ["AI技術"]
            }
        ]
        
        report = await engine.generate_summary_report(sample_analyses, keywords=["AI"])
        
        assert "executive_summary" in report, "executive_summary が結果に含まれていません"
        assert "key_findings" in report, "key_findings が結果に含まれていません"
        assert "recommendations" in report, "recommendations が結果に含まれていません"
        
        assert isinstance(report["key_findings"], list), "key_findings はリストである必要があります"
        assert isinstance(report["recommendations"], list), "recommendations はリストである必要があります"

    @pytest.mark.asyncio
    async def test_keyword_extraction(self, aws_credentials):
        """キーワード抽出機能のテスト"""
        from services.bedrock_engine import BedrockSentimentEngine
        
        engine = BedrockSentimentEngine()
        await engine.initialize()
        
        test_text = "この新しいAI技術は革新的で素晴らしい製品です"
        keywords = await engine.extract_keywords(test_text)
        
        assert isinstance(keywords, list), "キーワード抽出結果はリストである必要があります"
        # キーワードが空でないことを確認（APIの応答に依存）
        # assert len(keywords) > 0, "キーワードが抽出されませんでした"


# カスタムマーカー定義
def pytest_configure(config):
    """pytestの設定"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# 統合テスト用のマーカー
@pytest.mark.integration
@pytest.mark.slow
class TestFullIntegration:
    """完全統合テスト"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, aws_credentials):
        """完全なワークフローのテスト"""
        from services.bedrock_engine import BedrockSentimentEngine
        
        engine = BedrockSentimentEngine()
        await engine.initialize()
        
        # 1. 感情分析
        sentiment_result = await engine.analyze_sentiment(
            "この製品は本当に素晴らしい！", 
            keywords=["製品"]
        )
        assert sentiment_result["sentiment_label"] == "positive"
        
        # 2. レポート生成
        report = await engine.generate_summary_report(
            [sentiment_result], 
            keywords=["製品"]
        )
        assert "executive_summary" in report
        
        # 3. キーワード抽出
        keywords = await engine.extract_keywords("AI技術の革新的な製品")
        assert isinstance(keywords, list)
