import os
import json
import stripe
import boto3 as boto
import logging
from requests.structures import CaseInsensitiveDict
from schema import Schema, And, Use, Optional, SchemaError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


QUEUE_URL = os.environ["QUEUE"]

QUEUE = boto.client("sqs")


def respond(code=200, body="", headers={}):
    return {
        "statusCode": code,
        "body": json.dumps(body),
        "headers": headers or {"Content-Type": "application/json"},
    }


webhook_payload_schema = Schema({
    'id': And(str, len),
    'object': 'donation',
    "created": str,
    'event': str,
    "donation": {
        "id": str,
        "amount": str,
        "currency": str,
        "exchangerate": str,
        "datetime": str,
        "giftaid": str,
        "displayname": str,
        "message": str,
        "repeat": str,
        "recurrence": str,
        "recurrenceno": str,
        "cancelled": str,
        "custom": str,
        },
    "supporter": {
        "id": str,
        "title": str,
        "firstname": str,
        "surname": str,
        "address1": str,
        "address2": str,
        "town": str,
        "postcode": str,
        "county": str,
        "country": str,
        "telephone": str,
        "fax": str,
        "mobile": str,
        "email": str,
        "mailinglist": str,
        "active": str,
        }
    })




def validate_webhook_payload(payload):
    pass

def donation_succeded(event, context):
    headers, body = CaseInsensitiveDict(event["headers"]), json.loads(event["body"])
    logger.info(headers)
    logger.info(body)

    try:
        webhook_payload_schema.validate(body)
    except SchemaError as e:
        logger.warning("Bad payload")
        logger.warning(e)
        return respond(400, {"message": "Bad payload", "error": str(e)}) # XXX: only get the errors

    response = QUEUE.send_message(QueueUrl=QUEUE_URL,
                        MessageBody=event['body'])

    logger.info(response)

    return respond(200)
