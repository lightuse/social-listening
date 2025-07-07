#!/bin/bash

# AWS CLI のインストール
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# AWS CLI 設定
echo "AWS CLI がインストールされました。以下のコマンドを実行してください："
echo "aws configure"
echo "AWS Access Key ID, Secret Access Key, Region (例: us-east-1), Output format (json) を入力してください"
