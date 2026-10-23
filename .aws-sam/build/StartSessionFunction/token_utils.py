import hmac, hashlib, time

MAX_AGE = 35  # 30s rotation + 5s grace


def _sig(secret: str, msg: str) -> str:
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


def make_token(secret: str, session_id: str, now: int = None) -> str:
    ts = str(now if now is not None else int(time.time()))
    msg = f"{session_id}.{ts}"
    return f"{msg}.{_sig(secret, msg)}"


def verify_token(secret: str, token: str, now: int = None):
    """Returns (ok, session_id_or_error)."""
    try:
        session_id, ts, sig = token.rsplit(".", 2)
        ts_int = int(ts)
    except ValueError:
        return False, "malformed"
    if not hmac.compare_digest(sig, _sig(secret, f"{session_id}.{ts}")):
        return False, "bad_signature"
    age = (now if now is not None else int(time.time())) - ts_int
    if age > MAX_AGE or age < -5:
        return False, "expired"
    return True, session_id