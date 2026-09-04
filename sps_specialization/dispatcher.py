from .capability import Capability


class CapabilityDispatcher:
    """Resolve a request to an existing capability or ask the evolution engine to specialize one."""

    def __init__(self, registry, evolution_engine):
        self.registry = registry
        self.evolution_engine = evolution_engine

    @staticmethod
    def _type_name(value):
        return "float" if isinstance(value, float) else "int" if isinstance(value, int) and not isinstance(value, bool) else type(value).__name__

    def execute(self, name, a, b, specialization=None):
        input_types = [self._type_name(a), self._type_name(b)]
        capability = self.registry.find(name, input_types, active_only=True)
        if capability is not None:
            return capability.execute(a, b), capability

        if specialization is None:
            raise LookupError(f"No active capability for {name}{tuple(input_types)}")

        target_name, output_type, cases = specialization
        parent = self.registry.find(name, active_only=False)
        if parent is None:
            raise LookupError(f"No parent capability named {name}")
        result = self.evolution_engine.specialize_request(
            parent.id, target_name, input_types, output_type, cases
        )
        if result.state != "S1":
            raise RuntimeError(f"Specialization failed: {result.state}")
        return result.execute(a, b), result
