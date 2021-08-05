import odoorpc
import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

QUEUE_URL = os.getenv('QUEUE_URL')
event_bridge = os.getenv('EVENT_BRIDGE')
SQS = boto3.client('sqs')

def producer(event, context):
    status_code = 200
    message = ''

    if not event.get('body'):
        return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}

    try:
        message_attrs = {
            'AttributeName': {'StringValue': 'AttributeValue', 'DataType': 'String'}
        }
        SQS.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=event['body'],
            MessageAttributes=message_attrs,
        )
        message = 'Message accepted!'
    except Exception as e:
        logger.exception('Sending message to SQS queue failed!')
        message = str(e)
        status_code = 500

    return {'statusCode': status_code, 'body': json.dumps({'message': message})}


def consumer(event, context):
    for record in event['Records']:
        logger.info("*************************")
        logger.info(record)
        logger.info("*************************")
        logger.info(f'Message body: {record["body"]}')
        # logger.info(
            # f'Message attribute: {record["messageAttributes"]["AttributeName"]["stringValue"]}'
        # )
        totalgiving(event, context)

def totalgiving(event, context):
    logger.info(type(event['body']))
    logger.info(type(json.dumps(event['body'])))
    logger.info("*****env bus name is {0}".format(event_bridge))
    bus = boto3.client('events')
    detail = str(event['body'])
    logger.info(detail)
    response = bus.put_events(
            Entries=[
                {
                    'Source': 'totalgiving',
                    'DetailType': 'donation',
                    'Detail': detail,
                    'EventBusName': event_bridge
                }
            ]
        )

def s2q(event, context):
    print(event)

    username = "admin"
    password = "admin"

    url = "8069-amber-porpoise-u4ivsce1.ws-us13.gitpod.io"
    url = "uk.sulaba.isha.us"
    db = "ishafoundationit-odoo14-master-2820710"

    odoo = odoorpc.ODOO(url,protocol='jsonrpc+ssl',port='443')
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("initialzied")
    odoo.login(db, username, password)
    print("logged in")
    user = odoo.env.user
    print(user)

    try:
        id = odoo.env['donation.donation'].create(eval(event))
        print("id created is {0}".format(id))
        response = {"statusCode": 200, "id": id}
    except Exception as e:
        response = {"statusCode": 501, "error": str(e)}
    print("response is {0}".format(response))
    return response
