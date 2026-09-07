# SPS Self-Specialization Prototype

A small research prototype for **bounded capability growth**.

Stage 1 demonstrates:

```text
IntegerMultiplication [S0]
        |
        v
replicate -> S0-C
        |
        v
Type Specialization Rules
        |
        v
FloatMultiplication [GENERATED]
        |
        v
verify -> S1
```

## Core rule

Stage 1 is **deterministic**. No AI, Ollama, Qwen, API key or model server is required.

The allowed transformations are defined in one separate policy file:

```text
sps_specialization/type_specialization_rules.py
```

The transformer can only apply an explicitly declared rule and the operation must remain unchanged.

```text
IntegerMultiplication -> FloatMultiplication   ✓
IntegerMultiplication -> LongMultiplication    ✓
IntegerMultiplication -> DoubleMultiplication  ✓
IntegerMultiplication -> IntegerAddition       ✗
```

Thus `multiply -> add` is not silently treated as specialization. It belongs to a future semantic-growth stage.

## Runtime flow

1. `IntegerMultiplication [S0]` is the initial programmer-defined capability.
2. `multiply(6, 7)` executes the existing S0 capability.
3. A request such as `multiply(2.5, 4.0)` is detected as a missing typed capability.
4. The system creates `SerializeCapability [S0]` when needed and reparents the existing integer capability without changing its ID or state.
5. A transient `S0-C` copy is created.
6. The type-specialization rule table is checked.
7. Only type annotations are transformed; the multiplication operation is preserved.
8. The candidate is verified.
9. A verified specialization becomes `S1` and is registered as a sibling of the S0 capability.
10. Later requests reuse the registered S1 capability.

Final hierarchy:

```text
SerializeCapability [S0]
├── IntegerMultiplication [S0]
└── FloatMultiplication [S1]
```

## Repository structure

```text
sps_specialization/
├── capability.py                  # capability model and execution
├── handler.py                     # runtime execution/resource owner
├── registry.py                    # lookup, lineage and persistence
├── replication.py                 # transient S0-C copy
├── specialization.py              # specialization facade
├── type_specialization.py          # deterministic transformer
├── type_specialization_rules.py    # Stage 1 growth boundary
├── evolution.py                    # evolution lifecycle
├── dispatcher.py                   # typed request routing
└── verifier.py                     # verification before activation

experiments/
└── self_specialization_demo.py     # main end-to-end demonstration

colab/
└── SPS_Self_Specialization_Test.ipynb

tests/
├── test_prototype.py
├── test_registry_persistent_location.py
└── test_type_specialization_rules.py

docs/superpowers/specs/
├── 2026-09-04-capability-registry.md
└── 2026-09-04-self-specialization-design.md
```

## Install and test locally

```bash
git clone https://github.com/muhammadnaumantahir/self-specialization.git
cd self-specialization

python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the complete test suite:

```bash
PYTHONPATH=. pytest -q
```

On Windows PowerShell, use:

```powershell
$env:PYTHONPATH = "."
pytest -q
```

## Run the research demo

For a clean first run:

Windows PowerShell:

```powershell
$env:SPS_DEMO_RESET = "1"
$env:PYTHONPATH = "."
python experiments/self_specialization_demo.py
```

macOS/Linux:

```bash
SPS_DEMO_RESET=1 PYTHONPATH=. python experiments/self_specialization_demo.py
```

The demo should show:

```text
=== INITIAL S0 ===
IntegerMultiplication [S0]: 6 * 7 = 42

=== FLOAT REQUEST ===
Request: multiply(2.5, 4.0)
Result: FloatMultiplication [S1] = 10.0

=== FINAL HIERARCHY ===
SerializeCapability [S0]
  ├── IntegerMultiplication [S0]
  └── FloatMultiplication [S1]

=== BOUNDARY ===
Allowed: int multiplication -> float/long/double multiplication
Rejected: multiplication -> addition
```

## Test the growth boundary directly

```bash
PYTHONPATH=. pytest -q tests/test_type_specialization_rules.py
```

The important test is the rejection of:

```text
IntegerMultiplication -> IntegerAddition
```

That request must fail because there is no matching Stage 1 rule and the semantic operation changes from multiplication to addition.

## Persistence

Generated capabilities are stored under:

```text
data/capability-registry/
├── registry.json
├── records/
└── sources/
```

The location can be overridden with:

```text
SPS_CAPABILITY_REGISTRY_DIR
```

The runtime data directory is ignored by Git so generated research artifacts remain local.

## Google Colab

Open `colab/SPS_Self_Specialization_Test.ipynb` and run the cells in order. The notebook clones the current `main` branch, installs the requirements, runs the tests, runs the deterministic demo, and checks the rule boundary.

No Ollama setup is required.

## Research boundary

This prototype demonstrates **capability-level runtime self-specialization with bounded growth**. It is intentionally not a general autonomous programming system.

Semantic growth such as:

```text
IntegerMultiplication -> IntegerAddition
```

should be implemented later as a separate growth mechanism with its own rules, constraints and verification.
