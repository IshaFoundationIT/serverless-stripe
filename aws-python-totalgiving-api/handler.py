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
logger.setLevel(logging.INFO)

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


def consumer_dlq(event, context):
    pass

def consumer(event, context):

    for record in event['Records']:
        # record = json.loads(record['body'])
        logger.info("////////////DLQ url is {0}".format(event_bridge))
        logger.info("////////////QUE url is {0}".format(QUEUE_URL))
        QUEUE_DLQ_URL = QUEUE_URL.replace('my-queue','my-queue-dlq')
        logger.info("////////////QUE url is {0}".format(QUEUE_DLQ_URL))
        logger.info("************************* - {0}".format(type(record)))
        logger.info("************************* - {0}".format(json.loads(record['body'])))
        logger.info("========================= - {0}".format(type(json.loads(record['body']))))
        # logger.info("************************* - {0}".format(type(record['body']['detail'])))
        logger.info(f'Message: {record}')
        logger.info("*************************")
        logger.info(f'Message body: {record["body"]}')
        response = totalgiving_process_q(json.loads(record['body'])['detail'], context)
        if response['statusCode'] != 200:
            try:
                SQS.send_message(
                    QueueUrl=QUEUE_DLQ_URL,
                    MessageBody=json.dumps(record),
            )
                logger.info('.........Message pushed to DLQ!')
            except Exception as e:
                logger.exception('Sending message to SQS DLQ queue failed!')
                message = str(e)
                status_code = 599
                return response

def totalgiving_router(event, context):
    
    bus = boto3.client('events')
    logger.info(type(event['body']))
    logger.info(event['body'])
    r = event['body']
    # r = '[{    "id": "6677243",    "object": "donation",    "event": "created",    "created": "2021-08-08T01:08:08.000Z",    "donation": {        "id": "2172365",        "amount": "50",        "currency": "GBP",        "exchangerate": "1",        "datetime": "2021-08-08T01:07:32.000Z",        "giftaid": "false",        "displayname": "",        "message": "",        "repeat": "M",        "recurrence": "true",        "recurrenceno": "13",        "cancelled": "false",        "custom": ""    },    "supporter": {        "id": "1424341",        "title": "Mr",        "firstname": "Surjit",        "surname": "Singh",        "address1": "13 Anderson Road",        "address2": "",        "town": "Weybridge",        "county": "Surrey",        "postcode": "Kt13 9nl",        "country": "United Kingdom",        "telephone": "",        "fax": "",        "mobile": "",        "email": "surjit_taj@yahoo.in",        "mailinglist": "true",        "active": "true"    },    "totalgivingpage": {        "id": "17877",        "title": "Isha Sanghamitra - Crafting a Conscious Planet",        "url": "https://www.totalgiving.co.uk/appeal/Isha-Sanghamitra",        "visible": "true",        "allowdonations": "true",        "active": "true"    },    "appeal": {        "id": "6194",        "title": "Isha Sanghamitra - Crafting a Conscious Planet",        "active": "true"    }}]'
    detail = json.dumps(json.loads(r)[0])
    logger.info(json.loads(r)[0])
    logger.info(detail)
    logger.info(type(detail))
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
    logger.info("response is : {0}".format(response))
    if response['FailedEntryCount'] == 0:
        return {"statusCode": 200, "body": json.dumps(response['Entries'])}
    else:
        return {"statusCode": 501, "body": json.dumps(response)}


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
