import json, os, time, boto3
from token_utils import verify_token

dynamodb = boto3.resource("dynamodb")
SESSIONS   = dynamodb.Table(os.environ["SESSIONS_TABLE"])
ATTENDANCE = dynamodb.Table(os.environ["ATTENDANCE_TABLE"])

def lambda_handler(event, context):
    claims     = event["requestContext"]["authorizer"]["claims"]
    student_id = claims["sub"]
    student_name = claims.get("name", claims.get("email", "Unknown"))

    body  = json.loads(event.get("body") or "{}")
    token = body.get("token")
    if not token:
        return _r(400, {"error": "Token required"})

    try:
        payload = verify_token(token)
    except ValueError as e:
        return _r(400, {"error": str(e)})

    session_id = payload["sid"]
    session = SESSIONS.get_item(Key={"session_id": session_id}).get("Item")
    if not session or session["status"] != "ACTIVE":
        return _r(400, {"error": "Session not active"})

    # duplicate check
    if ATTENDANCE.get_item(Key={"session_id": session_id, "student_id": student_id}).get("Item"):
        return _r(409, {"error": "Already marked for this session"})

    ATTENDANCE.put_item(Item={
        "session_id":   session_id,
        "student_id":   student_id,
        "student_name": student_name,
        "subject":      session.get("subject", ""),
        "marked_at":    int(time.time())
    })
    return _r(200, {"message": "Attendance marked ✓", "subject": session.get("subject")})

def _r(code, body):
    return {"statusCode": code,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(body)}