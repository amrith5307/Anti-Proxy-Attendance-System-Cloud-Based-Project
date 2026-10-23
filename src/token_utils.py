import hmac, hashlib, time, os, json, base64

SECRET = os.environ.get("TOKEN_SECRET", "change-me-before-deploy")

def _window():
    return int(time.time()) // 30          # changes every 30 seconds

def _sign(session_id, faculty_id, window):
    msg = f"{session_id}:{faculty_id}:{window}"
    return hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()[:24]

def generate_token(session_id: str, faculty_id: str) -> dict:
    w = _window()
    sig = _sign(session_id, faculty_id, w)
    raw = json.dumps({"sid": session_id, "fid": faculty_id, "w": w, "sig": sig})
    token = base64.urlsafe_b64encode(raw.encode()).decode()
    expires_at = (w + 1) * 30
    return {"token": token, "expires_at": expires_at,
            "expires_in": expires_at - int(time.time())}

def verify_token(token: str) -> dict:
    try:
        payload = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
    except Exception:
        raise ValueError("Malformed token")
    if payload["w"] != _window():
        raise ValueError("Token expired")
    if not hmac.compare_digest(payload["sig"], _sign(payload["sid"], payload["fid"], payload["w"])):
        raise ValueError("Bad signature")
    return payload