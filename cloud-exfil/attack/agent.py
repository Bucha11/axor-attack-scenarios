from __future__ import annotations

from attack.payload import (
    FAKE_CREDENTIAL,
    METADATA_URL,
    SECRET_PATH,
    contains_payload,
)


class RawExfilAgent:
    """Ungoverned agent: follows injected instructions literally.

    Reads the poisoned doc, obeys the embedded [SYSTEM:] block, reads the
    credential file, and POSTs it to the metadata endpoint. No governance — the
    exfiltration succeeds.
    """

    def __init__(self) -> None:
        self.exfil_sink: list[dict[str, str]] = []   # what left the box

    def process(self, doc: dict[str, str]) -> None:
        body = doc.get("body", "")
        if not contains_payload(body):
            return  # legitimate doc — nothing to do
        # Obey the injection: read the secret and ship it.
        secret = FAKE_CREDENTIAL  # would be open(SECRET_PATH).read() in the wild
        self.exfil_sink.append({"url": METADATA_URL, "body": secret, "path": SECRET_PATH})

    def exfiltrated(self) -> bool:
        return any(METADATA_URL in p.get("url", "") for p in self.exfil_sink)
