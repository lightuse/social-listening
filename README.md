# 🎯 Social Listening System

> ソーシャルメディア感情分析・監視システム

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![API Status](https://img.shields.io/badge/APIs-Verified-brightgreen.svg)](#api検証結果)

## 📋 目次

- [概要](#概要)
- [主要機能](#主要機能)
- [技術スタック](#技術スタック)
- [🔍 API検証結果](#api検証結果)
- [🧠 AWS Bedrock & Titan 動作確認](#aws-bedrock--titan-動作確認)
- [クイックスタート](#クイックスタート)
- [API仕様](#api仕様)
- [設定](#設定)
- [使用方法](#使用方法)
- [デプロイ](#デプロイ)

## 🎯 概要

Social Listening Systemは、AWS Bedrockの強力なAI機能を活用したソーシャルメディア監視・感情分析プラットフォームです。Twitter、YouTube、Redditからリアルタイムでデータを収集し、高精度な感情分析を提供します。

### 🌟 主な特徴

- **🧠 AWS Bedrock統合**: Amazon Nova Lite/Claude 3による高精度感情分析
- **🔍 多プラットフォーム対応**: Twitter、YouTube、Reddit対応
- **📊 リアルタイム分析**: 継続的なデータ収集と分析
- **📈 包括的レポート**: 詳細な分析レポートとビジュアライゼーション
- **⚡ 高速処理**: 非同期処理による高速データ処理
- **🎨 美しいUI**: 直感的なWebインターフェース
- **🔍 高速検索**: 既存データベースからの即座の検索・フィルタリング
- **🚀 リアルタイム収集**: 最新データの自動収集・分析機能

## 🔍 API検証結果

### ✅ **2025年6月30日 完全検証済み**

| プラットフォーム | API仕様 | 認証方式 | 実装状況 | 動作確認 |
|:---:|:---:|:---:|:---:|:---:|
| **🐦 Twitter** | ✅ API v2 | ✅ Bearer Token | 🟢 完了 | **✅ 検証済み** |
| **📺 YouTube** | ✅ Data API v3 | ✅ API Key | 🟢 完了 | **✅ 検証済み** |
| **🔶 Reddit** | ✅ OAuth2 | ✅ Client Credentials | 🟢 完了 | **✅ 検証済み** |
| **🧠 AWS Bedrock** | ✅ Nova Lite | ✅ IAM Credentials | 🟢 完了 | **✅ 検証済み** |
| **🔤 Amazon Titan** | ✅ Embeddings | ✅ IAM Credentials | 🟢 完了 | **✅ 検証済み** |

#### 📊 検証詳細
- **Twitter API v2**: `search_recent_tweets`、レート制限対応、日本語フィルター実装
- **YouTube Data API v3**: 動画検索→コメント取得、クォータ効率化
- **Reddit API**: OAuth2認証、サブレディット検索、User-Agent設定
- **AWS Bedrock Nova Lite**: 感情分析、信頼度スコア、詳細感情分類
- **Amazon Titan Embeddings**: 1536次元ベクトル、類似度計算、クラスタリング

## 🧠 AWS Bedrock & Titan 動作確認

### ✅ **完全実装・テスト済み機能**

#### 1. **Amazon Nova Lite 感情分析**
```python
# 高精度日本語感情分析
result = await engine.analyze_sentiment(
    "この新しいAI技術は本当に素晴らしい！",
    keywords=["AI", "技術"]
)

# 結果例
{
    "sentiment_label": "positive",     # positive/negative/neutral
    "sentiment_score": 0.8,           # -1.0 〜 1.0
    "confidence": 0.9,                # 信頼度 0.0 〜 1.0
    "emotions": {                     # 詳細感情分析
        "joy": 0.8,
        "trust": 0.7,
        "anticipation": 0.6
    },
    "topics": ["AI・技術"],          # 抽出トピック
    "keywords_found": ["AI", "技術"], # 検出キーワード
    "reasoning": "分析根拠の説明"     # AI による解釈
}
```

#### 2. **Amazon Titan Text Embeddings**
```python
# 高品質テキスト埋め込み生成
embedding = await engine.generate_embedding("人工知能の発展")
# → 1536次元の正規化ベクトル

# 意味的類似度計算
similarity = engine.calculate_similarity(embedding1, embedding2)
# → コサイン類似度 (-1.0 〜 1.0)

# 類似投稿検索
similar_posts = await engine.find_similar_posts(
    target_text="AI技術について",
    post_texts=all_posts,
    threshold=0.7
)
```

#### 3. **包括レポート生成**
```python
# AI駆動の詳細レポート
report = await engine.generate_summary_report(analyses, keywords)

# 生成内容
{
    "executive_summary": "全体要約と主要洞察",
    "sentiment_insights": {
        "overall_tone": "ポジティブ傾向",
        "positive_drivers": ["高品質", "利便性"],
        "negative_drivers": ["価格", "対応速度"],
        "neutral_factors": ["一般的な利用"]
    },
    "key_findings": ["主要発見1", "主要発見2"],
    "recommendations": ["推奨アクション"],
    "trending_topics": ["トレンドトピック"],
    "risk_alerts": ["注意すべきリスク"]
}
```

#### 4. **高度な分析機能**
- **バッチ感情分析**: 大量投稿の並列処理
- **セマンティッククラスタリング**: 意味的グループ化
- **トレンド検出**: 時系列感情変化分析
- **リスクアラート**: ネガティブトレンドの早期発見

### 🔧 **AWS設定要件**

#### Bedrockモデルアクセス
1. [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/home#/modelaccess)
2. **Amazon Nova Lite** を有効化
3. **Amazon Titan Text Embeddings** を有効化

### 🧪 **テスト実行コマンド**
```bash
# 模擬テスト（AWS接続不要）
uv run python test_bedrock_mock.py

# 実際のAWS接続テスト
uv run python test_bedrock_titan.py

# APIテスト（包括的）
uv run pytest tests/ -v

# 特定のテストスイート実行
uv run pytest tests/test_api_robust.py -v

```

---

## 🚀 主要機能

### 1. AI駆動感情分析
- **高精度分析**: AWS Bedrock Amazon Nova Lite による感情分析
- **多次元評価**: ポジティブ/ネガティブ/ニュートラル + 詳細感情
- **日本語特化**: 日本語テキストに最適化された分析
- **信頼度評価**: 分析結果の信頼度スコア

### 2. マルチプラットフォームデータ収集
- **Twitter**: API v2を使用したリアルタイム収集
- **YouTube**: コメント・レビュー分析
- **Reddit**: 投稿・コメント監視
- **自動スケジューリング**: 定期的なデータ収集

### 3. インテリジェントレポート
- **自動レポート生成**: AI による包括的分析レポート
- **トレンド分析**: 時系列での感情変化追跡
- **キーワード抽出**: 重要なキーワード・トピック抽出
- **リスクアラート**: ネガティブトレンドの早期発見

### 4. リアルタイムダッシュボード
- **ライブ監視**: リアルタイム感情分析結果
- **カスタマイズ可能**: フィルタリング・検索機能
- **エクスポート機能**: CSV・JSON形式でのデータ出力
- **アラート機能**: 閾値超過時の通知
- **デュアルモード**: 高速データ検索と新規データ収集の両方に対応
- **自動更新**: 30秒間隔での自動データ更新

## 🛠️ 技術スタック

### AI・機械学習
- **AWS Bedrock**: Amazon Nova Lite (メイン分析エンジン)
- **Amazon Titan**: テキスト埋め込み生成
- **自然言語処理**: 高度なテキスト解析

### バックエンド
- **FastAPI**: 高性能API フレームワーク
- **Python 3.12+**: 最新Python機能活用
- **SQLAlchemy**: ORM・データベース管理
- **Pydantic**: データバリデーション
- **asyncio**: 非同期処理

### データベース・ストレージ
- **SQLite**: 軽量データベース
- **ファイルベースストレージ**: シンプルな構成

### データ収集
- **Twitter API v2**: 最新Twitter API
- **YouTube Data API**: YouTube データ取得
- **Reddit API**: Reddit投稿・コメント取得
- **Tweepy**: Twitter API クライアント
- **httpx**: 高性能HTTP クライアント

### インフラ・DevOps
- **uv**: 高速Pythonパッケージマネージャー
- **Docker**: コンテナ化
- **Docker Compose**: 開発環境管理
- **Uvicorn**: ASGI サーバー

### フロントエンド・UI
- **HTML5**: モダンWebインターフェース
- **CSS3**: レスポンシブデザイン・アニメーション
- **JavaScript ES6+**: 非同期UI処理
- **Chart.js**: データビジュアライゼーション
- **BootstrapCSS**: レスポンシブコンポーネント

## ⚡ クイックスタート

### 前提条件
- Python 3.12+
- Docker & Docker Compose（オプション）
- AWS アカウント（Bedrock アクセス権限）
- Social Media API キー（Twitter、YouTube、Reddit）

### 1. 環境設定

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd social-listening

# 2. 環境変数設定
cp .env.example .env
# .env ファイルを編集してAPIキーを設定

# 3. 依存関係インストール（uvを使用）
uv sync

# 4. データベース初期化
uv run python init_db.py
```

### 2. 開発サーバー起動

```bash
# Docker を使用した開発環境
docker compose build
docker compose up -d

# または、直接起動
uv run uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### 3. アクセス確認

- **メインアプリ**: http://localhost:8002
- **API ドキュメント**: http://localhost:8002/docs
- **ヘルスチェック**: http://localhost:8002/health
- **ダッシュボード**: http://localhost:8002/dashboard
- **レポート**: http://localhost:8002/reports

## 🔑 必要なAPIキーの取得

### AWS Bedrock設定（必須）
1. [AWS Console](https://console.aws.amazon.com/) にログイン
2. IAMでアクセスキーを作成
3. Bedrockサービスへのアクセス権限を付与
4. Amazon Nova Liteモデルへのアクセスを有効化

```bash
# .env ファイルに設定
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
```

### Twitter API設定（オプション）
1. [Twitter Developer Portal](https://developer.twitter.com/) でアプリを作成
2. Bearer Token と API キーを取得

```bash
# .env ファイルに設定
TWITTER_BEARER_TOKEN=your-bearer-token
TWITTER_API_KEY=your-api-key
TWITTER_API_SECRET=your-api-secret
```

### YouTube API設定（オプション）
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. YouTube Data API v3 を有効化
3. APIキーを作成

```bash
# .env ファイルに設定
YOUTUBE_API_KEY=your-youtube-api-key
```

### Reddit API設定（オプション）
1. [Reddit Apps](https://www.reddit.com/prefs/apps) でアプリを作成
2. Client ID と Client Secret を取得

```bash
# .env ファイルに設定
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
```

## 📡 API仕様

### キーワード管理
```http
POST   /api/v1/keywords           # キーワード登録
GET    /api/v1/keywords           # キーワード一覧
DELETE /api/v1/keywords/{id}      # キーワード削除
```

### 分析・データ収集
```http
POST /api/v1/analyze                    # 感情分析開始
GET  /api/v1/analysis/status/{task_id}  # 分析ステータス確認
GET  /api/v1/posts                      # 投稿データ取得
GET  /api/v1/sentiment/summary          # 感情分析サマリー
```

### レポート生成
```http
POST /api/v1/reports     # レポート生成開始
GET  /api/v1/reports     # レポート一覧
GET  /api/v1/reports/{id} # レポート詳細
```

### システム
```http
GET /health                    # ヘルスチェック
GET /dashboard                 # メインダッシュボード
GET /reports                   # レポートページ
GET /api/v1/system/status     # システム状態
```

## ⚙️ 設定

### 必須環境変数

```bash
# AWS Bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# セキュリティキー（以下のコマンドで生成）
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_generated_secret_key

# Twitter API
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# YouTube API
YOUTUBE_API_KEY=your_youtube_api_key

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

## 🎮 使用方法

### 1. キーワード登録

```bash
curl -X POST "http://localhost:8002/api/v1/keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "AI人工知能",
    "category": "テクノロジー",
    "platforms": ["twitter", "youtube"],
    "language": "ja"
  }'
```

### 2. 感情分析開始

```bash
curl -X POST "http://localhost:8002/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI人工知能", "機械学習"],
    "platforms": ["twitter", "youtube"],
    "max_posts_per_platform": 100
  }'
```

### 3. 結果確認

```bash
# 感情分析サマリー取得
curl "http://localhost:8002/api/v1/sentiment/summary?keywords=AI人工知能&days=7"

# 投稿データ取得
curl "http://localhost:8002/api/v1/posts?keyword=AI&sentiment=positive&limit=50"
```

### 4. レポート生成

```bash
curl -X POST "http://localhost:8002/api/v1/reports" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI人工知能"],
    "platforms": ["twitter", "youtube"],
    "date_from": "2024-01-01T00:00:00",
    "date_to": "2024-12-31T23:59:59"
  }'
```

## 🚀 デプロイ

### Docker Compose（推奨）

```bash
# 本番用ビルド
docker compose build

# 本番環境デプロイ
docker compose up -d

# ログ確認
docker compose logs -f
```

### 手動デプロイ

```bash
# 1. 依存関係インストール
uv sync

# 2. データベース初期化
python init_db.py

# 3. 本番サーバー起動
uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4
```

## 📚 使い方ガイド

### 🚀 基本的な使い方

#### 1. ダッシュボードでの監視

1. **アクセス**: ブラウザで http://localhost:8002 にアクセス
2. **リアルタイム監視**: 
   - 総投稿数、感情分析結果を確認
   - 感情分析チャート（ポジティブ/ネガティブ/ニュートラル）を表示
   - プラットフォーム別分析を確認
3. **デュアル検索機能**:
   - **🔍 データ検索**: 既存データベースから即座に検索・表示（高速）
   - **🚀 新規分析開始**: リアルタイムでSNSから新しいデータを収集・分析（数分）
3. **フィルタリング**:
   - キーワード欄で特定の話題を検索
   - プラットフォーム選択（Twitter、YouTube、Reddit）
   - 感情フィルター（ポジティブ/ネガティブ/ニュートラル）

#### 2. トレンドトピックの確認

1. **トレンドトピック表示**:
   - ダッシュボード上部のトレンドトピックセクションを確認
   - 過去24時間〜30日間のデータから選択可能
   - トレンドスコアと活動レベルを表示

2. **詳細分析**:
   - トピックをクリックして詳細情報を確認
   - 時系列トレンド、プラットフォーム分布、関連キーワードを表示

#### 3. キーワード監視の設定

```bash
# APIを使用してキーワードを登録
curl -X POST "http://localhost:8002/api/v1/keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "AI技術",
    "category": "テクノロジー",
    "platforms": ["twitter", "youtube", "reddit"],
    "language": "ja"
  }'
```

#### 4. 感情分析の実行

**方法1: ダッシュボードから（推奨）**
1. http://localhost:8002 にアクセス
2. キーワードを入力（例: "AI技術", "ChatGPT"）
3. プラットフォームを選択（Twitter、YouTube、Reddit）
4. **🚀 新規分析開始** ボタンをクリック
5. 数分待つと結果が表示される

**方法2: APIから**
```bash
# 特定キーワードの分析開始
curl -X POST "http://localhost:8002/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI", "人工知能", "機械学習"],
    "platforms": ["twitter", "youtube", "reddit"],
    "max_posts_per_platform": 100
  }'
```

### 📊 レポート機能の使い方

#### 1. 包括的レポートの生成

1. **レポートページ**: http://localhost:8002/reports にアクセス
2. **カスタムレポート**:
   - 期間を選択（過去7日、30日、カスタム期間）
   - 対象プラットフォームを選択
   - 特定キーワードでフィルタリング

#### 2. 研究用レポートの生成

```bash
# 研究レポート生成（15-20分で完成）
curl -X POST "http://localhost:8002/api/v1/research-report?query=AIエージェントが雇用に与える影響"
```

#### 3. データエクスポート

- **CSV形式**: 分析データをCSVでダウンロード
- **JSON形式**: API経由でJSONデータを取得
- **HTML形式**: 美しい形式のレポートをHTML出力

### 🔍 高度な使い方

#### 1. カスタム分析の実行

```bash
# Python APIクライアント例
import requests

# 感情分析サマリー取得
response = requests.get('http://localhost:8002/api/v1/sentiment/summary?days=7')
data = response.json()

print(f"総投稿数: {data['total_posts']}")
print(f"ポジティブ: {data['sentiment_breakdown']['positive']['percentage']}%")
print(f"ネガティブ: {data['sentiment_breakdown']['negative']['percentage']}%")
```

#### 2. バッチ分析の設定

```bash
# 定期実行用スクリプト
# crontab -e で以下を追加
# 0 */6 * * * curl -X POST "http://localhost:8002/api/v1/analyze" -H "Content-Type: application/json" -d '{"keywords":["トレンドキーワード"], "platforms":["twitter","youtube","reddit"]}'
```

#### 3. アラート設定

```bash
# ネガティブ感情が閾値を超えた場合のアラート
curl -X GET "http://localhost:8002/api/v1/sentiment/summary" | \
  jq '.sentiment_breakdown.negative.percentage > 30'
```

### 📈 実際の使用例

#### ケース1: ブランド監視

```bash
# 1. ブランド名でキーワード登録
curl -X POST "http://localhost:8002/api/v1/keywords" \
  -d '{"term": "あなたのブランド名", "category": "ブランド"}'

# 2. 定期的な感情分析
curl -X POST "http://localhost:8002/api/v1/analyze" \
  -d '{"keywords": ["あなたのブランド名"], "platforms": ["twitter"]}'

# 3. 結果確認
curl "http://localhost:8002/api/v1/sentiment/summary?keywords=あなたのブランド名"
```

#### ケース2: イベント・キャンペーン分析

```bash
# イベント期間中の感情分析
curl -X POST "http://localhost:8002/api/v1/research-report?query=新商品発表会の反応"
```

#### ケース3: 競合他社分析

```bash
# 競合他社のトレンド監視
curl "http://localhost:8002/api/v1/trending-topics?days=7" | \
  jq '.trending_topics[] | select(.topic | contains("競合ブランド名"))'
```

### 🛠️ トラブルシューティング

#### よくある問題と解決方法

1. **APIキーエラー**:
   ```bash
   # .envファイルの設定を確認
   grep -E "(AWS_|TWITTER_|YOUTUBE_|REDDIT_)" .env
   ```

2. **データが表示されない**:
   ```bash
   # データベースの確認
   curl "http://localhost:8002/api/v1/posts?limit=5"
   
   # サンプルデータの追加
   python add_sample_data.py
   ```

3. **分析が遅い**:
   - AWS Bedrockのリージョンを確認
   - 同時リクエスト数を調整
   - キーワード数を減らす

4. **Docker関連**:
   ```bash
   # コンテナの再起動
   docker-compose restart
   
   # ログの確認
   docker-compose logs -f
   
   # 完全な再ビルド
   docker-compose down && docker-compose up --build
   ```

## ⚡ システムパフォーマンス最適化

### 推奨設定

#### 高速検索の活用
- **初回確認**: まず🔍データ検索で既存データを確認
- **必要時のみ**: 🚀新規分析開始は最新データが必要な場合のみ実行
- **効率的なキーワード**: 具体的なキーワード使用で精度向上

#### Twitter API使用量削減
```bash
# Twitter以外のプラットフォームで分析
# プラットフォーム選択で "youtube" または "reddit" を選択
```

#### パフォーマンス監視
```bash
# リアルタイム監視
curl http://localhost:8002/api/v1/system/status

# レスポンス時間確認
time curl "http://localhost:8002/api/v1/posts?limit=10"
```

### 大量データ処理時の推奨事項

1. **バッチサイズ調整**: 一度に処理する件数を50-100件に制限
2. **非同期処理**: 複数キーワードの並列処理活用
3. **定期メンテナンス**: データベースの定期的な最適化
4. **キャッシュ活用**: 頻繁に使用するクエリ結果のキャッシュ
