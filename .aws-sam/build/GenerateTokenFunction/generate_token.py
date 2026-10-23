import json, os, time, boto3
from token_utils import make_token

table = boto3.resource("dynamodb").Table(os.environ["SESSIONS_TABLE"])
H = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}


def resp(code, body):
    return {"statusCode": code, "headers": H, "body": json.dumps(body)}


def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["claims"]
    if "Faculty" not in claims.get("cognito:groups", ""):
        return resp(403, {"error": "Faculty only"})

    sid = event["pathParameters"]["session_id"]
    item = table.get_item(Key={"session_id": sid}).get("Item")
    if not item:
        return resp(404, {"error": "Session not found"})
    if item["status"] != "open" or time.time() > int(item["expires_at"]):
        return resp(400, {"error": "Session closed"})

    token = make_token(os.environ["TOKEN_SECRET"], sid)
    return resp(200, {"token": token, "refresh_in": 30})