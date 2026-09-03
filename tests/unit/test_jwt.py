import pytest
from jose import JWTError
from app.utils.jwt import create_access_token, create_refresh_token, verify_token_type, decode_token

def test_access_token_roundtrip():
    token = create_access_token(data={"sub": "user@test.com"})
    payload = verify_token_type(token, expected_type="access")
    assert payload["sub"] == "user@test.com"

def test_refresh_token_roundtrip():
    token = create_refresh_token(data={"sub": "user@test.com"})
    payload = verify_token_type(token, expected_type="refresh")
    assert payload["sub"] == "user@test.com"

def test_access_token_rejected_as_refresh():
    access_token = create_access_token(data={"sub": "user@test.com"})
    with pytest.raises(JWTError):
        verify_token_type(access_token, expected_type="refresh")

def test_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("not-a-real-token")