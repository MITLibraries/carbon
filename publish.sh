#!/usr/bin/env bash
set -e

PACKAGE=carbon-`git rev-parse --short HEAD`.zip
S3_BUCKET=carbon-deploy

aws lambda update-function-code --function-name carbon-test --s3-bucket \
  $S3_BUCKET --s3-key $PACKAGE --region us-east-1
