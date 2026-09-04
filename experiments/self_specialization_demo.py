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
    print("[LINEAGE]")
    for cap in registry.lineage(capability_id):
        print(f"  {cap.name} [{cap.state}] id={cap.id} parent={cap.parent_id}")


def main():
    registry = CapabilityRegistry()
    parent = Capability.create(
        "IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE
    )
    registry.register(parent)

    print("=" * 72)
    print("STATE 0 — STATIC INTEGER MULTIPLICATION")
    print("=" * 72)
    print("Capability:", parent.name)
    print("Contract:", parent.input_types, "->", parent.output_type)
    print("6 * 7 =", parent.execute(6, 7))

    print("\n" + "=" * 72)
    print("RUNTIME REQUEST — INTEGER")
    print("=" * 72)
    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    dispatcher = CapabilityDispatcher(registry, engine)
    value, cap = dispatcher.execute("IntegerMultiplication", 8, 9)
    print("Resolved capability:", cap.name)
    print("8 * 9 =", value)
    print("Ollama is not needed because State 0 already supports int × int.")

    print("\n" + "=" * 72)
    print("RUNTIME REQUEST — FLOAT (MISSING CAPABILITY)")
    print("=" * 72)
    print("The request is multiply(2.5, 4.0).")
    print("No float capability exists, so the framework will:")
    print("  1. replicate IntegerMultiplication")
    print("  2. ask Ollama to specialize the child")
    print("  3. validate the generated code")
    print("  4. activate FloatMultiplication as State S1")

    cases = [(2.5, 4.0, 10.0), (0.5, 0.2, 0.1), (-2.5, 4.0, -10.0), (3.14, 2.0, 6.28)]
    value, specialized = dispatcher.execute(
        "IntegerMultiplication", 2.5, 4.0,
        ("FloatMultiplication", "float", cases),
    )

    print("\nResult capability:", specialized.name)
    print("Result state:", specialized.state)
    print("2.5 * 4.0 =", value)
    print_lineage(registry, specialized.id)

    print("\n[EVENTS]")
    for event in specialized.events:
        print(f"  {event.event}: {event.detail}")

    if specialized.state != "S1":
        print("\nSPECIALIZATION FAILED — check the Ollama service/model configuration.")
        return 1

    print("\nSUCCESS: State 0 reproduced and specialized into State 1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
