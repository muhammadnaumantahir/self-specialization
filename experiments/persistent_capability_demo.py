"""Run the self-specialization prototype against application-owned storage.

Unlike the original throwaway demo, this script does not delete the capability
registry between runs. Generated capabilities therefore survive process restarts.
Set SPS_DEMO_RESET=1 when a clean research run is explicitly required.
"""

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sps_specialization import (
    Capability,
    CapabilityDispatcher,
    CapabilityRegistry,
    EvolutionEngine,
    OllamaClient,
    Verifier,
)

INTEGER_SOURCE = '''def execute(a: int, b: int) -> int:\n    return a * b\n'''


def main():
    storage = CapabilityRegistry.default_storage_dir()
    if os.environ.get("SPS_DEMO_RESET") == "1" and storage.exists():
        shutil.rmtree(storage)

    registry = CapabilityRegistry.persistent()
    integer = registry.find("IntegerMultiplication", ["int", "int"])

    if integer is None:
        integer = Capability.create(
            "IntegerMultiplication", "1.0", "S0",
            ["int", "int"], "int", INTEGER_SOURCE
        )
        registry.register(integer)
        print("Created initial IntegerMultiplication [S0]")
    else:
        print(f"Loaded existing {integer.name} [{integer.state}]")

    print(f"Persistent registry: {registry.storage_dir}")
    print("Capabilities:")
    for capability in registry.all():
        print(f"  - {capability.name} [{capability.state}]")

    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    dispatcher = CapabilityDispatcher(registry, engine)

    value, capability = dispatcher.execute(
        "multiply", 2.5, 4.0,
        (
            "FloatMultiplication",
            "float",
            [(2.5, 4.0, 10.0), (-2.5, 4.0, -10.0)],
        ),
    )

    print(f"Result: {capability.name} [{capability.state}] -> {value}")
    print("Hierarchy:")
    for capability in registry.all():
        print(
            f"  {capability.name} [{capability.state}] "
            f"parent={capability.parent_id}"
        )

    reloaded = CapabilityRegistry.persistent()
    persisted = reloaded.get("FloatMultiplication")
    print(
        f"Reload verification: {persisted.name} [{persisted.state}] "
        f"-> {persisted.execute(3.0, 5.0)}"
    )
    print("No new AI generation is required after reload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
