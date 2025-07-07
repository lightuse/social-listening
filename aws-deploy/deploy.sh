#!/bin/bash

# 設定
AWS_REGION="us-east-1"
ECR_REPOSITORY="social-listening-app"
ECS_CLUSTER="social-listening-cluster"
ECS_SERVICE="social-listening-service"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Starting deployment process..."

# 1. ECR リポジトリの作成
echo "Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION || \
aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION

# 2. Docker イメージのビルドとプッシュ
echo "Building and pushing Docker image..."
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

# ECR ログイン
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# イメージビルド
docker build -t $ECR_REPOSITORY:latest -f Dockerfile.prod .

# イメージにタグ付け
docker tag $ECR_REPOSITORY:latest $ECR_URI:latest

# イメージプッシュ
docker push $ECR_URI:latest

# 3. CloudWatch ロググループの作成
echo "Creating CloudWatch log group..."
aws logs create-log-group --log-group-name /ecs/social-listening-app --region $AWS_REGION || true

# 4. ECS クラスターの作成
echo "Creating ECS cluster..."
aws ecs create-cluster --cluster-name $ECS_CLUSTER --region $AWS_REGION || true

# 5. タスク定義の更新
echo "Updating task definition..."
sed -i "s/{ACCOUNT_ID}/$ACCOUNT_ID/g" aws-deploy/task-definition.json
sed -i "s/{ECR_URI}/$ECR_URI/g" aws-deploy/task-definition.json

# タスク定義の登録
aws ecs register-task-definition --cli-input-json file://aws-deploy/task-definition.json --region $AWS_REGION

# 6. Application Load Balancer の作成（必要に応じて）
echo "Creating Application Load Balancer..."
# VPC とサブネットの情報を取得
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region $AWS_REGION)

# セキュリティグループの作成
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name social-listening-sg \
    --description "Security group for social listening app" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION \
    --query 'GroupId' --output text) || \
    aws ec2 describe-security-groups --filters "Name=group-name,Values=social-listening-sg" --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION

# セキュリティグループのルール追加
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8002 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION || true

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION || true

# 7. ECS サービスの作成
echo "Creating ECS service..."
cat > aws-deploy/service.json << EOF
{
  "serviceName": "$ECS_SERVICE",
  "cluster": "$ECS_CLUSTER",
  "taskDefinition": "social-listening-app",
  "desiredCount": 1,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": [$(echo $SUBNET_IDS | sed 's/ /", "/g' | sed 's/^/"/' | sed 's/$/"/')]
      "securityGroups": ["$SECURITY_GROUP_ID"],
      "assignPublicIp": "ENABLED"
    }
  }
}
EOF

aws ecs create-service --cli-input-json file://aws-deploy/service.json --region $AWS_REGION || \
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --task-definition social-listening-app --region $AWS_REGION

echo "Deployment completed!"
echo "Check the ECS console for service status: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$ECS_CLUSTER/services"
