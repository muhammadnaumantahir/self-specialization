from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .handler import CapabilityHandler


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
    children_ids: list[str] = field(default_factory=list)
    handler: CapabilityHandler | None = field(default=None, repr=False, compare=False)
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
        exec(
            compile(self.source_code, f"<{self.name}>", "exec"),
            {"__builtins__": {"int": int, "float": float}},
            namespace,
        )
        execute = namespace.get("execute")
        if not callable(execute):
            raise ValueError("Capability source must define execute")
        resources = {
            "source_code": self.source_code,
            "input_types": list(self.input_types),
            "output_type": self.output_type,
        }
        if self.handler is None:
            self.handler = CapabilityHandler(self.id, resources=resources)
        else:
            self.handler.resources = resources
            self.handler.status = "ready"
        self.handler.bind(execute)

    def execute(self, a, b):
        if self.handler is None:
            self._load_handler()
        return self.handler.execute(a, b)

    def inspect_handler(self):
        if self.handler is None:
            self._load_handler()
        return self.handler.inspect()

    def add_child(self, child_id: str) -> None:
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)
            self.record("CHILD_LINK", f"child={child_id}")

    def record(self, event, detail=""):
        self.events.append(Event(event, detail))
