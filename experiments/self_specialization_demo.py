import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sps_specialization import (
    Capability,
    CapabilityDispatcher,
    CapabilityRegistry,
    EvolutionEngine,
    OllamaClient,
    Verifier,
)

INTEGER_SOURCE = '''def execute(a: int, b: int) -> int:\n    return a * b\n'''
DEMO_STORAGE = Path("/tmp/sps-capability-registry")


def print_lineage(registry, capability_id):
    print("\n🧬 CAPABILITY LINEAGE")
    lineage = registry.lineage(capability_id)
    for index, cap in enumerate(lineage):
        connector = "└─" if index == len(lineage) - 1 else "├─"
        print(f"  {connector} {cap.name} [{cap.state}]  id={cap.id}")


def print_events(capability):
    print("\n📜 EVOLUTION EVENTS")
    for index, event in enumerate(capability.events, 1):
        print(f"  {index}. {event.event:<12} {event.detail}  ({event.timestamp})")


def print_created_capability(registry, capability):
    inspected = registry.inspect(capability.id)
    storage = inspected["storage"]
    print("\n" + "=" * 72)
    print("🟣 CAPABILITY CREATED AT RUNTIME")
    print("=" * 72)
    print(f"  ID:             {inspected['id']}")
    print(f"  Name:           {inspected['name']}")
    print(f"  State:          {inspected['state']}")
    print(f"  Parent:         {inspected['parent_id']}")
    print(f"  Created:        {inspected['created_at']}")
    print(f"  Location:       {storage['source']}")
    print(f"  Storage:        {storage['record']}")
    print(f"  Registry:       {storage['registry']}")
    print(f"  Contract:       {inspected['input_types']} -> {inspected['output_type']}")
    print("\n  SOURCE (.py)")
    print("  " + "-" * 58)
    for line in inspected["source_code"].strip().splitlines():
        print("  " + line)
    print("  " + "-" * 58)
    print("\n  ✓ Metadata persisted as JSON")
    print("  ✓ Source persisted as Python")
    print("  ✓ Capability is retrievable through the registry")


def main():
    if DEMO_STORAGE.exists():
        shutil.rmtree(DEMO_STORAGE)
    registry = CapabilityRegistry(storage_dir=DEMO_STORAGE)
    parent = Capability.create(
        "IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE
    )
    registry.register(parent)

    print("=" * 72)
    print("🧬 SPS SELF-SPECIALIZATION — MINIMAL RESEARCH PROTOTYPE")
    print("=" * 72)
    print("Research flow:")
    print("  S0 → REPLICATE → S0-C → SPECIALIZE → VERIFY → S1 → REUSE")
    print(f"\nPersistent capability registry: {DEMO_STORAGE}")

    print("\n" + "=" * 72)
    print("🔵 PHASE 1 — STATE 0: ORIGINAL STATIC CAPABILITY")
    print("=" * 72)
    print("Capability :", parent.name, "[S0]")
    print("Contract   :", parent.input_types, "->", parent.output_type)
    print("Test       : 6 × 7 =", parent.execute(6, 7))
    print("Registry   :", registry.inspect(parent.id)["storage"]["record"])
    print("Status     : READY")

    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    dispatcher = CapabilityDispatcher(registry, engine)

    print("\n" + "=" * 72)
    print("🟢 PHASE 2 — REQUEST THAT STATE 0 ALREADY SUPPORTS")
    print("=" * 72)
    print("User request: multiply(8, 9)")
    value, cap = dispatcher.execute("multiply", 8, 9)
    print("Resolved    :", cap.name, "[", cap.state, "]")
    print("Result      :", value)
    print("Decision    : Use existing capability; AI is not required.")

    print("\n" + "=" * 72)
    print("🟡 PHASE 3 — NEW REQUEST: FLOAT MULTIPLICATION")
    print("=" * 72)
    print("User request: multiply(2.5, 4.0)")
    print("Required    : [float, float] -> float")
    print("S0 status   : No active capability supports this contract.")
    print("\nThe system now performs self-specialization:")
    print("  1. Detect missing capability")
    print("  2. Replicate IntegerMultiplication")
    print("  3. Ask Ollama/Qwen to specialize the child")
    print("  4. Verify the generated capability")
    print("  5. Activate it as State S1")

    cases = [
        (2.5, 4.0, 10.0),
        (0.5, 0.2, 0.1),
        (-2.5, 4.0, -10.0),
        (3.14, 2.0, 6.28),
    ]
    value, specialized = dispatcher.execute(
        "multiply", 2.5, 4.0,
        ("FloatMultiplication", "float", cases),
    )

    print("\n" + "=" * 72)
    print("🟣 PHASE 4 — SELF-SPECIALIZATION RESULT")
    print("=" * 72)
    print("Created     :", specialized.name)
    print("State       :", specialized.state)
    print("Contract    :", specialized.input_types, "->", specialized.output_type)
    print("Test result : 2.5 × 4.0 =", value)

    print_created_capability(registry, specialized)
    print_lineage(registry, specialized.id)
    print_events(specialized)

    if specialized.state != "S1":
        print("\nSTATUS: FAILED — the generated capability was not activated.")
        return 1

    print("\n" + "=" * 72)
    print("🟢 PHASE 5 — REGISTRY INSPECTION")
    print("=" * 72)
    inspected = registry.inspect("FloatMultiplication")
    print("registry.get('FloatMultiplication') ->", registry.get("FloatMultiplication").id)
    print("registry.list_active() ->", [f"{c.name} [{c.state}]" for c in registry.list_active()])
    print("Persisted JSON ->", inspected["storage"]["record"])
    print("Persisted .py  ->", inspected["storage"]["source"])

    print("\n" + "=" * 72)
    print("🔁 PHASE 6 — RELOAD AND REUSE STATE 1")
    print("=" * 72)
    reloaded_registry = CapabilityRegistry(storage_dir=DEMO_STORAGE)
    reloaded = reloaded_registry.get("FloatMultiplication")
    print("Reloaded      :", reloaded.name, "[", reloaded.state, "]")
    print("Same ID       :", reloaded.id == specialized.id)
    print("Retrieved from:", reloaded_registry.inspect(reloaded.id)["storage"]["record"])
    print("Reuse test    : 3.0 × 5.0 =", reloaded.execute(3.0, 5.0))
    print("Decision      : Persisted S1 was retrieved; no new specialization was needed.")

    print("\n" + "=" * 72)
    print("📋 RESEARCH RESULT")
    print("=" * 72)
    print("✓ State 0 capability existed before the float request")
    print("✓ State 0 reproduced itself as a child capability")
    print("✓ Ollama generated a specialized float capability")
    print("✓ Generated code passed verification")
    print("✓ FloatMultiplication was activated as State S1")
    print("✓ S1 was integrated into the persistent capability registry")
    print("✓ S1 source exists as a .py artifact and metadata exists as JSON")
    print("✓ S1 can be inspected by name or ID")
    print("✓ S1 can be reloaded from storage and reused")
    print("\nSUCCESS: State 0 reproduced, specialized into State 1, persisted, reloaded, and reused.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
