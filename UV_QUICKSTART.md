# 🚀 UV Quick Start Guide

このプロジェクトをuvで素早く開始するためのガイドです。

## ⚡ 5分で開始

### 1. uvのインストール（初回のみ）
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. プロジェクトのセットアップ
```bash
# プロジェクトをクローン
git clone <repository-url>
cd social-listening

# 依存関係をインストール（自動で仮想環境も作成）
uv sync --all-extras

# 環境変数をセットアップ
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 3. アプリケーションの起動
```bash
# 開発サーバーを起動
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. テストの実行
```bash
# 全てのテストを実行
uv run pytest

# API接続テストを実行
uv run python test_api_connections.py
```

## 🔧 日常的なコマンド

```bash
# 新しいパッケージを追加
uv add package-name

# 開発用パッケージを追加
uv add --dev pytest-mock

# パッケージを削除
uv remove package-name

# 依存関係を同期
uv sync

# 依存関係を更新
uv lock --upgrade

# コードを実行
uv run python script.py

# テストを実行
uv run pytest tests/

# 仮想環境を削除して再作成
rm -rf .venv && uv sync
```

## 📦 よく使用するパッケージ

```bash
# API開発
uv add fastapi uvicorn pydantic

# データベース
uv add sqlalchemy alembic psycopg2-binary

# HTTP クライアント
uv add httpx aiohttp

# テスト
uv add --dev pytest pytest-asyncio pytest-cov

# コード品質
uv add --dev black isort flake8 mypy

# ソーシャルメディア API
uv add tweepy google-api-python-client praw

# AWS
uv add boto3 botocore
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### uvが見つからない
```bash
# パスを確認
echo $PATH
source ~/.bashrc  # または ~/.zshrc

# 再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 依存関係の競合
```bash
# キャッシュをクリア
uv cache clean

# ロックファイルを再生成
uv lock --upgrade

# 仮想環境を再作成
rm -rf .venv
uv sync
```

#### Python版本の問題
```bash
# 利用可能なPythonを確認
uv python list

# 特定のバージョンをインストール
uv python install 3.12

# プロジェクトのPythonを設定
uv python pin 3.12
```

## 📝 設定ファイル

### pyproject.toml の基本設定
```toml
[project]
name = "social-listening"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "isort>=5.12.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "black>=23.0.0",
]
```

## 🔗 参考リンク

- [UV公式ドキュメント](https://docs.astral.sh/uv/)