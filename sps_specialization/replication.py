from copy import deepcopy

from .capability import Capability


class ReplicationEngine:
    def replicate(self, source: Capability, parent_id: str | None = None) -> Capability:
        """Create an S0-C runtime copy without making it a final hierarchy node."""
        child = Capability.create(
            f"{source.name}-copy", source.version, "S0-C",
            list(source.input_types), source.output_type, source.source_code,
            parent_id if parent_id is not None else source.id,
        )
        child.events = [e for e in deepcopy(source.events) if e.event != "REGISTER"]
        child.record("REPLICATE", f"source={source.id}")
        return child
