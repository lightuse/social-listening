#!/bin/bash

AWS_REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Creating IAM roles and policies..."

# 1. ECS Task Execution Role
cat > aws-deploy/ecs-task-execution-role-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file://aws-deploy/ecs-task-execution-role-policy.json || true

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# 2. ECS Task Role (アプリケーションが使用)
cat > aws-deploy/ecs-task-role-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name ecsTaskRole \
    --assume-role-policy-document file://aws-deploy/ecs-task-role-policy.json || true

# 3. アプリケーション用のポリシー
cat > aws-deploy/app-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": [
        "arn:aws:ssm:$AWS_REGION:$ACCOUNT_ID:parameter/social-listening/*"
      ]
    }
  ]
}
EOF

aws iam create-policy \
    --policy-name SocialListeningAppPolicy \
    --policy-document file://aws-deploy/app-policy.json || true

aws iam attach-role-policy \
    --role-name ecsTaskRole \
    --policy-arn arn:aws:iam::$ACCOUNT_ID:policy/SocialListeningAppPolicy

echo "IAM roles and policies have been created!"
