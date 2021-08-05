import odoorpc
import json

def totalgiving(event, context):
    print(event)
    print(context)
    model = 'donation.donation'
    data = event['body']
    print(data)
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
        id = odoo.env['donation.donation'].create(eval(data))
        print("id created is {0}".format(id))
        response = {"statusCode": 200, "id": id}
    except Exception as e:
        response = {"statusCode": 501, "error": str(e)}
    print("response is {0}".format(response))
    return response
