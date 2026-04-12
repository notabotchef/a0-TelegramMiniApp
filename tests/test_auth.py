"""
Unit tests for a0-plugin/_miniapp/api/auth.py

Tests the HMAC-SHA256 initData validation using the exact algorithm from
Telegram's documentation:
  https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

Run with:
    python -m pytest tests/test_auth.py -v
"""

import hmac
import hashlib
import sys
import os
import urllib.parse

# Add plugin dir to path so we can import auth.py directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'a0-plugin', '_miniapp', 'api'))

from auth import _validate_init_data, _extract_user_id, _get_telegram_config  # noqa: E402


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def build_init_data(bot_token: str, fields: dict) -> str:
    """
    Build a valid initData string signed with bot_token.
    Mirrors the exact signing algorithm Telegram uses.
    """
    # Build data-check string from sorted fields
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(fields.items())
    )

    # secret_key = HMAC-SHA256(key=b"WebAppData", msg=bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # hash = HMAC-SHA256(key=secret_key, msg=data_check_string)
    hash_value = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # Encode all fields + hash as URL-encoded query string
    all_fields = {**fields, "hash": hash_value}
    return urllib.parse.urlencode(all_fields)


# ─── TEST VECTORS ────────────────────────────────────────────────────────────

BOT_TOKEN = "7654321098:AAFbKzExampleBotTokenForTesting123"

SAMPLE_FIELDS = {
    "query_id":  "AAHdF6IQAAAAAN0XohBz123",
    "user":      '{"id":123456789,"first_name":"Test","last_name":"User","username":"testuser","language_code":"en"}',
    "auth_date": "1712000000",
}


# ─── TESTS ───────────────────────────────────────────────────────────────────

class TestValidateInitData:

    def test_valid_signature_returns_true(self):
        """Correctly signed initData must pass validation."""
        init_data = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        assert _validate_init_data(init_data, BOT_TOKEN) is True

    def test_wrong_bot_token_returns_false(self):
        """initData signed with one token must fail validation against a different token."""
        init_data = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        wrong_token = "9999999999:ZZZwrongTokenZZZ"
        assert _validate_init_data(init_data, wrong_token) is False

    def test_tampered_field_returns_false(self):
        """Modifying any field after signing must invalidate the hash."""
        init_data = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        # Tamper: change auth_date in the URL-encoded string
        tampered = init_data.replace("auth_date=1712000000", "auth_date=9999999999")
        assert _validate_init_data(tampered, BOT_TOKEN) is False

    def test_missing_hash_returns_false(self):
        """initData without a hash field must return False."""
        fields_no_hash = urllib.parse.urlencode(SAMPLE_FIELDS)
        assert _validate_init_data(fields_no_hash, BOT_TOKEN) is False

    def test_empty_string_returns_false(self):
        """Empty string must return False, not raise an exception."""
        assert _validate_init_data("", BOT_TOKEN) is False

    def test_hash_only_returns_false(self):
        """A string that is only a hash with no other fields must return False."""
        init_data = "hash=abc123def456"
        assert _validate_init_data(init_data, BOT_TOKEN) is False

    def test_single_field_plus_hash(self):
        """Minimal valid initData with a single field must pass."""
        minimal_fields = {"auth_date": "1712000000"}
        init_data = build_init_data(BOT_TOKEN, minimal_fields)
        assert _validate_init_data(init_data, BOT_TOKEN) is True

    def test_wrong_hash_value_returns_false(self):
        """Correct structure but wrong hash hex value must return False."""
        init_data = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        # Replace the actual hash with a zeroed-out one of the same length
        bad_hash = "0" * 64
        tampered = urllib.parse.urlencode({**SAMPLE_FIELDS, "hash": bad_hash})
        assert _validate_init_data(tampered, BOT_TOKEN) is False

    def test_field_order_does_not_matter(self):
        """Validation must be order-independent (sorted before hashing)."""
        # Reverse the field order in the query string
        fields_reversed = dict(reversed(list(SAMPLE_FIELDS.items())))
        init_data_normal   = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        init_data_reversed = build_init_data(BOT_TOKEN, fields_reversed)
        # Both should produce the same hash and both should validate
        assert _validate_init_data(init_data_normal,   BOT_TOKEN) is True
        assert _validate_init_data(init_data_reversed, BOT_TOKEN) is True

    def test_returns_bool_not_truthy(self):
        """Return value must be exactly True or False, not a truthy/falsy value."""
        init_data = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        result = _validate_init_data(init_data, BOT_TOKEN)
        assert result is True
        assert type(result) is bool


# ─── P2 FIX: multi-bot token validation ──────────────────────────────────────

class TestMultiBotValidation:

    def test_valid_against_second_token(self):
        """initData signed with bot2 must validate when bot2 is in the list."""
        bot2 = "1111111111:BBBsecondBotTokenForTesting456"
        init_data = build_init_data(bot2, SAMPLE_FIELDS)
        # Validates against bot2 but not BOT_TOKEN
        assert _validate_init_data(init_data, BOT_TOKEN) is False
        assert _validate_init_data(init_data, bot2) is True

    def test_any_match_in_list(self):
        """any() over multiple tokens: match on second should succeed."""
        bot2 = "1111111111:BBBsecondBotTokenForTesting456"
        init_data = build_init_data(bot2, SAMPLE_FIELDS)
        tokens = [BOT_TOKEN, bot2]
        assert any(_validate_init_data(init_data, t) for t in tokens) is True

    def test_no_match_in_list_fails(self):
        """If no token in the list matches, validation must fail."""
        init_data = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        wrong_tokens = ["9999999999:ZZZ1", "8888888888:ZZZ2"]
        assert any(_validate_init_data(init_data, t) for t in wrong_tokens) is False


# ─── P1 FIX: user authorization ──────────────────────────────────────────────

class TestExtractUserId:

    def test_extracts_id_from_valid_user_field(self):
        """_extract_user_id must return the integer id from initData user field."""
        init_data = build_init_data(BOT_TOKEN, SAMPLE_FIELDS)
        assert _extract_user_id(init_data) == 123456789

    def test_returns_none_on_missing_user_field(self):
        """initData without a user field must return None."""
        minimal = build_init_data(BOT_TOKEN, {"auth_date": "1712000000"})
        assert _extract_user_id(minimal) is None

    def test_returns_none_on_malformed_user_json(self):
        """Malformed user JSON must return None, not raise."""
        fields = {**SAMPLE_FIELDS, "user": "not-valid-json"}
        init_data = build_init_data(BOT_TOKEN, fields)
        assert _extract_user_id(init_data) is None

    def test_returns_none_on_empty_string(self):
        """Empty initData must return None."""
        assert _extract_user_id("") is None
