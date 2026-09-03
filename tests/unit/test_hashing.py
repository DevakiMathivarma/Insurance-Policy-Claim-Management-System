from app.utils.hashing import hash_password, verify_password

def test_hash_and_verify():
    hashed = hash_password("MyPassword123")
    assert hashed != "MyPassword123"
    assert verify_password("MyPassword123", hashed) is True
    assert verify_password("WrongPassword", hashed) is False