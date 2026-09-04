class CapabilityDispatcher:
    """Resolve requests or trigger self-specialization when a typed capability is missing."""

    def __init__(self, registry, evolution_engine):
        self.registry = registry
        self.evolution_engine = evolution_engine

    @staticmethod
    def _type_name(value):
        return (
            "float" if isinstance(value, float)
            else "int" if isinstance(value, int) and not isinstance(value, bool)
            else type(value).__name__
        )

    @staticmethod
    def _operation_alias(name):
        normalized = name.replace("_", "").replace("-", "").lower()
        if normalized in {"multiply", "multiplication", "integermultiplication"}:
            return "multiply"
        return normalized

    def _find_parent(self, name):
        parent = self.registry.find(name, active_only=False)
        if parent is not None:
            return parent
        alias = self._operation_alias(name)
        for capability in self.registry.all():
            if self._operation_alias(capability.name) == alias:
                return capability
        return None

    @staticmethod
    def _is_executable(capability):
        return capability is not None and capability.state in {"S0", "S0-C", "S1"}

    @staticmethod
    def _failure_detail(capability):
        """Return the most recent failure event so the caller sees the root cause."""
        if capability is None:
            return "unknown failure"
        for event in reversed(capability.events):
            if event.event in {"FAILED", "VERIFY_FAIL"}:
                return event.detail or "no failure detail recorded"
        return "no failure detail recorded"

    def _find_executable(self, name, input_types):
        capability = self.registry.find(name, input_types, active_only=False)
        if self._is_executable(capability):
            return capability

        alias = self._operation_alias(name)
        candidates = [
            c for c in self.registry.all()
            if self._operation_alias(c.name) == alias
            and c.input_types == list(input_types)
            and self._is_executable(c)
        ]
        return candidates[-1] if candidates else None

    def execute(self, name, a, b, specialization=None):
        """Execute a request such as multiply(6, 7)."""
        input_types = [self._type_name(a), self._type_name(b)]

        capability = self._find_executable(name, input_types)
        if capability is not None:
            return capability.execute(a, b), capability

        if specialization is None:
            raise LookupError(f"No executable capability for {name}{tuple(input_types)}")

        target_name, output_type, cases = specialization
        parent = self._find_parent(name)
        if parent is None:
            raise LookupError(f"No parent capability for operation '{name}'")

        result = self.evolution_engine.specialize_request(
            parent.id, target_name, input_types, output_type, cases
        )
        if result.state != "S1":
            reason = self._failure_detail(result)
            raise RuntimeError(
                f"Specialization failed: state={result.state}; reason={reason}"
            )
        return result.execute(a, b), result
