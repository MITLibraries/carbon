#!/usr/bin/env bash
set -e

BUILD_DIR=build-aws
DIST_DIR=dist-aws
S3_BUCKET=carbon-deploy
LIBAIO_SO=libaio.so.1.0.1
ORACLE_ZIP=instantclient-basiclite-linux.x64-18.3.0.0.0dbru.zip
PACKAGE=carbon-`git rev-parse --short HEAD`.zip

mkdir -p $BUILD_DIR/lib
mkdir -p $DIST_DIR

aws s3 cp s3://$S3_BUCKET/$ORACLE_ZIP $BUILD_DIR/$ORACLE_ZIP && \
  unzip -j $BUILD_DIR/$ORACLE_ZIP -d $BUILD_DIR/lib/ 'instantclient_18_3/*' && \
  rm $BUILD_DIR/$ORACLE_ZIP
aws s3 cp s3://$S3_BUCKET/$LIBAIO_SO $BUILD_DIR/lib/$LIBAIO_SO && \
  ln -rs $BUILD_DIR/lib/$LIBAIO_SO $BUILD_DIR/lib/libaio.so.1 && \
  ln -rs $BUILD_DIR/lib/libaio.so.1 $BUILD_DIR/lib/libaio.so
cp -r carbon $BUILD_DIR
cp lambda.py $BUILD_DIR
pipenv lock -r > $BUILD_DIR/requirements.txt
pipenv run pip install -r $BUILD_DIR/requirements.txt -t $BUILD_DIR
cd $BUILD_DIR && zip --symlinks -r ../$DIST_DIR/$PACKAGE *
