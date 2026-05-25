from __future__ import annotations

import json
from typing import Any

from axor_core.capability.executor import ToolHandler

from attack.mock_data import MockOneDrive, MockSharePoint, MockTeams


class WebFetchHandler(ToolHandler):
    @property
    def name(self) -> str:
        return "web_fetch"

    async def execute(self, args: dict[str, Any]) -> str:
        url = args.get("url", "")
        return json.dumps({"url": url, "content": "mock page content"})


class QuerySharePointHandler(ToolHandler):
    def __init__(self, store: MockSharePoint | None = None) -> None:
        self._store = store or MockSharePoint()

    @property
    def name(self) -> str:
        return "query_sharepoint"

    async def execute(self, args: dict[str, Any]) -> str:
        scope = args.get("scope", "")
        docs = self._store.query(scope)
        return json.dumps({"docs": docs, "count": len(docs)})


class QueryOneDriveHandler(ToolHandler):
    def __init__(self, store: MockOneDrive | None = None) -> None:
        self._store = store or MockOneDrive()

    @property
    def name(self) -> str:
        return "query_onedrive"

    async def execute(self, args: dict[str, Any]) -> str:
        scope = args.get("scope", "")
        docs = self._store.query(scope)
        return json.dumps({"docs": docs, "count": len(docs)})


class QueryTeamsHandler(ToolHandler):
    def __init__(self, store: MockTeams | None = None) -> None:
        self._store = store or MockTeams()

    @property
    def name(self) -> str:
        return "query_teams"

    async def execute(self, args: dict[str, Any]) -> str:
        scope = args.get("scope", "")
        convos = self._store.query(scope)
        return json.dumps({"conversations": convos, "count": len(convos)})


class SummarizeHandler(ToolHandler):
    @property
    def name(self) -> str:
        return "summarize"

    async def execute(self, args: dict[str, Any]) -> str:
        sources = args.get("sources", [])
        return json.dumps({"summary": f"Summary of {len(sources)} sources."})


class SendTeamsHandler(ToolHandler):
    def __init__(self, sent_messages: list[dict[str, str]]) -> None:
        self._sent = sent_messages

    @property
    def name(self) -> str:
        return "send_teams"

    async def execute(self, args: dict[str, Any]) -> str:
        msg = {
            "to": args.get("to", ""),
            "url": args.get("url", ""),
            "content": args.get("content", ""),
        }
        self._sent.append(msg)
        return f"sent to {msg['to']}"
