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


def print_events(capability):
    print("\n[EVENTS]")
    for event in capability.events:
        print(f"  {event.event}: {event.detail}")


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

    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    dispatcher = CapabilityDispatcher(registry, engine)

    print("\n" + "=" * 72)
    print("USER INPUT — INTEGER")
    print("=" * 72)
    print("Request: multiply(8, 9)")
    value, cap = dispatcher.execute("multiply", 8, 9)
    print("Resolved capability:", cap.name)
    print("State:", cap.state)
    print("Result:", value)
    print("Ollama is not needed because State 0 already supports int × int.")

    print("\n" + "=" * 72)
    print("USER INPUT — FLOAT (MISSING CAPABILITY)")
    print("=" * 72)
    print("Request: multiply(2.5, 4.0)")
    print("No float capability exists, so the framework will:")
    print("  1. detect the unsupported [float, float] contract")
    print("  2. replicate IntegerMultiplication")
    print("  3. ask Ollama to specialize the child")
    print("  4. verify the generated code")
    print("  5. integrate and activate FloatMultiplication as State S1")

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

    print("\nResult capability:", specialized.name)
    print("Result state:", specialized.state)
    print("2.5 * 4.0 =", value)
    print_lineage(registry, specialized.id)
    print_events(specialized)

    if specialized.state != "S1":
        print("\nSPECIALIZATION FAILED")
        print("Generated/failed capability source:")
        print(specialized.source_code)
        return 1

    print("\n" + "=" * 72)
    print("USER INPUT — FLOAT AGAIN (INTEGRATED S1)")
    print("=" * 72)
    print("Request: multiply(3.0, 5.0)")
    value2, reused = dispatcher.execute(
        "multiply", 3.0, 5.0,
        ("FloatMultiplication", "float", cases),
    )
    print("Resolved capability:", reused.name)
    print("State:", reused.state)
    print("Result:", value2)
    print("The integrated S1 capability is reused; Ollama is not called again.")

    print("\nSUCCESS: State 0 reproduced, specialized into State 1, integrated, and reused.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
