import json
import stripe

def totalgiving(event, context):
    print(event)
    print(context)
    stripe.api_key = "sk_test_51H05s0FOdz1GkABXzM29YYc6GfuIItqnHbInBpP9iB7CaaJYLJW2IQy7TnY1pxgN3oWBKGAt9QbxTYSm0DY72Neb00NGyAeWqX"
#     requestContextStage = event.requestContext
#     ? event.requestContext.stage
#     : 'test';
#     console.log(event.requestContext.stage)
#   const stripeApiKey =
#     requestContextStage === 'test'
#     ? ConfigFile.stripe.test_sk
#     : ConfigFile.stripe.live_sk;
#   console.log(event)
#   const stripe = require('stripe')(stripeApiKey); // eslint-disable-line
#   const endpointSecret = 'whsec_...';
#   const app = require('express')();
#   const bodyParser = require('body-parser');
#   try {
#     // Parse Stripe Event
#     console.log(event.body.id)
#     const jsonData = event
#     // const jsonData = JSON.parse(event); // https://stripe.com/docs/api#event_object
#     console.log("got json data")
#     // Verify the event by fetching it from Stripe
#     console.log("Stripe Event: %j", jsonData); // eslint-disable-line
    
#     const response = {
#         statusCode: 200,
#         body: JSON.stringify({
#           message: 'Stripe webhook incoming!',
#           stage: requestContextStage,
#         }),
#       };
#       callback(null, response);
# }
#   catch (err) {
#     callback(null, {
#       statusCode: err.statusCode || 501,
#       headers: { 'Content-Type': 'text/plain' },
#       body: err.message || err.message,
#     });
#   }
# };

#     body = {
#         "message": "Go Serverless v2.0! Your function executed successfully!",
#         "input": event,
#     }

    response = {"statusCode": 200, "body": json.dumps(event)}

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
