from auth.password_utils import hash_password, verify_password

def test_bcrypt_roundtrip():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)