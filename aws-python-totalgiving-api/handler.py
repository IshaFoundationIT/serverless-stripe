import odoorpc
import json
import boto3
import os
import logging
import datetime
import pytz
from datetime import timezone, datetime
from dateutil import parser
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

TOTALGIVING_QUEUE_URL = os.getenv('TOTALGIVING_QUEUE_URL')
STRIPE_QUEUE_URL = os.getenv('STRIPE_QUEUE_URL')
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
            QueueUrl=TOTALGIVING_QUEUE_URL,
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

def consumer_totalgiving(event, context):
    QUEUE_DLQ_URL = TOTALGIVING_QUEUE_URL.replace('my-queue','my-queue-dlq')
    for record in event['Records']:
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
def totalgiving_process_q(event, context):
    # logger.info(event)

    username = "admin"
    password = "admin"

    url = "8069-amber-porpoise-u4ivsce1.ws-us13.gitpod.io"
    url = "uk.sulaba.isha.us"
    db = "ishafoundationit-odoo14-master-2820710"

    odoo = odoorpc.ODOO(url,protocol='jsonrpc+ssl',port='443')
    # logger.info("++++++++++++++++++++++++++++++++++++++++++++++++")
    # logger.info("initialzied")
    odoo.login(db, username, password)
    # logger.info("logged in")
    # logger.info(event)
    # logger.info(type(event))

    try:
        appeal_dict = event.get('appeal')
        # logger.info("1_____")
        # logger.info(appeal_dict)
        campaign_id = odoo.env['donation.campaign'].search([('name', 'ilike', appeal_dict.get('title'))])
        logger.info("1.1__campaign on search___{0}".format(campaign_id))
        if not campaign_id:
            campaign_id = odoo.env['donation.campaign'].create({
                'code': appeal_dict.get('id'),
                'name': appeal_dict.get('title'),
                'active': appeal_dict.get('active')
            })
            logger.info("2__campaign_on_create___{0}".format(campaign_id))
        donor_dict = event.get('supporter')

        donor_id = odoo.env['res.partner'].search([('reference', '=', donor_dict.get('id'))])
        title_id = odoo.env['res.partner.title'].search([('name', 'ilike', donor_dict.get('title'))])
        if not title_id:
            title_id = odoo.env['res.partner.title'].create({
                'name': donor_dict.get('title'),
            })
        country_id = odoo.env['res.country'].search([('name', 'ilike', donor_dict.get('country'))])
        if not country_id:
            country_id = odoo.env['res.country'].create({
                'name': donor_dict.get('country'),
            })
        state_id = odoo.env['res.country.state'].search([('name', 'ilike', donor_dict.get('county'))])
        # if not state_id:
        #     state_id = odoo.env['res.country.state'].create({
        #         'name': donor_dict.get('county'),
        #         'country_id': country_id[0],
        #         'code': donor_dict.get('county'),
        #     })
        logger.info(" state, country, title - {0}/{1}/{2}".format(state_id,country_id,title_id))
        if not donor_id:
            logger.info("3_____")
            logger.info("inside if")
            donor_id = odoo.env['res.partner'].create({
                'reference': donor_dict.get('id'),
                'title': title_id[0],
                'name': donor_dict.get('firstname') + " " + donor_dict.get('surname'),
                'street': donor_dict.get('address1'),
                'street2': donor_dict.get('address2'),
                'city': donor_dict.get('town'),
                'state_id': state_id and state_id[0] or None,
                'zip': donor_dict.get('postcode'),
                'country_id': country_id[0],
                'phone': donor_dict.get('telephone'),
                'fax': donor_dict.get('fax'),
                'mobile': donor_dict.get('mobile'),
                'email': donor_dict.get('email'),
                'mailinglist': json.loads(donor_dict.get('mailinglist').lower()),
                # 'active': json.loads(donor_dict.get('active').lower()),
            })
        else:
            logger.info("4_____")
            logger.info("inside else")
            odoo.env['res.partner'].write(donor_id,{
                'title': title_id[0],
                'name': donor_dict.get('firstname') + " " + donor_dict.get('surname'),
                'street': donor_dict.get('address1'),
                'street2': donor_dict.get('address2'),
                'city': donor_dict.get('town'),
                'state_id': state_id[0],
                'zip': donor_dict.get('postcode'),
                'country_id': country_id[0],
                'phone': donor_dict.get('telephone'),
                'fax': donor_dict.get('fax'),
                'mobile': donor_dict.get('mobile'),
                'email': donor_dict.get('email'),
                # 'mailinglist': json.loads(donor_dict.get('mailinglist').lower()),
                # 'active': json.loads(donor_dict.get('active').lower()),
            })
            donor_id = donor_id[0]
        logger.info("5_1__donor___{0}".format(donor_id))
        donation_dict = event.get('donation')
        # logger.info(donation_dict)
        donation_id = None
        # donation_id = odoo.env['donation.donation'].search([('donation_ref','=',donation_dict.get('id'))])
        logger.info("5.1____{0}".format(donation_id))
        currency_id = odoo.env['res.currency'].search([('name', '=', donation_dict.get('currency'))])
        logger.info("5.2____{0}".format(currency_id))
        journal_id = odoo.env['account.journal'].search([('name','ilike','Bank')])
        logger.info("5.3____{0}".format(journal_id))
        company_id = odoo.env['res.company'].search([('name','ilike','Isha Foundation')])
        logger.info("5.4____{0}".format(company_id))
        product_id = odoo.env['product.product'].search([('default_code', '=', 'DON')])
        logger.info("5.5____{0}".format(product_id))
        donation_datetime = parser.parse(donation_dict.get('datetime'))
        logger.info("5.6____{0}".format(donation_datetime))
        logger.info("5.7____{0}".format(donation_datetime.astimezone(pytz.utc).strftime('%Y-%m-%d')))
        logger.info("6_____{0}".format(donation_dict))
        # logger.info("before donation vals - {0}, {1}".format(json.loads(donation_dict.get('giftaid')),json.loads(donation_dict.get('recurrence'))))

        donation_vals = {
            'journal_id': journal_id[0],
            'partner_id': donor_id,
            'company_id': company_id[0],
            'campaign_id': campaign_id[0],
            'donation_ref': donation_dict.get('id'),
            # 'check_total': donation_dict.get('amount'),
            'currency_id': currency_id[0],
            'exchange_rate': donation_dict.get('exchangerate'),
            'donation_date': donation_datetime.astimezone(pytz.utc).strftime('%Y-%m-%d'),
            'giftaid': json.loads(donation_dict.get('giftaid').lower()),
            'display_name': donation_dict.get('displayname'),
            'message': donation_dict.get('message'),
            'repeat': donation_dict.get('repeat'),
            # 'recurrence': json.loads(donation_dict.get('recurrence').lower()),
            'recurrence_number': donation_dict.get('recurrence_number'),
            'custom': donation_dict.get('custom'),
        }
        logger.info("7_____{0}".format(donation_vals))
        
        if json.loads(donation_dict.get('cancelled').lower()):
            donation_vals.update({'state': 'cancel'})
            logger.info("8____inside cancel")
        if not donation_id:
            logger.info("9_____no existing donation record")
            donation_vals.update({
                'line_ids': [(0, 0, {
                    'product_id': product_id[0],
                    'currency_id': currency_id[0],
                    'quantity': 1,
                    'unit_price': donation_dict.get('amount'),
                })]
            })
            logger.info("10_____updated donation with product - {0}".format(donation_vals))
            donation_id = odoo.env['donation.donation'].create(donation_vals)
            logger.info("11_____donation created - {0}".format(donation_id))
        else:
            odoo.env['donation.donation'].write(donation_id, donation_vals)
            logger.info("11_____donation updated - {0}".format(donation_id))

        logger.info("Donation id created is {0}".format(donation_id))
        response = {"statusCode": 200, "id": donation_id}
    except Exception as e:
        response = {"statusCode": 501, "error": str(e)}
    logger.info("response is {0}".format(response))
    return response

