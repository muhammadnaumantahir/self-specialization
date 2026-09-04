# SPS Self-Specialization Prototype

A minimal research prototype demonstrating two capabilities from the self-programming research problem:

1. An existing capability can generate a copy of itself.
2. The generated copy can be transformed into a specialized capability.

The prototype intentionally focuses on the small State 0 → State 1 experiment and does **not** attempt to implement the full SPS ten-layer architecture.

## Core research lifecycle

The important distinction is that `SerializeCapability` is **not present initially**.

```text
INITIAL
IntegerMultiplication [S0]
        │
        │ Float request arrives
        ▼
FloatMultiplication missing
        │
        ▼
Serialize / Generalize IntegerMultiplication [S0]
        │
        ▼
SerializeCapability [S0]  ← CREATED NOW
        │
        ├── IntegerMultiplication [S0]  ← SAME ID, reparented
        │
        ▼
Replicate IntegerMultiplication
        │
        ▼
Transient IntegerMultiplication-C [S0-C]
        │
        ▼
Ollama + Qwen Coder specialization
        │
        ▼
FloatMultiplication [GENERATED]
        │
        ▼
Verification
        │
        ▼
FloatMultiplication [S1]
        │
        ▼
Attach under SerializeCapability
```

## Before and after

### Before the float request

The persistent registry contains exactly the programmer-defined capability:

```text
IntegerMultiplication [S0]
```

There is:

- no `SerializeCapability`
- no `FloatMultiplication`
- no permanent replication copy

The integer implementation is:

```python
def execute(a: int, b: int) -> int:
    return a * b
```

It can immediately execute:

```text
multiply(6, 7) → 42
```

### After the float request

When the request

```text
multiply(2.5, 4.0)
```

arrives, the dispatcher detects that `[float, float] -> float` is missing.

The existing `IntegerMultiplication [S0]` capability is selected as the source. The system then creates the generalization boundary dynamically:

```text
SerializeCapability [S0]
```

The **existing integer capability is reparented**, preserving its original ID and its State 0 status.

A transient copy is then made for specialization. The copy is sent to the external brain (Ollama + `qwen2.5-coder:7b`), verified, and activated as State 1.

Final persistent hierarchy:

```text
              SerializeCapability [S0]
                        │
               ┌────────┴────────┐
               ▼                 ▼
 IntegerMultiplication    FloatMultiplication
        [S0]                    [S1]
```

The transient `S0-C` copy is an evolution mechanism and is **not** a final hierarchy node.

## Why IntegerMultiplication remains S0

State labels describe the capability's evolutionary state, not its depth in the hierarchy.

| State | Meaning |
|---|---|
| `S0` | Original/general capability state supplied or established without specialization |
| `S0-C` | Transient replicated copy used as the specialization substrate |
| `GENERATED` | Generated source exists but is not yet activated |
| `S1` | Verified, activated specialized capability |
| `FAILED` | Generation or verification failed |

Therefore:

```text
IntegerMultiplication = S0
SerializeCapability   = S0
FloatMultiplication   = S1
```

Creating `SerializeCapability` does **not** promote `IntegerMultiplication` to S1. The original capability remains State 0; only the verified specialized result becomes State 1.

## Complete runtime sequence

```text
1. IntegerMultiplication [S0] exists
2. User requests float multiplication
3. Dispatcher detects FloatMultiplication is missing
4. Existing IntegerMultiplication [S0] is selected as the source
5. System serializes/generalizes the existing source
6. SerializeCapability [S0] is created at runtime
7. Existing IntegerMultiplication [S0] is reparented under it
8. IntegerMultiplication is replicated into transient S0-C
9. Ollama/Qwen transforms the copy into FloatMultiplication
10. Generated source enters GENERATED state
11. Verifier checks syntax, policy and functional cases
12. Verified FloatMultiplication becomes S1
13. FloatMultiplication is linked directly under SerializeCapability
14. Generated metadata and source are persisted
15. Later float requests reuse the persisted S1 capability
```

## Capability Handler

Each capability owns a lightweight `CapabilityHandler` responsible for runtime concerns:

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

