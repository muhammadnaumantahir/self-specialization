"""Run the deterministic self-specialization prototype against application storage.

The demo contains no AI model or network dependency. Stage 1 specialization is
controlled by the explicit type-specialization rules module.
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

    engine = EvolutionEngine(registry, Verifier())
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
    for item in registry.all():
        print(
            f"  {item.name} [{item.state}] "
            f"parent={item.parent_id}"
        )

    reloaded = CapabilityRegistry.persistent()
    persisted = reloaded.get("FloatMultiplication")
    print(
        f"Reload verification: {persisted.name} [{persisted.state}] "
        f"-> {persisted.execute(3.0, 5.0)}"
    )
    print("No AI/model invocation is required for specialization or reuse.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
