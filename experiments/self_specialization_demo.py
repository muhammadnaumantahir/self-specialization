"""Minimal executable demonstration of bounded self-specialization.

Stage 1 is deterministic. No AI model is used: IntegerMultiplication can grow
only along type-specialization rules declared in
`specialization/type_specialization_rules.py`.
"""

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from specialization import Capability, CapabilityDispatcher, CapabilityRegistry, EvolutionEngine, Verifier

INTEGER_SOURCE = '''def execute(a: int, b: int) -> int:\n    return a * b\n'''


def main():
    storage = CapabilityRegistry.default_storage_dir()
    if os.environ.get("SPS_DEMO_RESET") == "1" and storage.exists():
        shutil.rmtree(storage)

    registry = CapabilityRegistry.persistent()
    integer = registry.find("IntegerMultiplication", ["int", "int"])

    if integer is None:
        integer = Capability.create(
            "IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE
        )
        registry.register(integer)

    dispatcher = CapabilityDispatcher(registry, EvolutionEngine(registry, Verifier()))

    print("=== INITIAL S0 ===")
    print(f"IntegerMultiplication [{integer.state}]: 6 * 7 = {integer.execute(6, 7)}")

    print("\n=== FLOAT REQUEST ===")
    print("Request: multiply(2.5, 4.0)")
    value, floating = dispatcher.execute(
        "multiply", 2.5, 4.0,
        ("FloatMultiplication", "float", [(2.5, 4.0, 10.0), (-2.5, 4.0, -10.0)]),
    )
    print(f"Result: {floating.name} [{floating.state}] = {value}")

    general = registry.get(floating.parent_id)
    print("\n=== FINAL HIERARCHY ===")
    print(f"{general.name} [{general.state}]")
    print(f"  ├── {integer.name} [{integer.state}]")
    print(f"  └── {floating.name} [{floating.state}]")

    print("\n=== BOUNDARY ===")
    print("Allowed: int multiplication -> float/long/double multiplication")
    print("Rejected: multiplication -> addition")
    print("Rules: specialization/type_specialization_rules.py")

    reloaded = CapabilityRegistry.persistent()
    persisted = reloaded.get("FloatMultiplication")
    print("\n=== RELOAD ===")
    print(f"{persisted.name} [{persisted.state}] -> {persisted.execute(3.0, 5.0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
