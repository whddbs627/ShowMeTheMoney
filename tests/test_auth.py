"""인증/보안 테스트"""
import pytest
from backend.auth import hash_password, verify_password, create_token, encrypt_key, decrypt_key


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "test_password_123"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        # 다른 salt → 다른 해시
        assert h1 != h2

    def test_invalid_hash_format(self):
        assert verify_password("test", "invalid_hash") is False
        assert verify_password("test", "") is False


class TestJWT:
    def test_create_token(self):
        token = create_token(1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_different_users(self):
        t1 = create_token(1)
        t2 = create_token(2)
        assert t1 != t2


class TestEncryption:
    def test_encrypt_decrypt(self):
        plain = "my_secret_api_key"
        encrypted = encrypt_key(plain)
        assert encrypted != plain
        assert decrypt_key(encrypted) == plain

    def test_different_encryptions(self):
        plain = "same_key"
        e1 = encrypt_key(plain)
        e2 = encrypt_key(plain)
        # Fernet은 매번 다른 암호문 생성
        assert e1 != e2
        # 복호화하면 같은 값
        assert decrypt_key(e1) == decrypt_key(e2) == plain
