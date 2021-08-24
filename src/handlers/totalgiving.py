import os
import json
import stripe
import boto3 as boto
from botocore.exceptions import ClientError
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


webhook_payload_schema = Schema(
    {
        "id": And(str, len),
        "object": "donation",
        "created": str,
        "event": str,
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
        },
    }
)


def validate_webhook_payload(payload):
    if isinstance(payload, list):
        for message in body:
            yield schema.validate(message)
    else:
        yield schema.validate(message)


# XXX: Totalgiving doesn't have any way to validate webhooks
#      we should probably try to validate the ip address instead as a rudimentary
#      workaround.


def donation_succeded(event, context):
    headers, body = CaseInsensitiveDict(event["headers"]), json.loads(event["body"])

    logger.info(headers)
    logger.info(body)

    if isinstance(body, list):
        if not len(body):
            logger.warning("Empty event payload")
            logger.warning(body)

        body = body[0]
        if len(body) > 1:
            logger.warning("Body contained more than 1 message")
            list(map(logger.warning, body))
            respond(500, {"message": "Body contained more than 1 message"})

    try:
        webhook_payload_schema.validate(body)
    except SchemaError as e:
        logger.warning("Bad payload", exc_info=e)
        return respond(
            400, {"message": "Bad payload", "error": str(e)}
        )  # XXX: only get the errors

    try:
        response = QUEUE.send_message(
            QueueUrl=QUEUE_URL,
            # Message body is a string not json
            MessageBody=event["body"],
            # The queue needs to be a FIFO queue for this work
            #MessageGroupId="sulaba.webhooks.totalgiving",
        )
        logger.info(response)
        return respond(200)

    except ClientError as e:
        logger.error(f"Error sending message to queue {QUEUE_URL}")
        logger.exception(e)
        return respond(500, "Internal Server Error.")
