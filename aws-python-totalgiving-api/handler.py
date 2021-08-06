import odoorpc
import json
import boto3
import os
import logging
###############################
#TO Dos
# 1. Add Alarms/notification if a message goes to dlq
# 2. check consumer if it raises exception on error
# 3. Add target to event rule
# 4. cleanup totalgiving
# 5. Create setup for other apis
#################################
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
        # record = json.loads(record['body'])
        logger.info("************************* - {0}".format(type(record)))
        logger.info("************************* - {0}".format(json.loads(record['body'])))
        logger.info("========================= - {0}".format(type(json.loads(record['body']))))
        # logger.info("************************* - {0}".format(type(record['body']['detail'])))
        logger.info(f'Message: {record}')
        logger.info("*************************")
        logger.info(f'Message body: {record["body"]}')
        response = totalgiving_process_q(json.loads(record['body'])['detail'], context)
        # if response['statusCode'] != 200:



def totalgiving_router(event, context):
    bus = boto3.client('events')
    logger.info(type(event['body']))
    response = bus.put_events(
            Entries=[
                {
                    'Source': 'totalgiving',
                    'DetailType': 'donation',
                    'Detail': event['body'],
                    'EventBusName': event_bridge
                }
            ]
        )

def totalgiving_process_q(event, context):
    logger.info(event)

    username = "admin"
    password = "admin"

    url = "8069-amber-porpoise-u4ivsce1.ws-us13.gitpod.io"
    url = "uk.sulaba.isha.us"
    db = "ishafoundationit-odoo14-master-2820710"

    odoo = odoorpc.ODOO(url,protocol='jsonrpc+ssl',port='443')
    logger.info("++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.info("initialzied")
    odoo.login(db, username, password)
    logger.info("logged in")
    logger.info(event)
    logger.info(type(event))

    try:
        id = odoo.env['donation.donation'].create(event)
        logger.info("id created is {0}".format(id))
        response = {"statusCode": 200, "id": id}
    except Exception as e:
        response = {"statusCode": 501, "error": str(e)}
    logger.info("response is {0}".format(response))
    return response
