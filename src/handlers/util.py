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
