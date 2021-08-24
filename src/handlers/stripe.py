import os
import stripe
import boto
from requests.structures import CaseInsensitiveDict


EVENT_BUS_NAME = os.environ["EVENT_BUS"]
EVENTS_SOURCE = os.environ["EVENTS_SOURCE"]
STRIPE_ENDPOINT_SECRET = os.environ["STRIPE_ENDPOINT_SECRET"]

BUS = boto.client("events")

def respond(code=200, body="", headers={}):
    return {
        "statusCode": code,
        "body": json.dumps(body),
        "headers": headers or {"Content-Type": "application/json"},
    }

def publish(detail):
    response = BUS.put_events(
        Entries=[
            {
                "Source": EVENTS_SOURCE,
                "DetailType": "charge.succeded",
                "Detail": json.dumps(detail),
                "EventBusName": EVENT_BUS_NAME,
            }
        ]
    )
    return response


def charge_succeded(event, context):
    #return {'statusCode': 200, 'body': json.dumps({'hello': 'world'})}
    headers, body = CaseInsensitiveDict(event["headers"]), json.loads(event["body"])

    payload = body
    signature = headers["Stripe-Signature"]

    try:
        valid_event = stripe.Webhook.construct_event(payload, signature, STRIPE_ENDPOINT_SECRET)

    except ValueError as e:
        # Invalid payload
        logger.warning("Invalid payload")
        logger.warning(e)
        return respond(400, "Invalid Payload")

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return respond(500, "Invalid Signature")

    response = publish(valid_event)

    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        return respond(200)

    return respond(500, {"message": "Internal Error"})
