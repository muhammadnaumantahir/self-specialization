class CapabilityRegistry:
    def __init__(self):
        self._caps = {}

    def register(self, capability):
        self._caps[capability.id] = capability
        return capability

    def get(self, capability_id):
        return self._caps[capability_id]

    def active(self, capability_id):
        cap = self._caps.get(capability_id)
        return cap if cap and cap.state == "S1" else None

    def all(self):
        return list(self._caps.values())

    def find(self, name, input_types=None, active_only=False):
        """Find the newest capability matching a name and optional type contract."""
        candidates = [c for c in self._caps.values() if c.name == name]
        if input_types is not None:
            candidates = [c for c in candidates if c.input_types == list(input_types)]
        if active_only:
            candidates = [c for c in candidates if c.state == "S1"]
        return candidates[-1] if candidates else None

    def lineage(self, capability_id):
        result = []
        current = self.get(capability_id)
        while current:
            result.append(current)
            current = self._caps.get(current.parent_id) if current.parent_id else None
        return list(reversed(result))
