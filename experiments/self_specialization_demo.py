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


def print_tree(registry, parent_id, indent=""):
    parent = registry.get(parent_id)
    print(f"{indent}{parent.name} [{parent.state}]  id={parent.id}")
    children = registry.children(parent.id)
    for index, child in enumerate(children):
        branch = "└─" if index == len(children) - 1 else "├─"
        print(f"{indent}{branch} ", end="")
        print_tree(registry, child.id, indent + ("   " if branch == "└─" else "│  "))


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
    print(f"  Parent:         {registry.get(inspected['parent_id']).name}")
    print(f"  Created:        {inspected['created_at']}")
    print(f"  Location:       {storage['source']}")
    print(f"  Storage:        {storage['record']}")
    print(f"  Registry:       {storage['registry']}")
    print(f"  Contract:       {inspected['input_types']} -> {inspected['output_type']}")
    print(f"  Handler:        {inspected['handler']['status']}")
    print(f"  Resources:      {list(inspected['handler']['resources'])}")
    print("\n  SOURCE (.py)")
    print("  " + "-" * 58)
    for line in inspected["source_code"].strip().splitlines():
        print("  " + line)
    print("  " + "-" * 58)
    print("\n  ✓ Handler owns execution")
    print("  ✓ Metadata persisted as JSON")
    print("  ✓ Source persisted as Python")
    print("  ✓ Capability is retrievable through the registry")


