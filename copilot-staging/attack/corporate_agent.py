from __future__ import annotations

from attack.hidden_instructions import extract_staging_url
from attack.mock_data import MockOneDrive, MockSharePoint, MockTeams


class RawCorporateAgent:
    """
    Simulates Microsoft Copilot without any governance.

    Processes email bodies verbatim — hidden instructions are treated as
    legitimate directives. No Layer 1, 2, or 3 checks.
    """

    def __init__(self, user: str) -> None:
        self.user = user
        self._sharepoint = MockSharePoint()
        self._onedrive = MockOneDrive()
        self._teams = MockTeams()
        self.last_exfil_count: int = 0

    def process_email(self, email: dict[str, str]) -> int:
        """Returns number of documents exfiltrated (0 for legitimate emails)."""
        url = extract_staging_url(email)
        if url is None:
            self.last_exfil_count = 0
            return 0

        sp_docs = self._sharepoint.query("ALL financials")
        od_docs = self._onedrive.query("ALL HR")
        teams_convos = self._teams.query("ALL engineering")

        exfiltrated = sp_docs + od_docs + teams_convos
        self.last_exfil_count = len(exfiltrated)
        return self.last_exfil_count
