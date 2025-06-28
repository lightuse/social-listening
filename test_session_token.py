#!/usr/bin/env python3
"""
AWS_SESSION_TOKEN 接続確認テスト
"""

import os
import sys
import boto3
from pathlib import Path

# プロジェクトのパスを追加
sys.path.append(str(Path(__file__).parent))

from core.config import settings

def test_aws_session_token():
    """AWS_SESSION_TOKEN を使った接続テスト"""
    print("🔐 AWS_SESSION_TOKEN 接続テスト")
    print("=" * 50)
    
    # 設定確認
    print("📋 現在の設定:")
    print(f"  AWS_REGION: {settings.AWS_REGION}")
    print(f"  AWS_ACCESS_KEY_ID: {'*' * 8}...{settings.AWS_ACCESS_KEY_ID[-4:]}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'設定済み' if settings.AWS_SECRET_ACCESS_KEY else '未設定'}")
    
    # AWS_SESSION_TOKENの確認
    aws_session_token = getattr(settings, 'AWS_SESSION_TOKEN', '')
    if aws_session_token:
        print(f"  AWS_SESSION_TOKEN: {'*' * 8}...{aws_session_token[-10:]}")
        print("  🔄 一時的な認証情報を使用")
    else:
        print("  AWS_SESSION_TOKEN: 未設定")
        print("  🔒 永続的なIAM認証情報を使用")
    
    print("\n🔍 AWS接続テスト:")
    
    try:
        # AWS認証情報の準備
        auth_kwargs = {
            "region_name": settings.AWS_REGION,
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        }
        
        # AWS_SESSION_TOKENが設定されている場合は追加
        if aws_session_token:
            auth_kwargs["aws_session_token"] = aws_session_token
        
        # STSで認証情報確認
        sts_client = boto3.client("sts", **auth_kwargs)
        caller_identity = sts_client.get_caller_identity()
        
        print("✅ AWS認証成功!")
        print(f"  Account: {caller_identity.get('Account', 'N/A')}")
        print(f"  User ARN: {caller_identity.get('Arn', 'N/A')}")
        print(f"  User ID: {caller_identity.get('UserId', 'N/A')}")
        
        # Bedrockアクセステスト
        print("\n🧠 Bedrock アクセステスト:")
        bedrock_client = boto3.client("bedrock", **auth_kwargs)
        
        # 簡単なリクエスト
        models = bedrock_client.list_foundation_models()
        model_count = len(models.get('modelSummaries', []))
        
        print(f"✅ Bedrock接続成功! 利用可能モデル: {model_count}個")
        
        # Nova/Titanモデルの確認
        nova_models = [m for m in models['modelSummaries'] if 'nova' in m['modelId'].lower()]
        titan_models = [m for m in models['modelSummaries'] if 'titan' in m['modelId'].lower()]
        
        print(f"  🌟 Nova モデル: {len(nova_models)}個")
        print(f"  🔤 Titan モデル: {len(titan_models)}個")
        
        if nova_models:
            print(f"  📝 設定モデル '{settings.DEFAULT_MODEL}' 利用可能: {'✅' if settings.DEFAULT_MODEL in [m['modelId'] for m in models['modelSummaries']] else '❌'}")
        
        if titan_models:
            print(f"  📝 埋め込みモデル '{settings.EMBEDDING_MODEL}' 利用可能: {'✅' if settings.EMBEDDING_MODEL in [m['modelId'] for m in models['modelSummaries']] else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS接続エラー: {e}")
        
        # エラーの種類に応じたアドバイス
        error_str = str(e)
        if "UnrecognizedClientException" in error_str:
            print("\n💡 解決方法:")
            print("  - AWS_SESSION_TOKEN が正しく設定されているか確認")
            print("  - 一時認証情報の有効期限が切れていないか確認")
            print("  - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN の組み合わせが正しいか確認")
        elif "AccessDenied" in error_str:
            print("\n💡 解決方法:")
            print("  - IAMポリシーでBedrock権限が付与されているか確認")
            print("  - AmazonBedrockFullAccess ポリシーの付与を確認")
        elif "InvalidUserID.NotFound" in error_str:
            print("\n💡 解決方法:")
            print("  - AWS_ACCESS_KEY_ID が正しいか確認")
            print("  - 一時認証情報が有効か確認")
        
        return False

def main():
    """メイン実行関数"""
    success = test_aws_session_token()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 AWS_SESSION_TOKEN 設定は正常に動作しています!")
        print("\n次のステップ:")
        print("  1. Bedrock感情分析テスト実行")
        print("  2. Titan埋め込みテスト実行")
        print("  3. アプリケーション本格運用")
    else:
        print("❌ AWS_SESSION_TOKEN に問題があります")
        print("\n推奨アクション:")
        print("  1. .envファイルのAWS設定を確認")
        print("  2. 一時認証情報の有効期限確認")
        print("  3. IAMポリシーの権限確認")

if __name__ == "__main__":
    main()
