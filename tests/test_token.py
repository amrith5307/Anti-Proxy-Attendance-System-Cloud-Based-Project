import os, time, pytest
os.environ["TOKEN_SECRET"] = "test-secret"

from src.token_utils import generate_token, verify_token

def test_roundtrip():
    result = generate_token("sess-1", "faculty-1")
    assert "token" in result
    payload = verify_token(result["token"])
    assert payload["sid"] == "sess-1"
    assert payload["fid"] == "faculty-1"

def test_bad_signature():
    result = generate_token("sess-1", "faculty-1")
    bad = result["token"][:-4] + "XXXX"
    with pytest.raises(ValueError, match="Bad signature"):
        verify_token(bad)

def test_malformed():
    with pytest.raises(ValueError, match="Malformed"):
        verify_token("not-a-valid-token")