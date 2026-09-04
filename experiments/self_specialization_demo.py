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
SERIALIZE_SOURCE = '''def execute(a, b):\n    raise NotImplementedError("SerializeCapability is a general capability")\n'''
DEMO_STORAGE = Path("/tmp/sps-capability-registry")


def print_tree(registry, parent_id, indent=""):
    parent = registry.get(parent_id)
    print(f"{indent}{parent.name} [{parent.state}]  id={parent.id}")
    for index, child in enumerate(registry.children(parent.id)):
        branch = "└─" if index == len(registry.children(parent.id)) - 1 else "├─"
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

    general = Capability.create(
        "SerializeCapability", "1.0", "S0", ["Any", "Any"], "Any", SERIALIZE_SOURCE
    )
    integer = Capability.create(
        "IntegerMultiplication", "1.0", "S1", ["int", "int"], "int", INTEGER_SOURCE,
        parent_id=general.id,
    )
    registry.register(general)
    registry.register(integer)

    print("=" * 72)
    print("🧬 SPS SELF-SPECIALIZATION — MINIMAL RESEARCH PROTOTYPE")
    print("=" * 72)
    print("Complete research flow:")
    print("  S0 GENERAL → DETECT MISSING TYPE → REPLICATE → S0-C")
    print("      → SPECIALIZE WITH OLLAMA/QWEN → VERIFY → S1 CHILD → PERSIST → REUSE")
    print(f"\nPersistent capability registry: {DEMO_STORAGE}")

    print("\n" + "=" * 72)
    print("🔵 PHASE 1 — GENERAL STATE 0")
    print("=" * 72)
    print("Capability :", general.name, "[S0]")
    print("Role       : General/root capability for the specialization family")
    print("Handler    :", general.inspect_handler())
    print("Children   :", [f"{c.name} [{c.state}]" for c in registry.children(general.id)])

    print("\n" + "=" * 72)
    print("🟢 PHASE 2 — EXISTING SPECIALIZED CHILD")
    print("=" * 72)
    print("Capability :", integer.name, "[S1]")
    print("Contract   :", integer.input_types, "->", integer.output_type)
    print("Test       : 6 × 7 =", integer.execute(6, 7))
    print("Parent     :", general.name)
    print("Decision   : Existing specialized capability handles integer input; AI is not required.")

    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    dispatcher = CapabilityDispatcher(registry, engine)

    print("\n" + "=" * 72)
    print("🟡 PHASE 3 — NEW REQUEST: FLOAT MULTIPLICATION")
    print("=" * 72)
    print("User request: multiply(2.5, 4.0)")
    print("Required    : [float, float] -> float")
    print("Lookup      : No active child supports this type contract.")
    print("\nThe handler/evolution flow is:")
    print("  1. General SerializeCapability receives the missing-capability request")
    print("  2. IntegerMultiplication is selected as the source capability")
    print("  3. A transient S0-C runtime copy is created")
    print("  4. Ollama/Qwen transforms that copy into FloatMultiplication")
    print("  5. Generated code is verified")
    print("  6. Verified capability becomes S1 and is linked directly to SerializeCapability")

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
    print("Parent      :", registry.get(specialized.parent_id).name)

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
    print("\nThe transient S0-C replication copy is an evolution mechanism, not a final hierarchy node.")

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
    print("Reloaded      :", reloaded.name, "[", reloaded.state, "]")
    print("Same ID       :", reloaded.id == specialized.id)
    print("Parent        :", reloaded_registry.get(reloaded.parent_id).name)
    print("Handler       :", reloaded.inspect_handler())
    print("Reuse test    : 3.0 × 5.0 =", reloaded.execute(3.0, 5.0))
    print("Decision      : Persisted S1 was retrieved; no new specialization was needed.")

    print("\n" + "=" * 72)
    print("📋 RESEARCH RESULT")
    print("=" * 72)
    print("✓ SerializeCapability exists as the general State S0 parent")
    print("✓ IntegerMultiplication is a statically defined specialized child")
    print("✓ A missing float contract triggers transient S0-C replication")
    print("✓ Ollama/Qwen generates the FloatMultiplication specialization")
    print("✓ Generated code passes verification before activation")
    print("✓ FloatMultiplication becomes State S1")
    print("✓ FloatMultiplication is linked directly under SerializeCapability")
    print("✓ CapabilityHandler owns runtime execution and lightweight resources")
    print("✓ S1 source and metadata are persisted")
    print("✓ S1 can be reloaded and reused without another specialization")
    print("\nSUCCESS: General S0 parent → replicated S0-C transformation → specialized S1 child → persisted and reused.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
