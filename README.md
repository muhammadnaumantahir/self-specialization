# SPS Self-Specialization Prototype

A minimal research prototype demonstrating how an existing capability can generate a copy of itself and how that copy can be transformed into a specialized capability.

The prototype intentionally focuses on the small concept from the research problem. It does **not** attempt to implement the full SPS ten-layer architecture.

## Research idea

The experiment demonstrates two fundamental abilities:

1. A capability can generate a transient copy of itself.
2. That generated copy can be transformed into a specialized capability.

The important lifecycle is:

```text
IntegerMultiplication [S1]
        │
        │ Float request arrives
        ▼
FloatMultiplication missing
        │
        ▼
Serialize/generalize existing IntegerMultiplication
        │
        ├── create SerializeCapability [S0] dynamically
        └── reparent existing IntegerMultiplication under it
        │
        ▼
replicate IntegerMultiplication
        │
        ▼
Transient copy [S0-C]
        │
        ▼
Ollama + Qwen Coder specialization
        │
        ▼
FloatMultiplication [GENERATED]
        │
        ▼
verification
        │
        ▼
FloatMultiplication [S1]
        │
        ▼
link under SerializeCapability
```

**Critical design rule:** `SerializeCapability` does **not** exist in the initial state. It is created only when the system needs a generalization boundary for the missing specialization.

## Before and after

### Initial state

Only the programmer-defined capability exists:

```text
IntegerMultiplication [S1]
```

There is no `SerializeCapability` node and no float capability.

### After a float request

A request such as:

```text
multiply(2.5, 4.0)
```

requires `[float, float] -> float`. The system cannot find an active capability for that contract, so it begins evolution.

The final persistent hierarchy is:

```text
              SerializeCapability [S0]
                        │
               ┌────────┴────────┐
               ▼                 ▼
 IntegerMultiplication    FloatMultiplication
        [S1]                    [S1]
```

The existing `IntegerMultiplication` object keeps the **same ID** and is reparented. It is not recreated.

The transient `S0-C` copy is not stored as a final hierarchy node.

## Complete runtime sequence

```text
1. IntegerMultiplication [S1] exists
2. User requests float multiplication
3. Dispatcher detects FloatMultiplication is missing
4. Existing IntegerMultiplication is selected as the source
5. System serializes/generalizes that source
6. SerializeCapability [S0] is created at runtime
7. Existing IntegerMultiplication is reparented under SerializeCapability
8. IntegerMultiplication is replicated into transient S0-C
9. Ollama/Qwen transforms the copy into FloatMultiplication
10. Generated source enters GENERATED state
11. Verifier checks syntax/policy and functional cases
12. Verified result becomes FloatMultiplication [S1]
13. FloatMultiplication is linked directly under SerializeCapability
14. S1 metadata/source are persisted
15. Later float requests reuse the persisted S1 capability
```

## Why serialization/generalization exists

The prototype uses `SerializeCapability` as the dynamically created general boundary for a capability family.

It is **not** a pre-installed parent. Its creation is itself part of the evolution event:

```text
existing capability
      ↓
SERIALIZE / GENERALIZE
      ↓
new S0 general capability
      ↓
existing capability becomes child
```

This makes the hierarchy reflect what actually happened at runtime instead of presenting a general parent that was secretly present from the beginning.

## State model

| State | Meaning |
|---|---|
| `S0` | General/static capability state |
| `S0-C` | Transient replicated copy used during specialization |
| `GENERATED` | Source generated but not yet activated |
| `S1` | Verified and active specialized capability |
| `FAILED` | Generation or verification failed |

The specialization path is therefore:

```text
S1 existing source
   │
   │ serialize/generalize
   ▼
S0 general parent
   │
   │ replicate
   ▼
S0-C transient copy
   │
   │ specialize with external brain
   ▼
GENERATED
   │
   │ verify
   ▼
S1 new specialization
```

## Capability Handler

Each capability has an explicit `CapabilityHandler` responsible for runtime concerns of that capability:

```text
Capability
    │
    └── CapabilityHandler
          ├── capability identity
          ├── executable function
          ├── resources
          │    ├── source code
          │    ├── input contract
          │    └── output contract
          ├── runtime status
          └── execution
```

The handler answers the research question: **when a generated capability exists, where is its handling and what does it own?**

The handler is deliberately lightweight. It is not a process supervisor or production security sandbox.

## Concrete example

The programmer initially supplies:

```python
def execute(a: int, b: int) -> int:
    return a * b
```

as:

```text
IntegerMultiplication [S1]
```

An integer request is handled directly and does not require AI:

```text
multiply(6, 7) → 42
```

Then the system receives:

```text
multiply(2.5, 4.0)
```

The required contract is:

```text
[float, float] -> float
```

No active capability matches it. The source capability is generalized, producing `SerializeCapability [S0]`, and the original integer capability is moved under it. A transient copy is then specialized by Ollama/Qwen.

The expected generated implementation is equivalent to:

```python
def execute(a: float, b: float) -> float:
    return a * b
```

Generated code is not activated immediately. It must first pass verification.

## Component responsibilities

### `SerializeCapability`

A general capability created **on demand** when a missing specialization requires a family/generalization boundary.

### `IntegerMultiplication`

The statically programmed source capability. It supplies the implementation that can be copied and specialized.

### `CapabilityHandler`

The runtime owner of execution and lightweight capability resources.

### `CapabilityRegistry`

