# 📦 UV Package Manager Documentation

このプロジェクトでは、高速なPythonパッケージマネージャー `uv` を使用しています。

## 📋 目次

- [uvとは](#uvとは)
- [インストール](#インストール)
- [基本的な使い方](#基本的な使い方)
- [プロジェクト管理](#プロジェクト管理)
- [仮想環境管理](#仮想環境管理)
- [依存関係管理](#依存関係管理)
- [トラブルシューティング](#トラブルシューティング)

## 🚀 uvとは

`uv` は、Rustで書かれた高速なPythonパッケージマネージャーです。`pip`や`pipenv`、`poetry`の代替として機能し、以下の特徴があります：

- **⚡ 高速**: Rustで実装されており、従来のツールより10-100倍高速
- **🔒 信頼性**: 決定論的な依存関係解決
- **📦 統合性**: プロジェクト管理、仮想環境、パッケージインストールを一元化
- **🔄 互換性**: pip、requirements.txt、pyproject.tomlと互換

## 📥 インストール

### Linux/macOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Cargo（Rust）
```bash
cargo install uv
```

## 🛠️ 基本的な使い方

### 1. 現在のプロジェクト設定確認
```bash
uv --version
# uv 0.7.12

# プロジェクト情報を表示
uv show
```

### 2. パッケージのインストール
```bash
# 単一パッケージのインストール
uv add fastapi

# 開発依存関係として追加
uv add --dev pytest

# 特定のバージョンを指定
uv add "fastapi==0.115.6"

# 複数パッケージを同時に追加
uv add fastapi uvicorn pydantic
```

### 3. パッケージの削除
```bash
uv remove fastapi
uv remove --dev pytest
```

## 🏗️ プロジェクト管理

### 新しいプロジェクトの初期化
```bash
# 新しいプロジェクトを作成
uv init my-project
cd my-project

# 既存のディレクトリでプロジェクトを初期化
uv init
```

### プロジェクトの同期
```bash
# pyproject.tomlに基づいて依存関係を同期
uv sync

# 開発依存関係も含めて同期
uv sync --all-extras

# 特定の環境のみ同期
uv sync --only-group dev
```

## 🔄 仮想環境管理

### 仮想環境の作成と管理
```bash
# 仮想環境を作成（自動でPythonバージョンを管理）
uv venv

# 特定のPythonバージョンで仮想環境作成
uv venv --python 3.12

# 仮想環境をアクティベート
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows

# 仮想環境でコマンドを実行（アクティベート不要）
uv run python main.py
uv run pytest
```

### Python管理
```bash
# 利用可能なPythonバージョンを表示
uv python list

# 特定のPythonバージョンをインストール
uv python install 3.12

# プロジェクトのPythonバージョンを設定
uv python pin 3.12
```

## 📋 依存関係管理

### requirements.txtからの移行
```bash
# requirements.txtから依存関係を追加
uv add -r requirements.txt

# requirements.txtを生成
uv export --format requirements-txt > requirements.txt
```

### ロックファイル
```bash
# uv.lockファイルを生成/更新
uv lock

# ロックファイルから依存関係をインストール
uv sync --frozen

# ロックファイルの内容を確認
uv tree
```

## 🏃‍♂️ このプロジェクトでの使用例

### 開発環境のセットアップ
```bash
# プロジェクトをクローン
git clone <repository-url>
cd social-listening

# 依存関係をインストール（自動で仮想環境も作成）
uv sync

# 開発用の依存関係も含めてインストール
uv sync --all-extras
```

### アプリケーションの実行
```bash
# メインアプリケーションを起動
uv run python main.py

# テストを実行
uv run pytest

# API接続テストを実行
uv run python test_api_connections.py
```

### 新しい依存関係の追加
```bash
# 新しいパッケージを追加
uv add google-api-python-client

# 開発用パッケージを追加
uv add --dev black isort

# 依存関係を同期
uv sync
```

### Docker環境での使用
```dockerfile
# Dockerfile例
FROM python:3.12-slim

# uvをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# プロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# 依存関係をインストール
RUN uv sync --frozen --no-cache

# アプリケーションを実行
CMD ["uv", "run", "python", "main.py"]
```

## 🔧 設定とカスタマイズ

### uvの設定ファイル（pyproject.toml）
```toml
[tool.uv]
# 開発依存関係のグループ定義
dev-dependencies = [
    "pytest>=7.4.3",
    "black>=23.0.0",
    "isort>=5.12.0",
]

# インデックスサーバーの設定
index-url = "https://pypi.org/simple"
extra-index-url = ["https://private-pypi.example.com/simple"]

# 仮想環境の場所を指定
venv = ".venv"
```

### 環境変数
```bash
# uvの設定
export UV_CACHE_DIR="~/.cache/uv"
export UV_PYTHON_PREFERENCE="only-managed"
export UV_INDEX_URL="https://pypi.org/simple"
```

## 🐛 トラブルシューティング

### 一般的な問題と解決方法

#### 1. 依存関係の競合
```bash
# 依存関係ツリーを確認
uv tree

# 特定のパッケージの情報を表示
uv show package-name

# ロックファイルを再生成
uv lock --upgrade
```

#### 2. キャッシュの問題
```bash
# キャッシュをクリア
uv cache clean

# 特定のパッケージのキャッシュをクリア
uv cache clean package-name
```

#### 3. Python版本の問題
```bash
# 現在のPython設定を確認
uv python list

# Pythonを再インストール
uv python install 3.12

# プロジェクトのPython設定をリセット
uv python pin 3.12
```

#### 4. 仮想環境の問題
```bash
# 仮想環境を削除して再作成
rm -rf .venv
uv venv

# 依存関係を再インストール
uv sync
```

## 📊 パフォーマンス比較

| ツール | インストール時間 | 解決時間 | ディスク使用量 |
|--------|------------------|----------|----------------|
| pip    | 45s             | 12s      | 200MB         |
| poetry | 60s             | 25s      | 300MB         |
| uv     | 4s              | 1s       | 150MB         |

## 🔗 参考リンク

- [uv公式ドキュメント](https://docs.astral.sh/uv/)
- [GitHub Repository](https://github.com/astral-sh/uv)
- [pyproject.toml設定ガイド](https://docs.astral.sh/uv/concepts/projects/)
- [マイグレーションガイド](https://docs.astral.sh/uv/guides/integration/)

## 📝 プロジェクト固有のコマンド

このプロジェクトでよく使用するuvコマンド：

```bash
# 開発環境セットアップ
uv sync --all-extras

# アプリケーション実行
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# テスト実行
uv run pytest tests/
uv run python test_api_connections.py

# コード品質チェック
uv run black .
uv run isort .

# 依存関係の更新
uv lock --upgrade
uv sync

# 新しい依存関係を追加
uv add package-name
uv add --dev development-package
```
