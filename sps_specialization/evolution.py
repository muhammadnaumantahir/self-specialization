from .replication import ReplicationEngine
from .specialization import SpecializationEngine


class EvolutionEngine:
    def __init__(self, registry, ollama, verifier):
        self.registry = registry
        self.ollama = ollama
        self.verifier = verifier

    def evolve(self, parent_id, target_name, input_types, output_type, cases, source_capability_id=None):
        """Replicate a source capability and publish its specialization under the general parent."""
        general_parent = self.registry.get(parent_id)
        source = self.registry.get(source_capability_id) if source_capability_id else general_parent
        child = ReplicationEngine().replicate(source, parent_id=general_parent.id)

        try:
            generated = SpecializationEngine(self.ollama).specialize(
                child,
                target_name,
                input_types,
                output_type,
                final_parent_id=general_parent.id,
            )
        except Exception as exc:
            child.state = "FAILED"
            child.record(
                "FAILED",
                f"SPECIALIZATION_ERROR: {type(exc).__name__}: {exc}",
            )
            return child

        try:
            verified, reason = self.verifier.verify_detailed(
                generated.source_code, cases
            )
            if verified:
                generated.state = "S1"
                generated.activated_at = generated.created_at
                generated.record("VERIFY_PASS", reason)
                generated.record("ACTIVATE", f"target={target_name}")
                self.registry.register(generated)
            else:
                generated.state = "FAILED"
                generated.record("VERIFY_FAIL", reason)
                self.registry.register(generated)
            return generated
        except Exception as exc:
            generated.state = "FAILED"
            generated.record(
                "FAILED",
                f"VERIFICATION_ERROR: {type(exc).__name__}: {exc}",
            )
            self.registry.register(generated)
            return generated

    def specialize_request(self, parent_id, target_name, input_types, output_type, cases, source_capability_id=None):
        """Specialize only when the requested typed capability is absent."""
        existing = self.registry.find(target_name, input_types, active_only=True)
        if existing is not None:
            return existing
        return self.evolve(
            parent_id,
            target_name,
            input_types,
            output_type,
            cases,
            source_capability_id=source_capability_id,
        )
