from .capability import Capability
from .replication import ReplicationEngine
from .specialization import SpecializationEngine


SERIALIZE_SOURCE = '''def execute(a, b):\n    raise NotImplementedError("SerializeCapability is a general capability")\n'''


class EvolutionEngine:
    def __init__(self, registry, ollama, verifier):
        self.registry = registry
        self.ollama = ollama
        self.verifier = verifier

    def _create_general_parent(self, source):
        """Generalize an existing capability only when a specialization family is needed."""
        existing = self.registry.find("SerializeCapability", active_only=False)
        if existing is not None:
            return existing

        general = Capability.create(
            "SerializeCapability",
            "1.0",
            "S0",
            ["Any", "Any"],
            "Any",
            SERIALIZE_SOURCE,
        )
        general.record("SERIALIZE", f"source={source.id}:{source.name}")
        self.registry.register(general)
        self.registry.reparent(source.id, general.id)
        return general

    def evolve(self, parent_id, target_name, input_types, output_type, cases, source_capability_id=None):
        """Replicate a source capability and publish its specialization under a general parent."""
        if parent_id is None:
            if source_capability_id is None:
                raise LookupError("A source capability is required to create a general parent")
            source = self.registry.get(source_capability_id)
            general_parent = self._create_general_parent(source)
        else:
            general_parent = self.registry.get(parent_id)
            source = self.registry.get(source_capability_id) if source_capability_id else general_parent

        if source.parent_id != general_parent.id:
            self.registry.reparent(source.id, general_parent.id)

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
