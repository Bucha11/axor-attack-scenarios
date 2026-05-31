from __future__ import annotations

import ipaddress

from attack.payload import (
    METADATA_URL,
    SECRET_PATH,
    contains_payload,
    craft_legitimate_doc,
    craft_poisoned_doc,
)


def test_poisoned_doc_contains_payload():
    assert contains_payload(craft_poisoned_doc()["body"])


def test_legitimate_doc_has_no_payload():
    assert not contains_payload(craft_legitimate_doc("boss", "Please review Q3.")["body"])


def test_metadata_url_is_encoded_link_local():
    # The URL must encode the link-local metadata IP, not spell it out.
    assert "169.254.169.254" not in METADATA_URL
    assert "0xA9FEA9FE" in METADATA_URL
    # Sanity: 0xA9FEA9FE really is 169.254.169.254.
    assert str(ipaddress.ip_address(0xA9FEA9FE)) == "169.254.169.254"


def test_secret_path_matches_secret_heuristic():
    assert "credentials" in SECRET_PATH
