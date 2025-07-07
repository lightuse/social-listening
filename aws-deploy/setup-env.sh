#!/bin/bash

# AWS Systems Manager Parameter Store に環境変数を設定

AWS_REGION="us-east-1"

echo "Setting up environment variables in AWS Systems Manager Parameter Store..."

# データベース URL（本番では RDS を使用することを推奨）
aws ssm put-parameter \
    --name "/social-listening/database-url" \
    --value "sqlite:///./data/social_listening.db" \
    --type "SecureString" \
    --region $AWS_REGION

# Twitter API キー（実際の値を入力してください）
read -p "Twitter API Key: " TWITTER_API_KEY
aws ssm put-parameter \
    --name "/social-listening/twitter-api-key" \
    --value "$TWITTER_API_KEY" \
    --type "SecureString" \
    --region $AWS_REGION

read -p "Twitter API Secret: " TWITTER_API_SECRET
aws ssm put-parameter \
    --name "/social-listening/twitter-api-secret" \
    --value "$TWITTER_API_SECRET" \
    --type "SecureString" \
    --region $AWS_REGION

read -p "Twitter Access Token: " TWITTER_ACCESS_TOKEN
aws ssm put-parameter \
    --name "/social-listening/twitter-access-token" \
    --value "$TWITTER_ACCESS_TOKEN" \
    --type "SecureString" \
    --region $AWS_REGION

read -p "Twitter Access Token Secret: " TWITTER_ACCESS_TOKEN_SECRET
aws ssm put-parameter \
    --name "/social-listening/twitter-access-token-secret" \
    --value "$TWITTER_ACCESS_TOKEN_SECRET" \
    --type "SecureString" \
    --region $AWS_REGION

echo "Environment variables have been set up in Parameter Store!"
