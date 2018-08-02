import json
import os

import boto3

from carbon.app import Config, Lambda
from carbon.db import engine


def handler(event, context):
    client = boto3.client('secretsmanager')
    secret_env = client.get_secret_value(SecretId=os.environ['SECRET_ID'])
    cfg = Config.from_env()
    cfg.update(json.loads(secret_env))
    engine.configure(cfg['CARBON_DB'])
    Lambda(event, context, cfg).run()
