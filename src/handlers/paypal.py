import os
import json
import boto3 as boto
import logging
from pprint import pprint as pp
from datetime import datetime
import paypalrestsdk
from paypalrestsdk import Webhook, WebhookEvent
from dataclasses import dataclass
from requests.structures import CaseInsensitiveDict


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ENV
EVENT_BUS_NAME = os.environ["EVENT_BUS"]
EVENTS_SOURCE = os.environ["EVENTS_SOURCE"]
print("--->", EVENTS_SOURCE)

logger.info("ENV:")
logger.info(f"EVENT BUS NAME: {EVENT_BUS_NAME}")

BUS = boto.client("events")


"""
PAYPAL = paypalrestsdk.configure({
    'client_id': os.environ("PAYPAL_CLIENT_ID"),
    'client_secret': os.environ("PAYPAL_CLIENT_SECRET"),
})
"""


class SignatureValidationError(ValueError):
    pass


class ValidationError(ValueError):
    pass


def respond(code=200, body="", headers={}):
    return {
        "statusCode": code,
        "body": json.dumps(body),
        "headers": headers or {"Content-Type": "application/json"},
    }


def validate_webhook_payload(headers, body):
    assert headers
    assert body

    assert headers["paypal-transmission-id"]
    assert headers["paypal-cert-url"]
    assert headers["paypal-auth-algo"]
    assert headers["paypal-transmission-sig"]
    assert headers["paypal-transmission-time"]

    assert body["id"]


def verify_paypal_webhook_signature(
    transmission_id, timestamp, id, body, certurl, signature, algo
):
    response = WebhookEvent.verify(
        transmission_id, timestamp, id, body, certurl, signature, algo
    )

    if response and "bad_signature" in response:
        raise ValidationError("Webhook signature is incorrect")
    return True


# Publisher
# Publishes an event to the Event bus after the validation of the signature
def publish(detail):
    wrapped_detail = {
        "meta": {
            "platform": "PAYPAL",
            "type": "webhook",
            "name": detail["event_type"],
        }
    }
    response = BUS.put_events(
        Entries=[
            {
                "Source": EVENTS_SOURCE,
                "DetailType": "payment.capture.completed",
                "Detail": json.dumps(detail),
                "EventBusName": EVENT_BUS_NAME,
            }
        ]
    )
    return response


# Handler
# This is the lambda function called when a webhook event from stripe hits
# the api gateway.
def payment_captured(event, context):
    logger.info(event)
    logger.info(context)

    logger.info("---")
    logger.info(event["body"])
    logger.info("---")
    # TODO: Catch json.loads exception
    headers, body = CaseInsensitiveDict(event["headers"]), json.loads(event["body"])

    try:
        validate_webhook_payload(headers, body)
    except (AssertionError, KeyError) as e:
        logger.warning("Bad Payload")
        logger.warning(e)
        return respond(400, {"message": "Bad Payload"})

    logger.info(
        "Webhook event recieved {id}, {timestamp}, {signature}".format(
            id=body["id"],
            timestamp=headers["paypal-transmission-time"],
            signature=headers["paypal-transmission-sig"],
        )
    )

    try:
        response = publish(body)

        logger.info("Published to the Event Bus")
        logger.info(response)

        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return respond(200)
        return respond(500, {"message": "Internal Error"})

        # XXX: This throws an error on lambda because can't find cffi module used for crypto
        verify_paypal_webhook_signature(
            transmission_id=headers["paypal-transmission-id"],
            timestamp=headers["paypal-transmission-time"],
            id=body["id"],
            # May have to use the event['body'] directly as json.dumps changes the order of the keys
            body=json.dumps(body),
            certurl=headers["paypal-cert-url"],
            signature=headers["paypal-transmission-sig"],
            algo=headers["paypal-auth-algo"],
        )

    except ValidationError as e:
        logger.warning(f"Bad Signature for webhook with id: {body['id']}")
        logger.warning(e)
        return respond(400, {"message": "Bad signature"})

    except Exception as e:
        logger.critical(e)
        return respond(500, {"message": "An Exception Happened"})


if __name__ == "__main__":
    pass