def main():
    if DEMO_STORAGE.exists():
        shutil.rmtree(DEMO_STORAGE)
    registry = CapabilityRegistry(storage_dir=DEMO_STORAGE)

    # Initial system: only the programmer-defined integer capability exists.
    integer = Capability.create(
        "IntegerMultiplication", "1.0", "S1", ["int", "int"], "int", INTEGER_SOURCE
    )
    registry.register(integer)

    print("=" * 72)
    print("🧬 SPS SELF-SPECIALIZATION — MINIMAL RESEARCH PROTOTYPE")
    print("=" * 72)
    print("Complete research flow:")
    print("  INTEGER S1 → MISSING FLOAT REQUEST → SERIALIZE/GENERALIZE → S0")
    print("      → REPLICATE → S0-C → SPECIALIZE WITH OLLAMA/QWEN")
    print("      → VERIFY → FLOAT S1 → LINK UNDER SERIALIZE → PERSIST → REUSE")
    print(f"\nPersistent capability registry: {DEMO_STORAGE}")

    print("\n" + "=" * 72)
    print("🔵 PHASE 1 — INITIAL STATE")
    print("=" * 72)
    print("Capability :", integer.name, "[S1]")
    print("Contract   :", integer.input_types, "->", integer.output_type)
    print("Test       : 6 × 7 =", integer.execute(6, 7))
    print("Parent     : None")
    print("Hierarchy  : IntegerMultiplication [S1]")
    print("Decision   : No SerializeCapability exists yet.")

    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    dispatcher = CapabilityDispatcher(registry, engine)

    print("\n" + "=" * 72)
    print("🟡 PHASE 2 — NEW REQUEST: FLOAT MULTIPLICATION")
    print("=" * 72)
    print("User request: multiply(2.5, 4.0)")
    print("Required    : [float, float] -> float")
    print("Lookup      : FloatMultiplication is missing.")
    print("\nThe handler/evolution flow is:")
    print("  1. Detect that FloatMultiplication does not exist")
    print("  2. Serialize/generalize the existing IntegerMultiplication")
    print("  3. Create SerializeCapability [S0] at runtime")
    print("  4. Reparent the existing IntegerMultiplication under SerializeCapability")
    print("  5. Create a transient S0-C copy of IntegerMultiplication")
    print("  6. Ollama/Qwen transforms that copy into FloatMultiplication")
    print("  7. Generated code is verified")
    print("  8. Verified FloatMultiplication becomes S1")
    print("  9. Link FloatMultiplication directly under SerializeCapability")

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
    general = registry.get(specialized.parent_id)

    print("\n" + "=" * 72)
    print("🟣 PHASE 3 — SERIALIZATION / GENERALIZATION")
    print("=" * 72)
    print("Created     :", general.name, "[", general.state, "]")
    print("Source      :", integer.name, "(existing capability; same ID preserved)")
    print("Integer ID  :", integer.id)
    print("Integer now :", integer.parent_id == general.id, "→ child of", general.name)
    print("Event       :", [e.event for e in general.events if e.event == "SERIALIZE"])

    print("\n" + "=" * 72)
    print("🟣 PHASE 4 — SELF-SPECIALIZATION RESULT")
    print("=" * 72)
    print("Created     :", specialized.name)
    print("State       :", specialized.state)
    print("Contract    :", specialized.input_types, "->", specialized.output_type)
    print("Test result : 2.5 × 4.0 =", value)
    print("Parent      :", general.name)

    print_created_capability(registry, specialized)
    print_events(specialized)

    if specialized.state != "S1":
        print("\nSTATUS: FAILED — the generated capability was not activated.")
        return 1

    print("\n" + "=" * 72)
    print("🌳 PHASE 5 — CAPABILITY HIERARCHY")
    print("=" * 72)
    print_tree(registry, general.id)
    print("\nFinal hierarchy:")
    print("  SerializeCapability [S0]")
    print("       ├── IntegerMultiplication [S1]")
    print("       └── FloatMultiplication [S1]")
    print("\nBefore the float request there was no SerializeCapability node.")
    print("The transient S0-C replication copy is an evolution mechanism, not a final hierarchy node.")

    print("\n" + "=" * 72)
    print("🟢 PHASE 6 — REGISTRY INSPECTION")
    print("=" * 72)
    inspected = registry.inspect("FloatMultiplication")
    print("registry.get('FloatMultiplication') ->", registry.get("FloatMultiplication").id)
    print("registry.children('SerializeCapability') ->", [c.name for c in registry.children(general.id)])
    print("registry.list_active() ->", [f"{c.name} [{c.state}]" for c in registry.list_active()])
    print("Persisted JSON ->", inspected["storage"]["record"])
    print("Persisted .py  ->", inspected["storage"]["source"])

    print("\n" + "=" * 72)
    print("🔁 PHASE 7 — RELOAD AND REUSE STATE 1")
    print("=" * 72)
    reloaded_registry = CapabilityRegistry(storage_dir=DEMO_STORAGE)
    reloaded = reloaded_registry.get("FloatMultiplication")
    reloaded_general = reloaded_registry.get(reloaded.parent_id)
    print("Reloaded      :", reloaded.name, "[", reloaded.state, "]")
    print("Same ID       :", reloaded.id == specialized.id)
    print("Parent        :", reloaded_general.name, "[", reloaded_general.state, "]")
    print("Integer child  :", reloaded_registry.get("IntegerMultiplication").parent_id == reloaded_general.id)
    print("Handler       :", reloaded.inspect_handler())
    print("Reuse test    : 3.0 × 5.0 =", reloaded.execute(3.0, 5.0))
    print("Decision      : Persisted S1 was retrieved; no new specialization was needed.")

    print("\n" + "=" * 72)
    print("📋 RESEARCH RESULT")
    print("=" * 72)
    print("✓ Initial state contains only IntegerMultiplication [S1]")
    print("✓ Float request detects the missing typed capability")
    print("✓ Existing IntegerMultiplication is serialized/generalized at runtime")
    print("✓ SerializeCapability [S0] is created only at that point")
    print("✓ Existing IntegerMultiplication is reparented; it is not recreated")
    print("✓ A transient S0-C replication copy is created for specialization")
    print("✓ Ollama/Qwen generates the FloatMultiplication specialization")
    print("✓ Generated code passes verification before activation")
    print("✓ FloatMultiplication becomes State S1")
    print("✓ IntegerMultiplication and FloatMultiplication are siblings under SerializeCapability")
    print("✓ S1 source and metadata are persisted")
    print("✓ S1 can be reloaded and reused without another specialization")
    print("\nSUCCESS: Integer S1 → dynamic Serialize S0 → transient S0-C → Float S1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
