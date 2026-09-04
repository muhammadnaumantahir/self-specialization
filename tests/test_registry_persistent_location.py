from pathlib import Path

from sps_specialization.capability import Capability
from sps_specialization.registry import CapabilityRegistry


def test_default_storage_dir_is_project_data_location(monkeypatch):
    monkeypatch.delenv("SPS_CAPABILITY_REGISTRY_DIR", raising=False)
    expected = Path(__file__).resolve().parents[1] / "data" / "capability-registry"
    assert CapabilityRegistry.default_storage_dir() == expected


def test_persistent_registry_uses_default_storage_and_survives_reload(tmp_path, monkeypatch):
    storage = tmp_path / "capability-registry"
    monkeypatch.setenv("SPS_CAPABILITY_REGISTRY_DIR", str(storage))

    registry = CapabilityRegistry.persistent()
    source = "def execute(a: int, b: int) -> int:\n    return a * b\n"
    capability = Capability.create(
        "IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", source
    )
    registry.register(capability)

    assert registry.storage_dir == storage
    assert (storage / "registry.json").exists()
    assert list((storage / "sources").glob("*.py"))

    reloaded = CapabilityRegistry.persistent()
    loaded = reloaded.get("IntegerMultiplication")
    assert loaded.id == capability.id
    assert loaded.state == "S0"
    assert loaded.execute(6, 7) == 42


def test_explicit_storage_override_still_works(tmp_path):
    storage = tmp_path / "custom"
    registry = CapabilityRegistry.persistent(storage)
    assert registry.storage_dir == storage