def totalgiving_router(event, context):
    event_bridge = os.getenv('EVENT_BRIDGE')
    bus = boto3.client('events')
    # logger.info(type(event['body']))
    # logger.info(event['body'])
    r = event['body']
    # r = '[{    "id": "6677243",    "object": "donation",    "event": "created",    "created": "2021-08-08T01:08:08.000Z",    "donation": {        "id": "2172365",        "amount": "50",        "currency": "GBP",        "exchangerate": "1",        "datetime": "2021-08-08T01:07:32.000Z",        "giftaid": "false",        "displayname": "",        "message": "",        "repeat": "M",        "recurrence": "true",        "recurrenceno": "13",        "cancelled": "false",        "custom": ""    },    "supporter": {        "id": "1424341",        "title": "Mr",        "firstname": "Surjit",        "surname": "Singh",        "address1": "13 Anderson Road",        "address2": "",        "town": "Weybridge",        "county": "Surrey",        "postcode": "Kt13 9nl",        "country": "United Kingdom",        "telephone": "",        "fax": "",        "mobile": "",        "email": "surjit_taj@yahoo.in",        "mailinglist": "true",        "active": "true"    },    "totalgivingpage": {        "id": "17877",        "title": "Isha Sanghamitra - Crafting a Conscious Planet",        "url": "https://www.totalgiving.co.uk/appeal/Isha-Sanghamitra",        "visible": "true",        "allowdonations": "true",        "active": "true"    },    "appeal": {        "id": "6194",        "title": "Isha Sanghamitra - Crafting a Conscious Planet",        "active": "true"    }}]'
    detail = json.dumps(json.loads(r)[0])
    # logger.info(json.loads(r)[0])
    # logger.info(detail)
    # logger.info(type(detail))
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
    # logger.info("response is : {0}".format(response))
    if response['FailedEntryCount'] == 0:
        return {"statusCode": 200, "body": json.dumps(response['Entries'])}
    else:
        return {"statusCode": 501, "body": json.dumps(response)}

