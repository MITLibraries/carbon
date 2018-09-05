#!/usr/bin/env bash
set -e

PACKAGE=carbon.zip
S3_BUCKET=carbon-deploy

for arg in $@; do
  if [ "$arg" = '--upload' ]; then
    aws s3 cp "dist-aws/$PACKAGE" "s3://$S3_BUCKET/$PACKAGE"
    break
  fi
done

aws lambda update-function-code --function-name mitlib-global-carbon \
  --s3-bucket $S3_BUCKET --s3-key $PACKAGE --region us-east-1
