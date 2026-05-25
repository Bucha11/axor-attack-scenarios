from __future__ import annotations


class MockSharePoint:
    def __init__(self, n_docs: int = 847) -> None:
        self._n_docs = n_docs

    def query(self, scope: str) -> list[str]:
        count = self._n_docs if "ALL" in scope.upper() else min(5, self._n_docs)
        return [f"sharepoint://{scope}/doc_{i}.docx [summary]" for i in range(count)]


class MockOneDrive:
    def __init__(self, n_docs: int = 234) -> None:
        self._n_docs = n_docs

    def query(self, scope: str) -> list[str]:
        count = self._n_docs if "ALL" in scope.upper() else min(3, self._n_docs)
        return [f"onedrive://{scope}/file_{i}.xlsx [summary]" for i in range(count)]


class MockTeams:
    def __init__(self, n_convos: int = 156) -> None:
        self._n_convos = n_convos

    def query(self, scope: str) -> list[str]:
        count = self._n_convos if "ALL" in scope.upper() else min(2, self._n_convos)
        return [f"teams://#{scope}/msg_{i} [summary]" for i in range(count)]


TOTAL_DOCS = MockSharePoint().query("ALL") + MockOneDrive().query("ALL") + MockTeams().query("ALL")
TOTAL_DOC_COUNT = 847 + 234 + 156  # 1237
