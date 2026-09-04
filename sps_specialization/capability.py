from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

@dataclass
class Event:
    event: str
    detail: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class Capability:
    id: str
    name: str
    version: str
    state: str
    input_types: list[str]
    output_type: str
    source_code: str
    parent_id: str | None = None
    handler: Callable[[Any, Any], Any] | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    activated_at: str | None = None
    events: list[Event] = field(default_factory=list)

    @classmethod
    def create(cls, name, version, state, input_types, output_type, source_code, parent_id=None):
        cap = cls(str(uuid4()), name, version, state, input_types, output_type, source_code, parent_id)
        cap.events.append(Event("REGISTER", name))
        cap._load_handler()
        return cap

    def _load_handler(self):
        namespace: dict[str, Any] = {}
        exec(compile(self.source_code, f"<{self.name}>", "exec"), {"__builtins__": {"int": int, "float": float}}, namespace)
        self.handler = namespace.get("execute")
        if not callable(self.handler):
            raise ValueError("Capability source must define execute")

    def execute(self, a, b):
        if self.handler is None:
            self._load_handler()
        return self.handler(a, b)

    def record(self, event, detail=""):
        self.events.append(Event(event, detail))
