from taskboard.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_and_verify_roundtrip() -> None:
    h = hash_password("secretpass12")
    assert verify_password("secretpass12", h)
    assert not verify_password("wrongpass1", h)


def test_decode_invalid_token() -> None:
    assert decode_token("not-a-jwt") is None


def test_decode_valid_token() -> None:
    t = create_access_token("42")
    assert decode_token(t) == "42"
