from copy import deepcopy
from .capability import Capability

class ReplicationEngine:
    def replicate(self, parent: Capability) -> Capability:
        child = Capability.create(
            f"{parent.name}-child", parent.version, "S0-C",
            list(parent.input_types), parent.output_type, parent.source_code, parent.id
        )
        child.events = [e for e in deepcopy(parent.events) if e.event != "REGISTER"]
        child.record("REPLICATE", f"parent={parent.id}")
        return child
