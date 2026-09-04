class CapabilityDispatcher:
    """Resolve typed requests and trigger specialization under the general capability."""

    GENERAL_PARENT_NAME = "SerializeCapability"

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
        if normalized in {"multiply", "multiplication", "integermultiplication", "floatmultiplication"}:
            return "multiply"
        return normalized

    def _find_general_parent(self, name):
        general = self.registry.find(self.GENERAL_PARENT_NAME, active_only=False)
        if general is not None:
            return general
        return self.registry.find(name, active_only=False)

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

    def _find_source_for_specialization(self, name):
        alias = self._operation_alias(name)
        candidates = [
            c for c in self.registry.all()
            if self._operation_alias(c.name) == alias
            and c.state in {"S0", "S1"}
            and c.name != self.GENERAL_PARENT_NAME
        ]
        return candidates[-1] if candidates else None

    @staticmethod
    def _is_executable(capability):
        return capability is not None and capability.state in {"S0", "S0-C", "S1"}

    def execute(self, name, a, b, specialization=None):
        """Execute a request such as multiply(6, 7)."""
        input_types = [self._type_name(a), self._type_name(b)]

        capability = self._find_executable(name, input_types)
        if capability is not None:
            return capability.execute(a, b), capability

        if specialization is None:
            raise LookupError(
                f"No executable capability for {name}{tuple(input_types)}"
            )

        target_name, output_type, cases = specialization
        general_parent = self._find_general_parent(name)
        source = self._find_source_for_specialization(name)
        if general_parent is None:
            raise LookupError(f"No general parent capability for operation '{name}'")
        if source is None:
            raise LookupError(f"No source capability for specialization of '{name}'")

        result = self.evolution_engine.specialize_request(
            general_parent.id,
            target_name,
            input_types,
            output_type,
            cases,
            source_capability_id=source.id,
        )
        if result.state != "S1":
            failure_events = [
                event.detail for event in result.events if event.event in {"VERIFY_FAIL", "FAILED"}
            ]
            reason = failure_events[-1] if failure_events else "no failure detail recorded"
            raise RuntimeError(
                f"Specialization failed: state={result.state}; reason={reason}"
            )

        return result.execute(a, b), result
