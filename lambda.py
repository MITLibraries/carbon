import json
import os
import ssl

import boto3

from carbon.app import Config, ENV_VARS, FTPFeeder
from carbon.db import engine


def handler(event, context):
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId=os.environ['SECRET_ID'])
    secret_env = json.loads(secret['SecretString'])
    cfg = Config.from_env()
    cfg.update({k: event[k] for k in ENV_VARS if k in event})
    cfg.update(secret_env)
    engine.configure(cfg['CARBON_DB'])
    c_dir = os.path.dirname(os.path.realpath(__file__))
    cert = os.path.join(c_dir, 'comodo.pem')
    ctx = ssl.create_default_context()
    # Load the missing cert from Symplectic's cert chain
    ctx.load_verify_locations(cafile=cert)
    FTPFeeder(event, context, cfg, ctx).run()
