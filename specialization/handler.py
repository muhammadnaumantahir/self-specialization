from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CapabilityHandler:
    """Runtime owner for a capability's execution and lightweight resources."""

    capability_id: str
    resources: dict[str, Any] = field(default_factory=dict)
    status: str = "ready"
    _execute: Callable[[Any, Any], Any] | None = field(default=None, repr=False, compare=False)

    def bind(self, execute: Callable[[Any, Any], Any]) -> None:
        if not callable(execute):
            raise ValueError("Capability handler requires a callable execute function")
        self._execute = execute

    def execute(self, a: Any, b: Any) -> Any:
        if self._execute is None:
            raise RuntimeError("Capability handler has no executable function")
        return self._execute(a, b)

    def inspect(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "status": self.status,
            "resources": dict(self.resources),
        }
