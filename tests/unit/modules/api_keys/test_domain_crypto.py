import pytest

from src.modules.api_keys.domain.value_objects import (
    KeyHash,
    KeyPrefix,
    RawApiKey,
)
from src.shared.infrastructure.security.hmac_key_hasher import HmacKeyHasher


class TestRawApiKey:
    def test_generate_produces_valid_format(self) -> None:
        raw = RawApiKey.generate()
        assert str(raw).startswith("pk_")
        assert len(raw.prefix.value) == 11
        assert len(raw.secret) >= 43

    def test_generate_produces_unique_keys(self) -> None:
        keys = {str(RawApiKey.generate()) for _ in range(100)}
        assert len(keys) == 100

    def test_prefix_extracts_first_12_chars(self) -> None:
        raw = RawApiKey("pk_a1b2c3d4_" + "x" * 43)
        assert raw.prefix == KeyPrefix("pk_a1b2c3d4")

    def test_secret_extracts_after_13th_char(self) -> None:
        raw = RawApiKey("pk_a1b2c3d4_" + "x" * 43)
        assert raw.secret == "x" * 43

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError):
            RawApiKey("not-a-valid-key")

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValueError):
            RawApiKey("pk_a1b2c3d4_short")


class TestKeyPrefix:
    def test_valid_prefix(self) -> None:
        p = KeyPrefix("pk_a1b2c3d4")
        assert str(p) == "pk_a1b2c3d4"

    def test_invalid_prefix_no_pk(self) -> None:
        with pytest.raises(ValueError):
            KeyPrefix("xx_a1b2c3d4")

    def test_invalid_prefix_wrong_length(self) -> None:
        with pytest.raises(ValueError):
            KeyPrefix("pk_a1b2c3d")


class TestKeyHash:
    def test_valid_hash(self) -> None:
        h = KeyHash("a" * 64)
        assert str(h) == "a" * 64

    def test_wrong_length_raises(self) -> None:
        with pytest.raises(ValueError):
            KeyHash("a" * 63)

    def test_non_hex_raises(self) -> None:
        with pytest.raises(ValueError):
            KeyHash("z" * 64)


class TestHmacKeyHasher:
    @pytest.fixture()
    def hasher(self) -> HmacKeyHasher:
        return HmacKeyHasher(pepper="a" * 32)

    def test_hash_is_deterministic(
        self, hasher: HmacKeyHasher
    ) -> None:
        h1 = hasher.hash("my_secret")
        h2 = hasher.hash("my_secret")
        assert h1 == h2

    def test_hash_is_64_hex_chars(
        self, hasher: HmacKeyHasher
    ) -> None:
        h = hasher.hash("my_secret")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_verify_true_on_match(
        self, hasher: HmacKeyHasher
    ) -> None:
        h = hasher.hash("my_secret")
        assert hasher.verify("my_secret", h) is True

    def test_verify_false_on_mismatch(
        self, hasher: HmacKeyHasher
    ) -> None:
        h = hasher.hash("my_secret")
        assert hasher.verify("wrong_secret", h) is False

    def test_different_peppers_produce_different_hashes(self) -> None:
        h1 = HmacKeyHasher("a" * 32).hash("secret")
        h2 = HmacKeyHasher("b" * 32).hash("secret")
        assert h1 != h2

    def test_short_pepper_raises(self) -> None:
        with pytest.raises(ValueError):
            HmacKeyHasher(pepper="short")

    def test_verify_with_zero_hash_returns_false(
        self, hasher: HmacKeyHasher
    ) -> None:
        assert hasher.verify("any_secret", "0" * 64) is False