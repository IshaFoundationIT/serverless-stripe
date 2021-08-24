import os
import stripe
import boto
from requests.structures import CaseInsensitiveDict

QUEUE_NAME = os.environ["QUEUE_NAME"]

BUS = boto.client("sqs")

def respond(code=200, body="", headers={}):
    return {
        "statusCode": code,
        "body": json.dumps(body),
        "headers": headers or {"Content-Type": "application/json"},
    }


def charge_succeded(event, context):
    headers, body = CaseInsensitiveDict(event["headers"]), json.loads(event["body"])
    return respond(200)
