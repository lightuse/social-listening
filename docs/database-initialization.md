# データベース初期化ガイド

## 概要

Social Listening Systemのデータベース初期化手順とトラブルシューティングガイドです。

## 📋 目次

- [初期化スクリプトについて](#初期化スクリプトについて)
- [Docker環境での初期化方法](#docker環境での初期化方法)
- [トラブルシューティング](#トラブルシューティング)
- [サンプルデータ](#サンプルデータ)

## 初期化スクリプトについて

### `init_db.py`の機能

```python
# 主な機能:
# 1. データディレクトリの作成
# 2. データベーステーブルの作成
# 3. サンプルキーワードの挿入
```

### 作成されるテーブル構造

- **Keywords**: 監視対象キーワード
- **Posts**: 収集されたソーシャルメディア投稿
- **Analysis**: 分析結果
- **Reports**: レポートデータ

## Docker環境での初期化方法

### 🔄 方法1: コンテナ再起動時に自動初期化

`docker-compose.yml`にコマンドを追加:

```yaml
services:
  social-listening:
    # ...existing configuration...
    command: >
      sh -c "uv run python init_db.py && 
             uv run uvicorn main:app --host 0.0.0.0 --port 8002"
```

### 🗂️ 方法2: データベースファイルを削除して再作成

```bash
# 1. コンテナを停止
docker compose down

# 2. データベースファイルを削除
rm -f ./data/social_listening.db

# 3. コンテナを再起動
docker compose up -d

# 4. 初期化スクリプトを実行
docker compose exec social-listening uv run python init_db.py
```

### 🐳 方法3: 実行中のコンテナ内で初期化

```bash
# 実行中のコンテナ内で初期化
docker compose exec social-listening uv run python init_db.py

# または、コンテナ内に入って手動実行
docker compose exec social-listening bash
# コンテナ内で:
uv run python init_db.py
```

### 🔧 方法4: 完全なリセット

```bash
# 1. 全てを停止・削除
docker compose down
docker system prune -f

# 2. データディレクトリをクリア
rm -rf ./data/*

# 3. 再ビルド・起動
docker compose up --build -d

# 4. 初期化実行
docker compose exec social-listening uv run python init_db.py
```

## ✅ 推奨手順

最も確実で安全な方法:

```bash
# 1. 現在の状態を確認
docker compose ps

# 2. コンテナ停止
docker compose down

# 3. データベースファイル削除（バックアップ推奨）
cp ./data/social_listening.db ./data/social_listening.db.backup  # バックアップ
rm -f ./data/social_listening.db

# 4. コンテナ再起動
docker compose up -d

# 5. 初期化実行
docker compose exec social-listening uv run python init_db.py

# 6. 動作確認
curl http://localhost:8002/health
```

## サンプルデータ

### 自動作成されるキーワード

初期化時に以下のサンプルキーワードが作成されます:

| キーワード | カテゴリー | プラットフォーム | 言語 |
|-----------|-----------|----------------|------|
| AI人工知能 | テクノロジー | Twitter, YouTube, Reddit | ja |
| 機械学習 | テクノロジー | Twitter, YouTube, Reddit | ja |
| ChatGPT | AI製品 | Twitter, YouTube, Reddit | ja |
| データサイエンス | テクノロジー | Twitter, YouTube, Reddit | ja |
| Python | プログラミング | Twitter, YouTube, Reddit | ja |

### 追加サンプルデータの生成

API経由でサンプル投稿データを生成:

```bash
# 50件のサンプルデータを生成
curl -X POST "http://localhost:8002/api/v1/reports/generate-sample-data?count=50"

# より多くのデータを生成（テスト用）
curl -X POST "http://localhost:8002/api/v1/reports/generate-sample-data?count=100"
```

**📚 詳細情報**: より詳しいサンプルデータの管理方法については、[サンプルデータ生成ガイド](./sample-data-guide.md)を参照してください。

## トラブルシューティング

### 🚨 よくある問題

#### 1. "Database initialization failed" エラー

**原因**: データベースファイルの権限問題

**解決方法**:
```bash
# データディレクトリの権限を確認
ls -la ./data/

# 権限を修正
sudo chown -R $USER:$USER ./data/
chmod 755 ./data/
```

#### 2. "No such file or directory" エラー

**原因**: データディレクトリが存在しない

**解決方法**:
```bash
# データディレクトリを作成
mkdir -p ./data
```

#### 3. "Port already in use" エラー

**原因**: ポート8002が既に使用されている

**解決方法**:
```bash
# 使用中のプロセスを確認
lsof -i :8002

# または別のポートを使用
# docker-compose.ymlのポート設定を変更
ports:
  - "8003:8002"  # ホスト側のポートを変更
```

#### 4. 環境変数が読み込まれない

**原因**: `.env`ファイルが存在しないか、形式が間違っている

**解決方法**:
```bash
# .envファイルを確認
cat .env

# または環境変数を直接設定
export AWS_REGION=us-east-1
export SECRET_KEY=your-secret-key
```

### 🔍 デバッグ方法

#### ログの確認

```bash
# コンテナのログを確認
docker compose logs social-listening

# リアルタイムでログを監視
docker compose logs -f social-listening
```

#### データベース状態の確認

```bash
# SQLiteデータベースに接続
docker compose exec social-listening sqlite3 /app/data/social_listening.db

# テーブル一覧を表示
.tables

# キーワードテーブルの内容を確認
SELECT * FROM keywords;

# 終了
.quit
```

#### コンテナ内の状態確認

```bash
# コンテナ内に入る
docker compose exec social-listening bash

# Pythonでデータベース接続テスト
python -c "
from core.database import SessionLocal
from models.database import Keyword

db = SessionLocal()
keywords = db.query(Keyword).all()
print(f'Keywords count: {len(keywords)}')
for k in keywords:
    print(f'- {k.term} ({k.category})')
db.close()
"
```

## 🔄 定期的なメンテナンス

### バックアップの作成

```bash
# データベースのバックアップ
cp ./data/social_listening.db ./data/backups/social_listening_$(date +%Y%m%d_%H%M%S).db

# または、SQLダンプを作成
docker compose exec social-listening sqlite3 /app/data/social_listening.db .dump > backup_$(date +%Y%m%d_%H%M%S).sql
```

### パフォーマンス最適化

```bash
# データベースのVACUUM実行
docker compose exec social-listening sqlite3 /app/data/social_listening.db "VACUUM;"

# データベースの整合性チェック
docker compose exec social-listening sqlite3 /app/data/social_listening.db "PRAGMA integrity_check;"
```

## 📚 関連ドキュメント

- [API仕様書](./api-documentation.md)
- [設定ガイド](./configuration-guide.md)
- [デプロイメントガイド](./deployment-guide.md)

## 🆘 サポート

問題が解決しない場合は、以下の情報と共にお問い合わせください:

1. エラーメッセージの全文
2. 実行したコマンドの履歴
3. `docker compose logs`の出力
4. 環境情報（OS、Dockerバージョンなど）

```bash
# 環境情報の取得
echo "=== System Info ==="
uname -a
echo "=== Docker Version ==="
docker --version
docker compose --version
echo "=== Container Status ==="
docker compose ps
```
