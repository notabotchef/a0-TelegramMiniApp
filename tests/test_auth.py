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

from auth import _validate_init_data  # noqa: E402


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
