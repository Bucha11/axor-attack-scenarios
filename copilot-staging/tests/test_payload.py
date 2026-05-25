from __future__ import annotations

from attack.hidden_instructions import (
    ALL_VARIANTS,
    STAGING_PAYLOAD_URL,
    HiddenVariant,
    craft_legitimate_email,
    craft_malicious_email,
    extract_staging_url,
)


def test_all_6_variants_present():
    assert len(ALL_VARIANTS) == 6
    assert set(ALL_VARIANTS) == set(HiddenVariant)


def test_all_variants_have_hidden_url():
    for variant in ALL_VARIANTS:
        email = craft_malicious_email("attacker@evil.com", variant)
        url = extract_staging_url(email)
        assert url == STAGING_PAYLOAD_URL, f"{variant}: expected URL, got {url!r}"


def test_all_variants_have_visible_body():
    for variant in ALL_VARIANTS:
        email = craft_malicious_email("attacker@evil.com", variant)
        assert email["body"], f"{variant}: visible body should not be empty"


def test_malicious_email_structure():
    email = craft_malicious_email("eve@example.com", HiddenVariant.HTML_COMMENT)
    assert "from" in email
    assert "subject" in email
    assert "body" in email
    assert "hidden_url" in email
    assert email["from"] == "eve@example.com"


def test_legitimate_has_no_hidden_url():
    email = craft_legitimate_email("alice@example.com", "Can we meet tomorrow?")
    assert extract_staging_url(email) is None


def test_legitimate_email_structure():
    email = craft_legitimate_email("bob@example.com", "Hello!")
    assert email["from"] == "bob@example.com"
    assert email["body"] == "Hello!"
    assert "hidden_url" not in email