The handler addresses the research question: when a generated capability exists, **where is its handling and what resources does it own?**

It is intentionally lightweight and is not a production process supervisor or security sandbox.

## Component responsibilities

### `SerializeCapability`

A general capability created **on demand** when a missing specialization requires a generalization boundary. It is not pre-installed.

### `IntegerMultiplication`

The programmer-defined State 0 source capability. It remains S0 throughout this experiment and supplies the implementation that can be replicated and specialized.

### `CapabilityHandler`

The runtime owner of execution and lightweight capability resources.

### `CapabilityRegistry`

Stores capability identity, contracts, parent/child relationships, events, source code and handler metadata. It supports lookup, inspection, lineage, persistence, reload and reparenting.

### `ReplicationEngine`

Creates the transient `S0-C` copy. This proves the copy-generation step without polluting the final capability hierarchy.

### `SpecializationEngine`

Asks the external model to transform the replicated implementation into the requested specialization.

### `OllamaClient`

Connects to local Ollama. The default model is `qwen2.5-coder:7b`.

### `Verifier`

Checks generated source before activation using syntax/AST restrictions and functional test cases.

### `EvolutionEngine`

Coordinates dynamic serialization/generalization, reparenting, replication, AI specialization, verification and activation.

### `CapabilityDispatcher`

Receives typed requests, chooses an existing capability when possible, and triggers evolution when the requested typed capability is missing.

## Event trace

The dynamic process is observable through events such as:

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

The events are persisted with capability metadata and exposed through registry inspection.

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

After reload, the S1 float capability can be reused without another AI generation step, while the original integer capability remains S0.

## Deterministic tests

The tests do not require Ollama:

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

Coverage includes:

- initial State 0 integer capability
- transient S0-C replication
- generated float specialization
- source normalization
- verifier acceptance/rejection
- verification diagnostics
- Ollama failure diagnostics
- dispatcher reuse vs specialization
- dynamic creation of `SerializeCapability`
- reparenting the existing `IntegerMultiplication` without changing its ID
- preserving `IntegerMultiplication` as S0
- final sibling hierarchy
- handler execution/resources
- persistence
- reload and reuse

## Google Colab

Use a fresh clone so the notebook always runs the current `main` branch:

```python
%cd /content
!rm -rf self-specialization
!git clone --branch main --single-branch https://github.com/muhammadnaumantahir/self-specialization.git
%cd /content/self-specialization
!git rev-parse HEAD
!pip install -q -r requirements.txt pytest
!PYTHONPATH=. pytest -q
```

Start Ollama from `/content` before deleting/recloning the repository. This avoids the Colab `llama-server process has terminated / cannot get current path` failure:

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

The demo explicitly prints the initial State 0 hierarchy and the post-request hierarchy.

## Research boundary

This is an experiment-grade proof of concept, not a production autonomous programming system.

It intentionally excludes:

- the full SPS ten-layer architecture
- multi-agent orchestration
- cloud APIs
- paid credentials
- a production security sandbox
- unrestricted autonomous code execution

The narrow research question is:

> **Can an existing State 0 capability create a generalization boundary on demand, generate a copy of itself, transform that copy with an external AI model, verify the result, and activate the specialization as a reusable State 1 sibling while preserving the original State 0 capability?**

## Research observation

The key result is the distinction between **generalization**, **copy generation**, and **specialization**:

```text
INITIAL
IntegerMultiplication [S0]

REQUEST
FloatMultiplication missing

EVOLUTION
IntegerMultiplication [S0]
        ↓
Serialize / Generalize
        ↓
SerializeCapability [S0]  ← dynamically created
        ↓
Reparent existing IntegerMultiplication [S0]
        ↓
Replicate → S0-C
        ↓
Specialize with Qwen
        ↓
Verify
        ↓
FloatMultiplication [S1]

FINAL
              SerializeCapability [S0]
                        │
               ┌────────┴────────┐
               ▼                 ▼
 IntegerMultiplication    FloatMultiplication
        [S0]                    [S1]
```

This is the intended State 0 → State 1 prototype: the programmer-defined integer capability remains the original S0 capability, while the generated and verified float specialization becomes S1.
