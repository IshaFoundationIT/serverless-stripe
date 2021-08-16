import odoorpc
import json
import boto3
import os
import logging
import datetime
import pytz
from datetime import timezone, datetime
from dateutil import parser
import stripe
###############################
#TO Dos
# 1. Add Alarms/notification if a message goes to dlq
# 2. check consumer if it raises exception on error
# 3. Add target to event rule
# 4. cleanup stripe
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

def consumer_stripe(event, context):
    logger.info("____________________________")
    logger.info(event)
    QUEUE_DLQ_URL = QUEUE_URL.replace('stripe-queue','stripe-queue-dlq')
    logger.info("data to be sent is ")
    
    for record in event['Records']:
        logger.info(json.loads(record['body'])['detail'])
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
    stripe.api_key = ""
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
    # logger.info(type(event))
    event = event['data']['object']
    logger.info(event)
    try:
        fee = event.get('balance_transaction')
        logger.info("-2____________{0}".format(fee))
        fee="txn_3JPAs6FOdz1GkABX02vnwpnF"
        fee = stripe.BalanceTransaction.retrieve(fee)
        logger.info("-1____________{0}".format(fee))
        #Use fee.get('fee') and divide it by 100. This will be the stripe fee to be 
        #used for creating journal entry (Dr to NC-5821 PayPal, Stripe & Shopify Card Processing Fees 
        # Cr to NC-Bank Stripe . The journal entry shud be created at the time of validating
        # donation record. The fee shuld be stored as a value in tax receipt.

        journal_id = odoo.env['account.journal'].search([('name', '=', 'Stripe')])[0]
        logger.info("0_____{0}".format(event.get('object')))

        billing_detail_dic = event.get('billing_details')
        logger.info("1___{0}".format(billing_detail_dic))
        donor_id = odoo.env['res.partner'].search([('name', 'ilike', billing_detail_dic.get('name'))])
        logger.info("2___{0}".format(donor_id))
        currency_id = odoo.env['res.currency'].search([('name', 'ilike', event.get('currency'))])
        logger.info("3___{0}".format(currency_id))
        dt_obj = datetime.fromtimestamp(event.get('created')).strftime('%Y-%m-%d')
        logger.info("4___{0}".format(dt_obj))
        donation_id = odoo.env['donation.donation'].search([('partner_id', '=', donor_id),
                                                            ('amount_total', '=', event.get('amount')/100),
                                                            ('currency_id', '=', currency_id),
                                                            ('donation_date', '=', dt_obj),
                                                            ('state', '=', 'draft')], limit=1)
        logger.info("5___{0}".format(donation_id))                                                                
        donation_tax_receipt_id = odoo.env['donation.tax.receipt'].search([('reference', '=', event.get('id'))])
        partner_id = []
        partner_id = odoo.env['res.partner'].search([('name', 'ilike', billing_detail_dic.get('name'))])
        if not partner_id:
            partner_id.append(odoo.env['res.partner'].create({
                'name': billing_detail_dic.get('name'),
            }))
        company_id = odoo.env['res.company'].search([('name', 'ilike', 'Isha Foundation')])
        donation_tax_vals = {
                                'reference': event.get('id'),
                                'object_name': "{0} with fee of ({1})".format(event.get('object'),fee.get('fee')/100),
                                'payment_method': event.get('payment_method'),
                                'receipt_url': event.get('receipt_url'), }
        if donation_id:
            odoo.env['donation.donation'].write(donation_id[0],{
                'journal_id': journal_id or False,
            })
            odoo.execute('donation.donation', 'validate', [donation_id[0]])
            tax_receipt_id = odoo.execute('donation.donation', 'read', [donation_id[0]], ['tax_receipt_id'])
            donation_tax_receipt_id = tax_receipt_id[0]['tax_receipt_id'][0]
            odoo.env['donation.tax.receipt'].write(donation_tax_receipt_id, donation_tax_vals)
        else:
            donation_tax_vals = {'number': event.get('metadata').get('order_id'),
                                    'date': dt_obj,
                                    'partner_id': partner_id[0],
                                    'type': 'each',
                                    'donation_date': dt_obj,
                                    'print_date': dt_obj,
                                    'amount': event.get('amount')/100,
                                    'company_id': company_id[0],
                                    'reference': event.get('id'),
                                    'object_name': "{0} with fee of ({1})".format(event.get('object'),fee.get('fee')/100),
                                    'payment_method': event.get('payment_method'),
                                    'receipt_url': event.get('receipt_url'), }
            # if not donation_tax_receipt_id:
            donation_tax_receipt_id = odoo.env['donation.tax.receipt'].create(donation_tax_vals)
            # else:
                # odoo.env['donation.tax.receipt'].write(donation_tax_receipt_id, donation_tax_vals)

        logger.info("tax invoice created is {0}".format(donation_tax_receipt_id))
        response = {"statusCode": 200, "id": id}
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
    # detail = json.dumps(json.loads(event))
    response = bus.put_events(
            Entries=[
                {
                    'Source': 'stripe',
                    'DetailType': 'donation',
                    'Detail': event,
                    'EventBusName': event_bridge
                }
            ]
        )
    logger.info("response is : {0}".format(response))
    if response['FailedEntryCount'] == 0:
        return {"statusCode": 200, "body": json.dumps(response['Entries'])}
    else:
        return {"statusCode": 501, "body": json.dumps(response)}

