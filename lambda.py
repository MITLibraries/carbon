import json
import os

import boto3

from carbon.app import Config, FTPFeeder
from carbon.db import engine


def handler(event, context):
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId=os.environ['SECRET_ID'])
    secret_env = json.loads(secret['SecretString'])
    cfg = Config.from_env()
    cfg.update(secret_env)
    engine.configure(cfg['CARBON_DB'])
    FTPFeeder(event, context, cfg).run()
