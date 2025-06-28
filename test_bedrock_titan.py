#!/usr/bin/env python3
"""
AWS Bedrock & Amazon Titan 動作確認スクリプト
"""

import asyncio
import sys
import os
import json
import boto3
from datetime import datetime

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from services.bedrock_engine import BedrockSentimentEngine

def check_aws_settings():
    """AWS設定の確認"""
    print("=== AWS Bedrock 設定確認 ===")
    
    required_settings = {
        'AWS_REGION': settings.AWS_REGION,
        'AWS_ACCESS_KEY_ID': settings.AWS_ACCESS_KEY_ID,
        'AWS_SECRET_ACCESS_KEY': settings.AWS_SECRET_ACCESS_KEY,
        'DEFAULT_MODEL': settings.DEFAULT_MODEL,
        'EMBEDDING_MODEL': settings.EMBEDDING_MODEL,
    }
    
    # AWS_SESSION_TOKENは条件付きでチェック
    aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
    
    all_set = True
    for key, value in required_settings.items():
        if value and value.strip():
            if 'KEY' in key:
                masked_value = f"{'*' * 10}...{value[-4:]}" if len(value) > 4 else "設定済み"
            else:
                masked_value = value
            print(f"✓ {key}: {masked_value}")
        else:
            print(f"❌ {key}: 未設定")
            all_set = False
    
    # AWS_SESSION_TOKENの確認
    if aws_session_token:
        masked_token = f"{'*' * 10}...{aws_session_token[-10:]}" if len(aws_session_token) > 10 else "設定済み"
        print(f"✓ AWS_SESSION_TOKEN: {masked_token}")
        print(f"ℹ️  一時的な認証情報を使用中（ASIAキー + セッショントークン）")
    else:
        access_key = settings.AWS_ACCESS_KEY_ID
        if access_key.startswith('ASIA'):
            print(f"⚠️  AWS_SESSION_TOKEN: 未設定（ASIAキーには必須）")
            all_set = False
        else:
            print(f"ℹ️  AWS_SESSION_TOKEN: 不要（永続的IAMキー使用）")
    
    return all_set

async def test_bedrock_connection():
    """Bedrockの基本接続テスト"""
    print("\n=== AWS Bedrock 接続テスト ===")
    
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
            print("ℹ️  一時的な認証情報（セッショントークン）を使用")
        else:
            print("ℹ️  永続的なIAM認証情報を使用")
        
        # Bedrockクライアントの作成
        bedrock_client = boto3.client("bedrock", **auth_kwargs)
        
        print("✓ Bedrockクライアント作成成功")
        
        # 利用可能なモデル一覧を取得
        response = bedrock_client.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        print(f"✓ 利用可能なモデル数: {len(models)}")
        
        # Amazon Nova Liteが利用可能かチェック
        nova_models = [m for m in models if 'nova' in m.get('modelId', '').lower()]
        titan_models = [m for m in models if 'titan' in m.get('modelId', '').lower()]
        
        print(f"✓ Amazon Nova モデル: {len(nova_models)}個")
        for model in nova_models[:3]:  # 最初の3つを表示
            print(f"  - {model.get('modelId')}")
            
        print(f"✓ Amazon Titan モデル: {len(titan_models)}個")
        for model in titan_models[:3]:  # 最初の3つを表示
            print(f"  - {model.get('modelId')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock接続エラー: {e}")
        return False

async def test_nova_lite_sentiment():
    """Amazon Nova Liteで感情分析テスト"""
    print("\n=== Amazon Nova Lite 感情分析テスト ===")
    
    try:
        engine = BedrockSentimentEngine()
        await engine.initialize()
        
        # テスト用テキスト
        test_texts = [
            "この新しいAI技術は本当に素晴らしい！期待以上の性能です。",
            "サービスの対応が遅くて困っています。改善してほしい。",
            "今日は普通の一日でした。特に何もありませんでした。"
        ]
        
        print("テストケース:")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. {text}")
        
        print("\n分析結果:")
        for i, text in enumerate(test_texts, 1):
            try:
                result = await engine.analyze_sentiment(text, keywords=["AI", "技術", "サービス"])
                
                print(f"\n{i}. テキスト: {text[:50]}...")
                print(f"   感情: {result.get('sentiment_label')} (スコア: {result.get('sentiment_score', 0):.2f})")
                print(f"   確信度: {result.get('confidence', 0):.2f}")
                print(f"   主要感情: {list(result.get('emotions', {}).keys())[:3]}")
                print(f"   トピック: {result.get('topics', [])[:2]}")
                
            except Exception as e:
                print(f"   ❌ 分析エラー: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Nova Lite テストエラー: {e}")
        return False

