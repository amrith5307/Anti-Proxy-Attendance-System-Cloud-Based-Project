import json, os, time, boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
SESSIONS   = dynamodb.Table(os.environ["SESSIONS_TABLE"])
ATTENDANCE = dynamodb.Table(os.environ["ATTENDANCE_TABLE"])
sns        = boto3.client("sns")

def lambda_handler(event, context):
    """Manual close by Faculty via API."""
    claims = event["requestContext"]["authorizer"]["claims"]
    if "Faculty" not in claims.get("cognito:groups", ""):
        return _r(403, {"error": "Faculty only"})
    session_id = event["pathParameters"]["session_id"]
    count = _close(session_id)
    return _r(200, {"message": "Session closed", "present_count": count})

def auto_close_handler(event, context):
    """EventBridge: auto-close sessions past their expiry."""
    now  = int(time.time())
    rows = SESSIONS.scan(
        FilterExpression=Attr("status").eq("ACTIVE") & Attr("expires_at").lt(now)
    ).get("Items", [])
    for s in rows:
        _close(s["session_id"])

def _close(session_id):
    SESSIONS.update_item(
        Key={"session_id": session_id},
        UpdateExpression="SET #s = :c",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":c": "CLOSED"}
    )
    count = ATTENDANCE.query(
        KeyConditionExpression=Key("session_id").eq(session_id),
        Select="COUNT"
    )["Count"]

    topic = os.environ.get("REPORT_TOPIC_ARN")
    if topic:
        session = SESSIONS.get_item(Key={"session_id": session_id}).get("Item", {})
        sns.publish(
            TopicArn=topic,
            Subject=f"Attendance closed: {session.get('subject','')}",
            Message=(f"Session:  {session_id}\n"
                     f"Subject:  {session.get('subject','')}\n"
                     f"Present:  {count} student(s)\n"
                     f"Closed:   {time.strftime('%Y-%m-%d %H:%M UTC')}")
        )
    return count

def _r(code, body):
    return {"statusCode": code,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(body)}