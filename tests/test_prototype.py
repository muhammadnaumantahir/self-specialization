from sps_specialization.capability import Capability
from sps_specialization.registry import CapabilityRegistry
from sps_specialization.replication import ReplicationEngine
from sps_specialization.specialization import SpecializationEngine
from sps_specialization.verifier import Verifier
from sps_specialization.evolution import EvolutionEngine

INTEGER_SOURCE = '''def execute(a: int, b: int) -> int:\n    return a * b\n'''
FLOAT_SOURCE = '''def execute(a: float, b: float) -> float:\n    return a * b\n'''

class FakeOllama:
    def __init__(self, source):
        self.source = source
        self.prompts = []
    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.source

def test_capability_executes_and_replication_preserves_parent():
    parent = Capability.create("IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE)
    assert parent.execute(6, 7) == 42
    child = ReplicationEngine().replicate(parent)
    assert child.id != parent.id
    assert child.parent_id == parent.id
    assert child.state == "S0-C"
    assert child.execute(3, 4) == 12

def test_specialization_generates_float_child_without_activation():
    parent = Capability.create("IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE)
    child = ReplicationEngine().replicate(parent)
    ollama = FakeOllama(FLOAT_SOURCE)
    specialized = SpecializationEngine(ollama).specialize(child, "FloatMultiplication", ["float", "float"], "float")
    assert "specialization" in ollama.prompts[0].lower()
    assert specialized.name == "FloatMultiplication"
    assert specialized.parent_id == child.id
    assert specialized.state == "GENERATED"
    assert specialized.source_code == FLOAT_SOURCE

def test_specialization_normalizes_markdown_wrapped_source():
    parent = Capability.create("IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE)
    child = ReplicationEngine().replicate(parent)
    wrapped = "Here is the specialized capability:\n\n```python\ndef execute(a: float, b: float) -> float:\n    return a * b\n```\n"
    specialized = SpecializationEngine(FakeOllama(wrapped)).specialize(child, "FloatMultiplication", ["float", "float"], "float")
    assert specialized.source_code == FLOAT_SOURCE


def test_verifier_accepts_float_and_rejects_unsafe():
    verifier = Verifier()
    assert verifier.verify(FLOAT_SOURCE, [(2.5, 4.0, 10.0), (-2.5, 4.0, -10.0)])
    unsafe = "import os\ndef execute(a, b):\n    return os.system('echo bad')\n"
    assert not verifier.verify(unsafe, [(1.0, 2.0, 2.0)])

def test_evolution_activates_verified_specialization_and_records_lineage():
    registry = CapabilityRegistry()
    parent = Capability.create("IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE)
    registry.register(parent)
    result = EvolutionEngine(registry, FakeOllama(FLOAT_SOURCE), Verifier()).evolve(parent.id, "FloatMultiplication", ["float", "float"], "float", [(2.5, 4.0, 10.0)])
    assert result.state == "S1"
    assert result.execute(2.5, 4.0) == 10.0
    assert registry.active(result.id) is result
    assert [c.name for c in registry.lineage(result.id)] == ["IntegerMultiplication", "IntegerMultiplication-child", "FloatMultiplication"]
    assert [e.event for e in result.events][-1] == "ACTIVATE"

def test_failed_generation_never_activates():
    registry = CapabilityRegistry()
    parent = Capability.create("IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE)
    registry.register(parent)
    bad = "def execute(a, b):\n    return a + b\n"
    result = EvolutionEngine(registry, FakeOllama(bad), Verifier()).evolve(parent.id, "BadFloatMultiplication", ["float", "float"], "float", [(2.5, 4.0, 10.0)])
    assert result.state == "FAILED"
    assert registry.active(result.id) is None
    assert any(e.event == "VERIFY_FAIL" for e in result.events)
