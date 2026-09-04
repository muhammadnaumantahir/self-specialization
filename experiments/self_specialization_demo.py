import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from sps_specialization import Capability, CapabilityRegistry, EvolutionEngine, OllamaClient, Verifier

INTEGER_SOURCE = '''def execute(a: int, b: int) -> int:\n    return a * b\n'''

def print_lineage(registry, capability_id):
    for cap in registry.lineage(capability_id):
        print(f"  {cap.name} [{cap.state}] id={cap.id} parent={cap.parent_id}")

def main():
    registry = CapabilityRegistry()
    parent = Capability.create("IntegerMultiplication", "1.0", "S0", ["int", "int"], "int", INTEGER_SOURCE)
    registry.register(parent)
    print("[REGISTER] IntegerMultiplication v1")
    print("[STATE] S0")
    print("[REPLICATE] child created")
    engine = EvolutionEngine(registry, OllamaClient(), Verifier())
    result = engine.evolve(
        parent.id, "FloatMultiplication", ["float", "float"], "float",
        [(2.5,4.0,10.0),(0.5,0.2,0.1),(-2.5,4.0,-10.0),(3.14,2.0,6.28)]
    )
    print(f"[RESULT] {result.name} -> {result.state}")
    print("[LINEAGE]")
    print_lineage(registry, result.id)
    print("[EVENTS]")
    for event in result.events:
        print(f"  {event.event}: {event.detail}")
    if result.state == "S1":
        print("[EXECUTE] FloatMultiplication(2.5, 4.0) =", result.execute(2.5, 4.0))
    return 0 if result.state == "S1" else 1

if __name__ == "__main__":
    raise SystemExit(main())