Stores capability identity, contracts, parent/child relationships, events, source code and handler metadata. It also supports lookup, inspection, lineage, persistence, reload and reparenting.

### `ReplicationEngine`

Creates the transient `S0-C` copy. This copy is an evolution artifact, not a permanent capability-family node.

### `SpecializationEngine`

Asks the external model to transform the replicated implementation into the target specialization.

### `OllamaClient`

Connects to local Ollama. The default model is `qwen2.5-coder:7b`.

### `Verifier`

Checks generated source before activation using syntax/AST restrictions and functional test cases.

### `EvolutionEngine`

Coordinates serialization/generalization, reparenting, replication, AI specialization, verification and activation.

### `CapabilityDispatcher`

Receives typed requests, chooses an existing capability when possible, and triggers evolution when the requested typed capability is missing.

## Event trace

The dynamic generalization is observable through events such as:

```text
SERIALIZE
REPARENT
REPLICATE
SPECIALIZE
GENERATED
VERIFY_PASS
ACTIVATE
CHILD_LINK
```

The events are persisted with capability metadata and exposed through `registry.inspect()`.

## Persistence

The registry writes:

```text
/tmp/sps-capability-registry/
├── registry.json
├── records/
│   ├── <capability-id>.json
│   └── ...
└── sources/
    ├── <capability-id>_IntegerMultiplication.py
    ├── <capability-id>_FloatMultiplication.py
    └── ...
```

The JSON record contains state, contracts, relationships, events and handler metadata. The Python file contains executable source.

After reload, the S1 float capability can be reused without another AI generation step.

## Project layout

```text
sps_specialization/
├── capability.py       # capability contract and lifecycle
├── handler.py          # runtime capability handler
├── registry.py         # lookup, hierarchy, persistence, reparenting
├── replication.py      # transient S0-C replication
├── specialization.py   # AI-assisted specialization
├── ollama_client.py    # local Ollama adapter
├── verifier.py         # generated-code verification
├── evolution.py        # dynamic generalization + evolution flow
└── dispatcher.py       # typed request routing

experiments/
└── self_specialization_demo.py

tests/
└── test_prototype.py

colab/
└── SPS_Self_Specialization_Test.ipynb
```

## Deterministic tests

The tests do not require Ollama:

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

Coverage includes:

- initial integer capability
- transient S0-C replication
- generated float specialization
- source normalization
- verifier acceptance/rejection
- verification diagnostics
- Ollama failure diagnostics
- dispatcher reuse vs specialization
- **dynamic creation of SerializeCapability**
- **reparenting the existing IntegerMultiplication without changing its ID**
- **final sibling hierarchy**
- handler execution/resources
- persistence
- reload and reuse

## Local Ollama experiment

Start Ollama from a stable working directory before changing or deleting the repository directory:

```bash
cd /tmp
ollama serve
```

In another terminal:

```bash
ollama pull qwen2.5-coder:7b
export OLLAMA_MODEL=qwen2.5-coder:7b
```

Then:

```bash
cd self-specialization
PYTHONPATH=. python experiments/self_specialization_demo.py
```

The demo prints both the initial state and the final hierarchy so the dynamic creation of `SerializeCapability` is visible.

## Google Colab

Use a fresh clone:

```python
%cd /content
!rm -rf self-specialization
!git clone --branch main --single-branch https://github.com/muhammadnaumantahir/self-specialization.git
%cd /content/self-specialization
!git rev-parse HEAD
!pip install -q -r requirements.txt
!PYTHONPATH=. pytest -q
```

Start Ollama from `/content` before deleting/recloning the repository:

```python
%cd /content
!apt-get update -qq
!apt-get install -y -qq zstd curl
!curl -fsSL https://ollama.com/install.sh | sh
!pkill -9 ollama || true
!pkill -9 llama-server || true
!nohup ollama serve >/tmp/ollama.log 2>&1 &
!sleep 5
!ollama --version
!curl -sf http://127.0.0.1:11434/api/tags || (cat /tmp/ollama.log; exit 1)
!ollama pull qwen2.5-coder:7b
```

Then:

```python
%cd /content/self-specialization
!PYTHONPATH=. python experiments/self_specialization_demo.py
```

## Research boundary

This is an experiment-grade proof of concept, not a production autonomous programming system.

It intentionally excludes:

- the full SPS ten-layer architecture
- multi-agent orchestration
- cloud APIs
- paid credentials
- a production security sandbox
- unrestricted autonomous code execution

The research target is deliberately narrow:

> **Can an existing capability create a generalization boundary on demand, generate a copy of itself, transform that copy with an external AI model, verify the result, and activate the specialization as a reusable sibling capability?**

## Research observation

The most important architectural observation is:

```text
INITIAL
IntegerMultiplication [S1]

REQUEST
FloatMultiplication missing

EVOLUTION
IntegerMultiplication
        ↓
Serialize/generalize
        ↓
SerializeCapability [S0]
        ↓
reparent existing IntegerMultiplication
        ↓
replicate → S0-C
        ↓
specialize with Qwen
        ↓
verify
        ↓
FloatMultiplication [S1]

FINAL
              SerializeCapability [S0]
                        │
               ┌────────┴────────┐
               ▼                 ▼
 IntegerMultiplication    FloatMultiplication
        [S1]                    [S1]
```

This keeps the **copy** as a transformation mechanism and the **general capability** as a runtime-created family boundary. That distinction is the core correction implemented by this iteration.
