class CapabilityDispatcher:
    """Resolve a request to an existing capability or trigger specialization."""

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

    def execute(self, name, a, b, specialization=None):
        """Execute a request such as multiply(6, 7)."""
        input_types = [self._type_name(a), self._type_name(b)]

        capability = self.registry.find(name, input_types, active_only=True)
        if capability is None:
            parent = self._find_parent(name)
            if parent is not None:
                capability = self.registry.find(parent.name, input_types, active_only=True)

        if capability is not None:
            return capability.execute(a, b), capability

        if specialization is None:
            raise LookupError(f"No active capability for {name}{tuple(input_types)}")

        target_name, output_type, cases = specialization
        parent = self._find_parent(name)
        if parent is None:
            raise LookupError(f"No parent capability for operation '{name}'")

        result = self.evolution_engine.specialize_request(
            parent.id, target_name, input_types, output_type, cases
        )
        if result.state != "S1":
            raise RuntimeError(f"Specialization failed: {result.state}")
        return result.execute(a, b), result
