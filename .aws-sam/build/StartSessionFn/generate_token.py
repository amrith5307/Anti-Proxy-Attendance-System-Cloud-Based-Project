import json, os, boto3
from token_utils import generate_token

dynamodb = boto3.resource("dynamodb")
TABLE = dynamodb.Table(os.environ["SESSIONS_TABLE"])

def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["claims"]
    if "Faculty" not in claims.get("cognito:groups", ""):
        return _r(403, {"error": "Faculty only"})

    session_id = event["pathParameters"]["session_id"]
    item = TABLE.get_item(Key={"session_id": session_id}).get("Item")
    if not item:                              return _r(404, {"error": "Not found"})
    if item["status"] != "ACTIVE":           return _r(400, {"error": "Session closed"})
    if item["faculty_id"] != claims["sub"]:  return _r(403, {"error": "Not your session"})

    return _r(200, generate_token(session_id, item["faculty_id"]))

def _r(code, body):
    return {"statusCode": code,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(body)}