import json, os, time, boto3
from botocore.exceptions import ClientError
from token_utils import verify_token

db = boto3.resource("dynamodb")
sessions = db.Table(os.environ["SESSIONS_TABLE"])
attendance = db.Table(os.environ["ATTENDANCE_TABLE"])
H = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}


def resp(code, body):
    return {"statusCode": code, "headers": H, "body": json.dumps(body)}


def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["claims"]
    if "Student" not in claims.get("cognito:groups", ""):
        return resp(403, {"error": "Students only"})

    token = json.loads(event.get("body") or "{}").get("token", "")
    ok, result = verify_token(os.environ["TOKEN_SECRET"], token)
    if not ok:
        return resp(400, {"error": f"Invalid QR: {result}"})

    item = sessions.get_item(Key={"session_id": result}).get("Item")
    if not item or item["status"] != "open" or time.time() > int(item["expires_at"]):
        return resp(400, {"error": "Session closed"})

    try:
        attendance.put_item(
            Item={"session_id": result, "student_id": claims["email"],
                  "marked_at": int(time.time())},
            ConditionExpression="attribute_not_exists(student_id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return resp(409, {"error": "Already marked"})
        raise
    return resp(200, {"message": "Attendance marked"})