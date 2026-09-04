from pathlib import Path

from sps_specialization.capability import Capability
from sps_specialization.handler import CapabilityHandler
from sps_specialization.registry import CapabilityRegistry
from sps_specialization.replication import ReplicationEngine
from sps_specialization.specialization import SpecializationEngine
from sps_specialization.verifier import Verifier
from sps_specialization.evolution import EvolutionEngine
from sps_specialization.dispatcher import CapabilityDispatcher

INTEGER_SOURCE = '''def execute(a: int, b: int) -> int:\n    return a * b\n'''
FLOAT_SOURCE = '''def execute(a: float, b: float) -> float:\n    return a * b\n'''
SERIALIZE_SOURCE = '''def execute(a, b):\n    raise NotImplementedError("SerializeCapability is a general capability")\n'''


class FakeOllama:
    def __init__(self, source):
        self.source = source
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        return self.source


class FailingOllama:
    def generate(self, prompt):
        raise ConnectionError("Ollama server unavailable")


def make_parent(registry=None):
    parent = Capability.create("IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE)
    if registry:
        registry.register(parent)
    return parent


def make_hierarchy(registry):
    general = Capability.create(
        "SerializeCapability", "1.0", "S0", ["Any", "Any"], "Any", SERIALIZE_SOURCE
    )
    integer = Capability.create(
        "IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE,
        parent_id=general.id,
    )
    registry.register(general)
    registry.register(integer)
    return general, integer


def test_state_0_integer_multiplication():
    parent = make_parent()
    assert parent.state == "S0"
    assert parent.execute(6, 7) == 42
    assert parent.execute(-3, 4) == -12


def test_replication_creates_independent_child():
    parent = make_parent()
    child = ReplicationEngine().replicate(parent)
    assert child.id != parent.id
    assert child.parent_id == parent.id
    assert child.state == "S0-C"
    assert child.execute(3, 4) == 12


def test_specialization_generates_float_child():
    parent = make_parent()
    child = ReplicationEngine().replicate(parent)
    specialized = SpecializationEngine(FakeOllama(FLOAT_SOURCE)).specialize(
        child, "FloatMultiplication", ["float", "float"], "float"
    )
    assert specialized.name == "FloatMultiplication"
    assert specialized.parent_id == child.id
    assert specialized.state == "GENERATED"
    assert specialized.source_code == FLOAT_SOURCE


def test_specialization_normalizes_markdown_source():
    parent = make_parent()
    child = ReplicationEngine().replicate(parent)
    wrapped = "Here is the specialized capability:\n```python\ndef execute(a: float, b: float) -> float:\n    return a * b\n```"
    specialized = SpecializationEngine(FakeOllama(wrapped)).specialize(
        child, "FloatMultiplication", ["float", "float"], "float"
    )
    assert specialized.source_code == FLOAT_SOURCE


def test_verifier_accepts_float_and_rejects_unsafe():
    verifier = Verifier()
    assert verifier.verify(FLOAT_SOURCE, [(2.5, 4.0, 10.0), (-2.5, 4.0, -10.0)])
    unsafe = "import os\ndef execute(a, b):\n    return os.system('echo bad')\n"
    assert not verifier.verify(unsafe, [(1.0, 2.0, 2.0)])


def test_verifier_reports_wrong_result():
    verifier = Verifier()
    ok, reason = verifier.verify_detailed(
        "def execute(a, b):\n    return a + b\n",
        [(2.5, 4.0, 10.0)],
    )
    assert not ok
    assert "WRONG_RESULT" in reason
    assert verifier.last_error == reason


def test_verifier_reports_syntax_error():
    verifier = Verifier()
    malformed = "def execute(a, b)\n    return a * b\n"
    ok, reason = verifier.verify_detailed(malformed, [(1.0, 2.0, 2.0)])
    assert not ok
    assert "syntax error" in reason.lower()
    assert verifier.last_error == reason


def test_evolution_activates_only_after_verification():
    registry = CapabilityRegistry()
    general, integer = make_hierarchy(registry)
    result = EvolutionEngine(registry, FakeOllama(FLOAT_SOURCE), Verifier()).evolve(
        general.id, "FloatMultiplication", ["float", "float"], "float",
        [(2.5, 4.0, 10.0)], source_capability_id=integer.id
    )
    assert result.state == "S1"
    assert result.execute(2.5, 4.0) == 10.0
    assert registry.active(result.id) is result
    assert [c.name for c in registry.lineage(result.id)] == [
        "SerializeCapability", "FloatMultiplication"
    ]
    assert [c.name for c in registry.children(general.id)] == [
        "IntegerMultiplication", "FloatMultiplication"
    ]
    assert integer.state == "S0"
    assert not any(c.name.endswith("-copy") for c in registry.all())
    assert any(e.event == "VERIFY_PASS" and e.detail == "PASS" for e in result.events)


def test_failed_generation_never_activates_and_records_reason():
    registry = CapabilityRegistry()
    general, integer = make_hierarchy(registry)
    bad = "def execute(a, b):\n    return a + b\n"
    result = EvolutionEngine(registry, FakeOllama(bad), Verifier()).evolve(
        general.id, "BadFloatMultiplication", ["float", "float"], "float",
        [(2.5, 4.0, 10.0)], source_capability_id=integer.id
    )
    assert result.state == "FAILED"
    assert registry.active(result.id) is None
    failures = [e.detail for e in result.events if e.event == "VERIFY_FAIL"]
    assert failures and "WRONG_RESULT" in failures[-1]


def test_ollama_failure_is_preserved_and_dispatcher_surfaces_reason():
    registry = CapabilityRegistry()
    make_hierarchy(registry)
    dispatcher = CapabilityDispatcher(
        registry,
        EvolutionEngine(registry, FailingOllama(), Verifier()),
    )
    try:
        dispatcher.execute(
            "multiply", 2.5, 4.0,
            ("FloatMultiplication", "float", [(2.5, 4.0, 10.0)]),
        )
        assert False, "dispatcher should raise for failed specialization"
    except RuntimeError as exc:
        message = str(exc)
        assert "state=FAILED" in message
        assert "ConnectionError" in message
        assert "Ollama server unavailable" in message


def test_multiply_request_uses_integer_state_without_ai_then_specializes_float():
    registry = CapabilityRegistry()
    general, integer = make_hierarchy(registry)
    fake = FakeOllama(FLOAT_SOURCE)
    evolution = EvolutionEngine(registry, fake, Verifier())
    dispatcher = CapabilityDispatcher(registry, evolution)

    value, capability = dispatcher.execute("multiply", 6, 7)
    assert value == 42
    assert capability.id == integer.id
    assert capability.state == "S0"
    assert fake.prompts == []

    cases = [(2.5, 4.0, 10.0), (0.5, 0.2, 0.1), (-2.5, 4.0, -10.0)]
    value, capability = dispatcher.execute(
        "multiply", 2.5, 4.0, ("FloatMultiplication", "float", cases)
    )
    assert value == 10.0
    assert capability.name == "FloatMultiplication"
    assert capability.state == "S1"
    assert capability.parent_id == general.id
    assert integer.state == "S0"
    assert len(fake.prompts) == 1

    value2, capability2 = dispatcher.execute(
        "multiply", 3.0, 5.0, ("FloatMultiplication", "float", cases)
    )
    assert value2 == 15.0
    assert capability2.id == capability.id
    assert len(fake.prompts) == 1


def test_missing_float_request_dynamically_creates_serialize_parent_and_reparents_existing_integer():
    registry = CapabilityRegistry()
    integer = make_parent(registry)
    fake = FakeOllama(FLOAT_SOURCE)
    dispatcher = CapabilityDispatcher(
        registry,
        EvolutionEngine(registry, fake, Verifier()),
    )

    assert [cap.name for cap in registry.all()] == ["IntegerMultiplication"]
    assert integer.parent_id is None
    assert integer.state == "S0"

    value, floating = dispatcher.execute(
        "multiply", 2.5, 4.0,
        ("FloatMultiplication", "float", [(2.5, 4.0, 10.0)]),
    )

    assert value == 10.0
    assert floating.state == "S1"
    assert floating.parent_id is not None
    general = registry.get(floating.parent_id)
    assert general.name == "SerializeCapability"
    assert general.state == "S0"
    assert integer.parent_id == general.id
    assert integer.state == "S0"
    assert registry.get(integer.id) is integer
    assert [cap.name for cap in registry.children(general.id)] == [
        "IntegerMultiplication", "FloatMultiplication"
    ]
    assert [cap.name for cap in registry.lineage(floating.id)] == [
        "SerializeCapability", "FloatMultiplication"
    ]
    assert not any(cap.name.endswith("-copy") for cap in registry.all())
    assert any(event.event == "SERIALIZE" for event in general.events)
    assert any(event.event == "REPARENT" for event in integer.events)


def test_registry_persists_capability_metadata_and_python_source(tmp_path):
    registry = CapabilityRegistry(storage_dir=tmp_path / "capabilities")
    parent = make_parent(registry)
    parent.state = "S1"
    parent.activated_at = parent.created_at
    registry.register(parent)

    registry_path = tmp_path / "capabilities" / "registry.json"
    record_path = tmp_path / "capabilities" / "records" / f"{parent.id}.json"
    source_dir = tmp_path / "capabilities" / "sources"

    assert registry_path.exists()
    assert record_path.exists()
    source_files = list(source_dir.glob(f"{parent.id}_*.py"))
    assert len(source_files) == 1
    assert source_files[0].read_text() == INTEGER_SOURCE


def test_registry_list_active_get_and_inspect(tmp_path):
    registry = CapabilityRegistry(storage_dir=tmp_path / "capabilities")
    parent = make_parent(registry)
    parent.state = "S1"
    parent.activated_at = parent.created_at
    registry.register(parent)
    failed = Capability.create("FailedCapability", "1.0", "FAILED", ["float", "float"], "float", FLOAT_SOURCE)
    registry.register(failed)

    assert registry.list_active() == [parent]
    assert registry.get(parent.id) is parent
    assert registry.get("IntegerMultiplication") is parent

    inspected = registry.inspect("IntegerMultiplication")
    assert inspected["id"] == parent.id
    assert inspected["name"] == "IntegerMultiplication"
    assert inspected["state"] == "S1"
    assert inspected["parent_id"] is None
    assert inspected["storage"]["record"] == str(tmp_path / "capabilities" / "records" / f"{parent.id}.json")
    assert inspected["storage"]["source"].endswith(f"{parent.id}_IntegerMultiplication.py")
    assert inspected["source_code"] == INTEGER_SOURCE


def test_registry_load_reconstructs_persisted_capability_for_reuse(tmp_path):
    storage_dir = tmp_path / "capabilities"
    registry = CapabilityRegistry(storage_dir=storage_dir)
    parent = make_parent(registry)
    parent.state = "S1"
    parent.activated_at = parent.created_at
    registry.register(parent)

    reloaded = CapabilityRegistry(storage_dir=storage_dir)
    loaded = reloaded.get(parent.id)

    assert loaded.id == parent.id
    assert loaded.name == parent.name
    assert loaded.state == "S1"
    assert loaded.source_code == INTEGER_SOURCE
    assert loaded.execute(8, 9) == 72
    assert reloaded.list_active()[0].id == parent.id


def test_evolution_persists_generated_state_1_artifact(tmp_path):
    storage_dir = tmp_path / "capabilities"
    registry = CapabilityRegistry(storage_dir=storage_dir)
    general, integer = make_hierarchy(registry)
    result = EvolutionEngine(registry, FakeOllama(FLOAT_SOURCE), Verifier()).evolve(
        general.id, "FloatMultiplication", ["float", "float"], "float",
        [(2.5, 4.0, 10.0)], source_capability_id=integer.id
    )

    inspected = registry.inspect(result.id)
    assert result.state == "S1"
    assert result.parent_id == general.id
    assert Path(inspected["storage"]["record"]).exists()
    assert Path(inspected["storage"]["source"]).read_text() == FLOAT_SOURCE
    assert registry.get("FloatMultiplication").execute(2.5, 4.0) == 10.0


def test_capability_handler_owns_execution_and_resources():
    capability = Capability.create(
        "IntegerMultiplication", "1.0", "S1", ["int", "int"], "int", INTEGER_SOURCE
    )
    assert isinstance(capability.handler, CapabilityHandler)
    assert capability.handler.capability_id == capability.id
    assert capability.handler.status == "ready"
    assert "source_code" in capability.handler.resources
    assert capability.handler.execute(6, 7) == 42
    assert capability.inspect_handler()["capability_id"] == capability.id


def test_general_serialize_capability_is_root_of_specialized_children():
    registry = CapabilityRegistry()
    general, integer = make_hierarchy(registry)
    floating = Capability.create(
        "FloatMultiplication", "1.0", "S1", ["float", "float"], "float", FLOAT_SOURCE,
        parent_id=general.id,
    )
    registry.register(floating)

    assert general.state == "S0"
    assert integer.state == "S0"
    assert integer.parent_id == general.id
    assert floating.parent_id == general.id
    assert [cap.name for cap in registry.children(general.id)] == [
        "IntegerMultiplication", "FloatMultiplication"
    ]
    assert [cap.name for cap in registry.lineage(floating.id)] == [
        "SerializeCapability", "FloatMultiplication"
    ]
    assert [cap.name for cap in registry.lineage(integer.id)] == [
        "SerializeCapability", "IntegerMultiplication"
    ]


def test_specialized_capabilities_are_siblings_not_nested_replication_children():
    registry = CapabilityRegistry()
    general, integer = make_hierarchy(registry)
    result = EvolutionEngine(registry, FakeOllama(FLOAT_SOURCE), Verifier()).evolve(
        general.id, "FloatMultiplication", ["float", "float"], "float",
        [(2.5, 4.0, 10.0)], source_capability_id=integer.id
    )

    assert result.state == "S1"
    assert result.parent_id == general.id
    assert integer.state == "S0"
    assert [cap.name for cap in registry.children(general.id)] == [
        "IntegerMultiplication", "FloatMultiplication"
    ]
    assert not any(cap.name == "IntegerMultiplication-child" for cap in registry.all())
    assert not any(cap.name == "IntegerMultiplication-copy" for cap in registry.all())
    assert [cap.name for cap in registry.lineage(result.id)] == [
        "SerializeCapability", "FloatMultiplication"
    ]
