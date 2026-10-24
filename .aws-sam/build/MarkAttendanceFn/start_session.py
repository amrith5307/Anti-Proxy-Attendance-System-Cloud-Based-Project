import json, os, uuid, time, boto3

dynamodb = boto3.resource("dynamodb")
TABLE = dynamodb.Table(os.environ["SESSIONS_TABLE"])

def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["claims"]
    if "Faculty" not in claims.get("cognito:groups", ""):
        return _r(403, {"error": "Faculty only"})

    body = json.loads(event.get("body") or "{}")
    subject = body.get("subject", "General")
    duration = int(body.get("duration_minutes", 60))
    session_id = str(uuid.uuid4())
    now = int(time.time())

    TABLE.put_item(Item={
        "session_id": session_id,
        "faculty_id": claims["sub"],
        "subject": subject,
        "status": "ACTIVE",
        "created_at": now,
        "expires_at": now + duration * 60
    })
    return _r(200, {"session_id": session_id, "expires_at": now + duration * 60})

def _r(code, body):
    return {"statusCode": code,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(body)}