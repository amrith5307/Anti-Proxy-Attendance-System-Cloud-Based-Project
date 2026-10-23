import json, os, time, uuid, boto3

table = boto3.resource("dynamodb").Table(os.environ["SESSIONS_TABLE"])
H = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}


def resp(code, body):
    return {"statusCode": code, "headers": H, "body": json.dumps(body)}


def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["claims"]
    if "Faculty" not in claims.get("cognito:groups", ""):
        return resp(403, {"error": "Faculty only"})

    body = json.loads(event.get("body") or "{}")
    minutes = int(body.get("minutes", 10))
    now = int(time.time())
    session_id = str(uuid.uuid4())[:8]

    table.put_item(Item={
        "session_id": session_id,
        "course": body.get("course", "General"),
        "faculty": claims["email"],
        "status": "open",
        "created_at": now,
        "expires_at": now + minutes * 60,
    })
    return resp(200, {"session_id": session_id, "expires_in_minutes": minutes})