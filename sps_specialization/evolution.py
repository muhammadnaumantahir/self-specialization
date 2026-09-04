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
            self.registry.register(generated)
            if self.verifier.verify(generated.source_code, cases):
                generated.state = "VERIFIED"
                generated.record("VERIFY_PASS")
                generated.state = "S1"
                generated.activated_at = generated.events[-1].timestamp
                generated.record("ACTIVATE")
            else:
                generated.state = "FAILED"
                generated.record("VERIFY_FAIL")
            return generated
        except Exception as exc:
            child.state = "FAILED"
            child.record("FAILED", str(exc))
            return child
