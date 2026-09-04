import os
import sys

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


def print_lineage(registry, capability_id):
    print("\nCAPABILITY LINEAGE")
    print("  S0  IntegerMultiplication")
    lineage = registry.lineage(capability_id)
    for cap in lineage[1:]:
        state = cap.state
        print(f"   ↓")
        print(f"  {state:<3} {cap.name}  (parent={cap.parent_id})")


def print_events(capability):
    print("\nEVOLUTION EVENTS")
    for index, event in enumerate(capability.events, 1):
        print(f"  {index}. {event.event:<10} {event.detail}")


def print_created_capability(capability):
    print("\nNEW CAPABILITY CREATED AT RUNTIME")
    print("  Name:          ", capability.name)
    print("  State:         ", capability.state)
    print("  Input contract:", capability.input_types)
    print("  Output type:   ", capability.output_type)
    print("  Parent ID:     ", capability.parent_id)
    print("\nGENERATED CAPABILITY SOURCE CODE")
    print("  " + "-" * 58)
    for line in capability.source_code.strip().splitlines():
        print("  " + line)
    print("  " + "-" * 58)


def main():
    registry = CapabilityRegistry()
    parent = Capability.create(
        "IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE
    )
    registry.register(parent)

    print("=" * 72)
    print("SPS SELF-SPECIALIZATION — MINIMAL RESEARCH PROTOTYPE")
    print("=" * 72)
    print("Research flow:")
    print("  S0 static capability → replicate → specialize → verify → S1 → reuse")

    print("\n" + "=" * 72)
    print("PHASE 1 — STATE 0: ORIGINAL STATIC CAPABILITY")
    print("=" * 72)
    print("Capability :", parent.name)
    print("Contract   :", parent.input_types, "->", parent.output_type)
    print("Test       : 6 × 7 =", parent.execute(6, 7))
    print("Status     : READY")

    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    dispatcher = CapabilityDispatcher(registry, engine)

    print("\n" + "=" * 72)
    print("PHASE 2 — REQUEST THAT STATE 0 ALREADY SUPPORTS")
    print("=" * 72)
    print("User request: multiply(8, 9)")
    value, cap = dispatcher.execute("multiply", 8, 9)
    print("Resolved    :", cap.name, "[", cap.state, "]")
    print("Result      :", value)
    print("Decision    : Use existing capability; AI is not required.")

    print("\n" + "=" * 72)
    print("PHASE 3 — NEW REQUEST: FLOAT MULTIPLICATION")
    print("=" * 72)
    print("User request: multiply(2.5, 4.0)")
    print("Required    : [float, float] -> float")
    print("Current     : No active capability supports this contract.")
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
    print("PHASE 4 — SELF-SPECIALIZATION RESULT")
    print("=" * 72)
    print("Created     :", specialized.name)
    print("State       :", specialized.state)
    print("Contract    :", specialized.input_types, "->", specialized.output_type)
    print("Test result : 2.5 × 4.0 =", value)

    print_created_capability(specialized)
    print_lineage(registry, specialized.id)
    print_events(specialized)

    if specialized.state != "S1":
        print("\nSTATUS: FAILED — the generated capability was not activated.")
        return 1

    print("\n" + "=" * 72)
    print("PHASE 5 — REUSE THE NEW STATE 1 CAPABILITY")
    print("=" * 72)
    print("User request: multiply(3.0, 5.0)")
    value2, reused = dispatcher.execute(
        "multiply", 3.0, 5.0,
        ("FloatMultiplication", "float", cases),
    )
    print("Resolved    :", reused.name, "[", reused.state, "]")
    print("Result      :", value2)
    print("Decision    : Reuse existing S1; Ollama is not called again.")

    print("\n" + "=" * 72)
    print("RESEARCH RESULT")
    print("=" * 72)
    print("✓ State 0 capability existed before the float request")
    print("✓ State 0 reproduced itself as a child capability")
    print("✓ Ollama generated a specialized float capability")
    print("✓ Generated code passed verification")
    print("✓ FloatMultiplication was activated as State S1")
    print("✓ S1 was integrated into the registry")
    print("✓ A later float request reused S1 without AI generation")
    print("\nSUCCESS: State 0 reproduced, specialized into State 1, integrated, and reused.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