def consumer_stripe(event, context):
    QUEUE_DLQ_URL = STRIPE_QUEUE_URL.replace('stripe-queue','atripe-queue-dlq')
    logger.info("getting called...")
    for record in event['Records']:
        logger.info(record)
        logger.info(QUEUE_DLQ_URL)
        return {"statusCode":200}

        response = stripe_process_q(json.loads(record['body'])['detail'], context)
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

def stripe_process_q(event, context):
    # logger.info(event)

    username = "admin"
    password = "admin"

    url = "8069-amber-porpoise-u4ivsce1.ws-us13.gitpod.io"
    url = "uk.sulaba.isha.us"
    db = "ishafoundationit-odoo14-master-2820710"

    odoo = odoorpc.ODOO(url,protocol='jsonrpc+ssl',port='443')
    # logger.info("++++++++++++++++++++++++++++++++++++++++++++++++")
    # logger.info("initialzied")
    odoo.login(db, username, password)
    # logger.info("logged in")
    # logger.info(event)
    # logger.info(type(event))

    try:
        appeal_dict = event.get('appeal')
        # logger.info("1_____")
        # logger.info(appeal_dict)
        campaign_id = odoo.env['donation.campaign'].search([('name', 'ilike', appeal_dict.get('title'))])
        logger.info("1.1__campaign on search___{0}".format(campaign_id))
        if not campaign_id:
            campaign_id = odoo.env['donation.campaign'].create({
                'code': appeal_dict.get('id'),
                'name': appeal_dict.get('title'),
                'active': appeal_dict.get('active')
            })
            logger.info("2__campaign_on_create___{0}".format(campaign_id))
        donor_dict = event.get('supporter')

        donor_id = odoo.env['res.partner'].search([('reference', '=', donor_dict.get('id'))])
        title_id = odoo.env['res.partner.title'].search([('name', 'ilike', donor_dict.get('title'))])
        if not title_id:
            title_id = odoo.env['res.partner.title'].create({
                'name': donor_dict.get('title'),
            })
        country_id = odoo.env['res.country'].search([('name', 'ilike', donor_dict.get('country'))])
        if not country_id:
            country_id = odoo.env['res.country'].create({
                'name': donor_dict.get('country'),
            })
        state_id = odoo.env['res.country.state'].search([('name', 'ilike', donor_dict.get('county'))])
        # if not state_id:
        #     state_id = odoo.env['res.country.state'].create({
        #         'name': donor_dict.get('county'),
        #         'country_id': country_id[0],
        #         'code': donor_dict.get('county'),
        #     })
        logger.info(" state, country, title - {0}/{1}/{2}".format(state_id,country_id,title_id))
        if not donor_id:
            logger.info("3_____")
            logger.info("inside if")
            donor_id = odoo.env['res.partner'].create({
                'reference': donor_dict.get('id'),
                'title': title_id[0],
                'name': donor_dict.get('firstname') + " " + donor_dict.get('surname'),
                'street': donor_dict.get('address1'),
                'street2': donor_dict.get('address2'),
                'city': donor_dict.get('town'),
                'state_id': state_id and state_id[0] or None,
                'zip': donor_dict.get('postcode'),
                'country_id': country_id[0],
                'phone': donor_dict.get('telephone'),
                'fax': donor_dict.get('fax'),
                'mobile': donor_dict.get('mobile'),
                'email': donor_dict.get('email'),
                'mailinglist': json.loads(donor_dict.get('mailinglist').lower()),
                # 'active': json.loads(donor_dict.get('active').lower()),
            })
        else:
            logger.info("4_____")
            logger.info("inside else")
            odoo.env['res.partner'].write(donor_id,{
                'title': title_id[0],
                'name': donor_dict.get('firstname') + " " + donor_dict.get('surname'),
                'street': donor_dict.get('address1'),
                'street2': donor_dict.get('address2'),
                'city': donor_dict.get('town'),
                'state_id': state_id[0],
                'zip': donor_dict.get('postcode'),
                'country_id': country_id[0],
                'phone': donor_dict.get('telephone'),
                'fax': donor_dict.get('fax'),
                'mobile': donor_dict.get('mobile'),
                'email': donor_dict.get('email'),
                # 'mailinglist': json.loads(donor_dict.get('mailinglist').lower()),
                # 'active': json.loads(donor_dict.get('active').lower()),
            })
            donor_id = donor_id[0]
        logger.info("5_1__donor___{0}".format(donor_id))
        donation_dict = event.get('donation')
        # logger.info(donation_dict)
        donation_id = None
        # donation_id = odoo.env['donation.donation'].search([('donation_ref','=',donation_dict.get('id'))])
        logger.info("5.1____{0}".format(donation_id))
        currency_id = odoo.env['res.currency'].search([('name', '=', donation_dict.get('currency'))])
        logger.info("5.2____{0}".format(currency_id))
        journal_id = odoo.env['account.journal'].search([('name','ilike','Bank')])
        logger.info("5.3____{0}".format(journal_id))
        company_id = odoo.env['res.company'].search([('name','ilike','Isha Foundation')])
        logger.info("5.4____{0}".format(company_id))
        product_id = odoo.env['product.product'].search([('default_code', '=', 'DON')])
        logger.info("5.5____{0}".format(product_id))
        donation_datetime = parser.parse(donation_dict.get('datetime'))
        logger.info("5.6____{0}".format(donation_datetime))
        logger.info("5.7____{0}".format(donation_datetime.astimezone(pytz.utc).strftime('%Y-%m-%d')))
        logger.info("6_____{0}".format(donation_dict))
        # logger.info("before donation vals - {0}, {1}".format(json.loads(donation_dict.get('giftaid')),json.loads(donation_dict.get('recurrence'))))

        donation_vals = {
            'journal_id': journal_id[0],
            'partner_id': donor_id,
            'company_id': company_id[0],
            'campaign_id': campaign_id[0],
            'donation_ref': donation_dict.get('id'),
            # 'check_total': donation_dict.get('amount'),
            'currency_id': currency_id[0],
            'exchange_rate': donation_dict.get('exchangerate'),
            'donation_date': donation_datetime.astimezone(pytz.utc).strftime('%Y-%m-%d'),
            'giftaid': json.loads(donation_dict.get('giftaid').lower()),
            'display_name': donation_dict.get('displayname'),
            'message': donation_dict.get('message'),
            'repeat': donation_dict.get('repeat'),
            # 'recurrence': json.loads(donation_dict.get('recurrence').lower()),
            'recurrence_number': donation_dict.get('recurrence_number'),
            'custom': donation_dict.get('custom'),
        }
        logger.info("7_____{0}".format(donation_vals))
        
        if json.loads(donation_dict.get('cancelled').lower()):
            donation_vals.update({'state': 'cancel'})
            logger.info("8____inside cancel")
        if not donation_id:
            logger.info("9_____no existing donation record")
            donation_vals.update({
                'line_ids': [(0, 0, {
                    'product_id': product_id[0],
                    'currency_id': currency_id[0],
                    'quantity': 1,
                    'unit_price': donation_dict.get('amount'),
                })]
            })
            logger.info("10_____updated donation with product - {0}".format(donation_vals))
            donation_id = odoo.env['donation.donation'].create(donation_vals)
            logger.info("11_____donation created - {0}".format(donation_id))
        else:
            odoo.env['donation.donation'].write(donation_id, donation_vals)
            logger.info("11_____donation updated - {0}".format(donation_id))

        logger.info("Donation id created is {0}".format(donation_id))
        response = {"statusCode": 200, "id": donation_id}
    except Exception as e:
        response = {"statusCode": 501, "error": str(e)}
    logger.info("response is {0}".format(response))
    return response

def stripe_router(event, context):
    bus = boto3.client('events')
    # r = event['body']
    logger.info(event)
    logger.info(event_bridge)
    # return {"statusCode": 200, "body": "Succesfully triggered lambda"}
    detail = json.dumps(event)
    response = bus.put_events(
            Entries=[
                {
                    'Source': 'stripe',
                    'DetailType': 'invoice.paid',
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