async def test_titan_embeddings():
    """Amazon Titan Text Embeddings テスト"""
    print("\n=== Amazon Titan Embeddings テスト ===")
    
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
        
        bedrock_runtime = boto3.client("bedrock-runtime", **auth_kwargs)
        
        # テスト用テキスト
        test_texts = [
            "人工知能とAI技術の発展",
            "機械学習とディープラーニング",
            "今日の天気は晴れです"
        ]
        
        print("テキスト埋め込み生成:")
        embeddings = []
        
        for i, text in enumerate(test_texts, 1):
            try:
                body = json.dumps({
                    "inputText": text
                })
                
                response = bedrock_runtime.invoke_model(
                    modelId=settings.EMBEDDING_MODEL,
                    body=body
                )
                
                response_body = json.loads(response["body"].read())
                embedding = response_body.get("embedding", [])
                embeddings.append(embedding)
                
                print(f"  {i}. '{text}' → {len(embedding)}次元ベクトル")
                if len(embedding) >= 2:
                    print(f"     サンプル値: [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")
                elif len(embedding) == 1:
                    print(f"     サンプル値: [{embedding[0]:.4f}]")
                else:
                    print(f"     サンプル値: 空のベクトル")
                
            except Exception as e:
                print(f"  ❌ エラー: {e}")
        
        # 類似度計算（簡単なコサイン類似度）
        if len(embeddings) >= 2:
            print("\n類似度分析:")
            similarity = calculate_similarity(embeddings[0], embeddings[1])
            print(f"  テキスト1とテキスト2の類似度: {similarity:.4f}")
            
            similarity = calculate_similarity(embeddings[0], embeddings[2])
            print(f"  テキスト1とテキスト3の類似度: {similarity:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Titan Embeddings テストエラー: {e}")
        return False

def calculate_similarity(vec1, vec2):
    """コサイン類似度計算"""
    import math
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    return dot_product / (magnitude1 * magnitude2)

async def test_bedrock_report_generation():
    """Bedrockレポート生成テスト"""
    print("\n=== Bedrock レポート生成テスト ===")
    
    try:
        engine = BedrockSentimentEngine()
        await engine.initialize()
        
        # サンプル分析データ
        sample_analyses = [
            {
                "sentiment_label": "positive",
                "sentiment_score": 0.8,
                "confidence": 0.9,
                "emotions": {"joy": 0.8, "trust": 0.7},
                "topics": ["AI技術", "イノベーション"]
            },
            {
                "sentiment_label": "negative", 
                "sentiment_score": -0.6,
                "confidence": 0.8,
                "emotions": {"anger": 0.7, "sadness": 0.5},
                "topics": ["サービス不満", "対応遅延"]
            },
            {
                "sentiment_label": "neutral",
                "sentiment_score": 0.1,
                "confidence": 0.7,
                "emotions": {"trust": 0.4},
                "topics": ["日常", "情報共有"]
            }
        ]
        
        print("サンプルデータでレポート生成中...")
        report = await engine.generate_summary_report(sample_analyses, keywords=["AI", "技術"])
        
        print("✓ レポート生成成功")
        print(f"  要約: {report.get('executive_summary', 'N/A')[:100]}...")
        print(f"  主要発見: {len(report.get('key_findings', []))}件")
        print(f"  推奨事項: {len(report.get('recommendations', []))}件")
        
        return True
        
    except Exception as e:
        print(f"❌ レポート生成エラー: {e}")
        return False

def check_bedrock_models():
    """Bedrockモデルの詳細確認"""
    print("\n=== Bedrock モデル詳細確認 ===")
    
    print(f"設定されているモデル:")
    print(f"  メイン分析モデル: {settings.DEFAULT_MODEL}")
    print(f"  埋め込みモデル: {settings.EMBEDDING_MODEL}")
    
    # 推奨設定
    print(f"\n推奨設定:")
    print(f"  Amazon Nova Lite: amazon.nova-lite-v1:0")
    print(f"  Amazon Titan Embeddings: amazon.titan-embed-text-v1")
    print(f"  Amazon Claude 3 Haiku: anthropic.claude-3-haiku-20240307-v1:0")

async def main():
    """メイン実行関数"""
    print("🔍 AWS Bedrock & Amazon Titan 動作確認")
    print(f"確認時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 設定確認
    settings_ok = check_aws_settings()
    
    if not settings_ok:
        print("\n⚠️  AWS設定が不完全です。.envファイルを確認してください。")
        return
    
    # 詳細なモデル情報
    check_bedrock_models()
    
    # 各テスト実行
    results = {}
    
    # Bedrock基本接続
    results['connection'] = await test_bedrock_connection()
    
    # Nova Lite感情分析
    results['nova_sentiment'] = await test_nova_lite_sentiment()
    
    # Titan Embeddings
    results['titan_embeddings'] = await test_titan_embeddings()
    
    # レポート生成
    results['report_generation'] = await test_bedrock_report_generation()
    
    # 結果サマリー
    print("\n" + "="*60)
    print("=== テスト結果サマリー ===")
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for test_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        test_display = test_name.replace('_', ' ').title()
        print(f"{test_display}: {status}")
    
    print(f"\n成功: {success_count}/{total_count} テスト")
    
    if success_count == total_count:
        print("🎉 AWS Bedrock & Amazon Titan は正常に動作しています！")
    elif success_count > 0:
        print("⚠️  一部のテストで問題があります。設定やアクセス権限を確認してください。")
    else:
        print("❌ すべてのテストが失敗しました。AWS設定とBedrockアクセス権限を確認してください。")
    
    print("\n📚 参考情報:")
    print("  - AWS Bedrock コンソール: https://console.aws.amazon.com/bedrock/")
    print("  - Model access設定でNova LiteとTitanを有効化")
    print("  - IAMポリシーでbedrock:InvokeModel権限を付与")

if __name__ == "__main__":
    asyncio.run(main())
