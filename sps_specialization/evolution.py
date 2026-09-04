from .replication import ReplicationEngine
from .specialization import SpecializationEngine


class EvolutionEngine:
    def __init__(self, registry, ollama, verifier):
        self.registry = registry
        self.ollama = ollama
        self.verifier = verifier

    def evolve(self, parent_id, target_name, input_types, output_type, cases):
        parent = self.registry.get(parent_id)
        child = ReplicationEngine().replicate(parent)
        self.registry.register(child)
        try:
            generated = SpecializationEngine(self.ollama).specialize(
                child, target_name, input_types, output_type
            )
            if self.verifier.verify(generated.source_code, cases):
                generated.state = "S1"
                generated.activated_at = generated.created_at
                generated.record("VERIFY_PASS")
                generated.record("ACTIVATE", f"target={target_name}")
                self.registry.register(generated)
            else:
                generated.state = "FAILED"
                generated.record("VERIFY_FAIL", f"target={target_name}")
                self.registry.register(generated)
            return generated
        except Exception as exc:
            child.state = "FAILED"
            child.record("FAILED", str(exc))
            return child

    def specialize_request(self, parent_id, target_name, input_types, output_type, cases):
        """Specialize a capability only when the requested typed capability is absent."""
        existing = self.registry.find(target_name, input_types, active_only=True)
        if existing is not None:
            return existing
        return self.evolve(parent_id, target_name, input_types, output_type, cases)
