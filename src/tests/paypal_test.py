
import sys
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment


CLIENT_ID = 'Ae3kTzVUaZ9fXRMbKmnR43rEMG6IwPs9pLGGq0JjK_eZgApGAXBW4B10x1nmf4GZHO3qoP4NLsjcZIfi'
SECRET_ID = 'EDRI-OYIysbhcO4W4Tx664hF_oWJ636pwdm8i5giVyPgT3V23E5mUgDeQWQX8VmA6gkS-eBeAjlCr4Sb'

environment = LiveEnvironment(CLIENT_ID, client_secret=SECRET_ID)
client = PayPalHttpClient(environment)


STRIPE_BASE_URL='https://api.stripe.com'
STRIPE_API_KEY='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'

def run():
    pass

run()
