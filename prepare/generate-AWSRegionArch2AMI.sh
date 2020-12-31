#!/bin/bash

owner="099720109477"  # Canonical
filter_amd64="Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20201026"
filter_arm64="Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-focal-20.04-arm64-server-20201026"
query="Images[*].[ImageId]"

echo "  AWSRegionArch2AMI:"
for region in $(aws ec2 describe-regions --query 'Regions[*].[RegionName]' --output text); do
	echo "    $region:"
	echo "      x86: '$(aws ec2 describe-images --region "$region" --owners "$owner" --filters "$filter_amd64" --query "$query" --output text)'"
	echo "      Arm: '$(aws ec2 describe-images --region "$region" --owners "$owner" --filters "$filter_arm64" --query "$query" --output text)'"
done;

