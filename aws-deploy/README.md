# AWS デプロイメントガイド

## 前提条件

1. AWS CLI がインストールされていること
2. AWS アカウントに適切な権限があること
3. Docker がインストールされていること

## デプロイ手順

### 1. AWS CLI の設定

```bash
# AWS CLI のインストール
bash aws-deploy/setup.sh

# AWS 認証情報の設定
aws configure
```

### 2. IAM ロールとポリシーの作成

```bash
chmod +x aws-deploy/setup-iam.sh
bash aws-deploy/setup-iam.sh
```

### 3. 環境変数の設定

```bash
chmod +x aws-deploy/setup-env.sh
bash aws-deploy/setup-env.sh
```

### 4. アプリケーションのデプロイ

```bash
chmod +x aws-deploy/deploy.sh
bash aws-deploy/deploy.sh
```

## 本番環境での推奨事項

### 1. データベース
- SQLite の代わりに Amazon RDS (PostgreSQL/MySQL) を使用
- データの永続化とスケーラビリティのため

### 2. Redis
- Amazon ElastiCache for Redis を使用
- セッション管理やキャッシュのため

### 3. ロードバランサー
- Application Load Balancer (ALB) を使用
- SSL/TLS 証明書の設定

### 4. ドメイン
- Route 53 でドメインを管理
- CloudFront でCDNを設定

### 5. 監視
- CloudWatch でログとメトリクスを監視
- AWS X-Ray でトレーシング

## 環境変数

以下の環境変数を AWS Systems Manager Parameter Store に設定してください：

- `/social-listening/database-url`: データベース接続文字列
- `/social-listening/twitter-api-key`: Twitter API キー
- `/social-listening/twitter-api-secret`: Twitter API シークレット
- `/social-listening/twitter-access-token`: Twitter アクセストークン
- `/social-listening/twitter-access-token-secret`: Twitter アクセストークンシークレット

## コスト見積もり

### 最小構成（月額）
- ECS Fargate: $15-30
- Application Load Balancer: $16
- CloudWatch Logs: $5
- Parameter Store: $0.05/パラメータ
- **合計: 約 $36-51/月**

### 本番推奨構成（月額）
- ECS Fargate (複数インスタンス): $60-120
- RDS (db.t3.micro): $15
- ElastiCache (cache.t3.micro): $12
- Application Load Balancer: $16
- CloudWatch: $10
- **合計: 約 $113-173/月**

## トラブルシューティング

### ECS タスクが起動しない場合
1. CloudWatch ログを確認
2. タスク定義の CPU/メモリ設定を確認
3. セキュリティグループの設定を確認

### アプリケーションにアクセスできない場合
1. セキュリティグループでポート 8002 が開いているか確認
2. タスクのパブリック IP を確認
3. ヘルスチェックが通っているか確認

### 環境変数が読み込まれない場合
1. Parameter Store の値を確認
2. IAM ロールの権限を確認
3. タスク定義の secrets セクションを確認

## 更新手順

```bash
# 新しいイメージをビルドしてプッシュ
docker build -t social-listening-app:latest -f Dockerfile.prod .
docker tag social-listening-app:latest $ECR_URI:latest
docker push $ECR_URI:latest

# サービスを更新
aws ecs update-service --cluster social-listening-cluster --service social-listening-service --force-new-deployment
```
