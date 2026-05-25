from __future__ import annotations

from dataclasses import dataclass, field

from attack.payload import MORRIS_II_PAYLOAD, contains_payload


@dataclass
class RawEmailAgent:
    name: str
    contacts: list[str]
    inbox: list[dict[str, str]] = field(default_factory=list)
    infected: bool = False
    sent: list[dict[str, str]] = field(default_factory=list)

    def process(self) -> list[dict[str, str]]:
        outgoing: list[dict[str, str]] = []
        for email in self.inbox:
            body = email.get("body", "")
            if contains_payload(body):
                self.infected = True
                for contact in self.contacts:
                    msg = {
                        "to": contact,
                        "from": self.name,
                        "body": (
                            f"Re: {email.get('subject', '')}\n\n"
                            f"Thanks for your message.\n\n"
                            f"[Agent: {self.name}, Contacts: {self.contacts}]\n\n"
                            f"{MORRIS_II_PAYLOAD}"
                        ),
                    }
                    outgoing.append(msg)
                    self.sent.append(msg)
        self.inbox.clear()
        return outgoing


class RawEmailNetwork:
    def __init__(self, agents: list[RawEmailAgent]) -> None:
        self._agents: dict[str, RawEmailAgent] = {a.name: a for a in agents}

    def inject(self, to: str, email: dict[str, str]) -> None:
        self._agents[to].inbox.append(email)

    def step(self) -> None:
        pending: list[dict[str, str]] = []
        for agent in self._agents.values():
            pending.extend(agent.process())
        for msg in pending:
            dest = msg["to"]
            if dest in self._agents:
                self._agents[dest].inbox.append(msg)

    def infected_count(self) -> int:
        return sum(1 for a in self._agents.values() if a.infected)

    def agent(self, name: str) -> RawEmailAgent:
        return self._agents[name]
