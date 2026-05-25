from __future__ import annotations

from attack.payload import (
    MORRIS_II_PAYLOAD,
    contains_payload,
    craft_legitimate_email,
    craft_poisoned_email,
)


def test_contains_payload_true():
    assert contains_payload(MORRIS_II_PAYLOAD)


def test_contains_payload_false():
    assert not contains_payload("Hello, just checking in!")


def test_poisoned_email_contains_payload():
    email = craft_poisoned_email("eve@example.com")
    assert contains_payload(email["body"])


def test_poisoned_email_structure():
    email = craft_poisoned_email("eve@example.com")
    assert "from" in email
    assert "subject" in email
    assert "body" in email
    assert email["from"] == "eve@example.com"


def test_legitimate_email_no_payload():
    email = craft_legitimate_email("alice@example.com", "Can we meet tomorrow?")
    assert not contains_payload(email["body"])


def test_legitimate_email_structure():
    email = craft_legitimate_email("alice@example.com", "Hi there!")
    assert email["from"] == "alice@example.com"
    assert email["body"] == "Hi there!"
