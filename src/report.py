import json, os, boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
SESSIONS   = dynamodb.Table(os.environ["SESSIONS_TABLE"])
ATTENDANCE = dynamodb.Table(os.environ["ATTENDANCE_TABLE"])

def lambda_handler(event, context):
    claims     = event["requestContext"]["authorizer"]["claims"]
    is_faculty = "Faculty" in claims.get("cognito:groups", "")
    uid        = claims["sub"]
    params     = event.get("pathParameters") or {}

    if is_faculty:
        if "session_id" in params:
            # detail view: list who attended
            rows = ATTENDANCE.query(
                KeyConditionExpression=Key("session_id").eq(params["session_id"])
            ).get("Items", [])
            return _r(200, {"attendance": rows})
        # list faculty's sessions
        sessions = SESSIONS.scan(
            FilterExpression=Attr("faculty_id").eq(uid)
        ).get("Items", [])
        return _r(200, {"sessions": sessions})
    else:
        # student: their own records
        rows = ATTENDANCE.scan(
            FilterExpression=Attr("student_id").eq(uid)
        ).get("Items", [])
        return _r(200, {"attendance": rows})

def _r(code, body):
    return {"statusCode": code,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(body)}