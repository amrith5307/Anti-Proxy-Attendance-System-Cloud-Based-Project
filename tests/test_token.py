import sys
sys.path.insert(0, "src")
from token_utils import make_token, verify_token

S = "test-secret"


def test_valid():
    t = make_token(S, "sess1", now=1000)
    assert verify_token(S, t, now=1010) == (True, "sess1")


def test_expired_screenshot():
    t = make_token(S, "sess1", now=1000)
    assert verify_token(S, t, now=1100) == (False, "expired")


def test_tampered():
    t = make_token(S, "sess1", now=1000)
    assert verify_token(S, t.replace("sess1", "sess2"), now=1005)[0] is False


def test_wrong_secret():
    t = make_token("other", "sess1", now=1000)
    assert verify_token(S, t, now=1005)[0] is False