# SPS Self-Specialization Prototype

A minimal research prototype demonstrating two capabilities from the self-programming research problem:

1. An existing capability can generate a copy of itself.
2. The generated copy can be transformed into a bounded specialized capability.

The prototype intentionally focuses on the small State 0 → State 1 experiment and does **not** attempt to implement the full SPS ten-layer architecture.

## Stage 1: bounded type specialization

This implementation deliberately removes the AI/model dependency from specialization.

The rule boundary is a separate file:

```text
sps_specialization/type_specialization_rules.py
```

Only transformations explicitly declared there are allowed. The transformer does **not** invent a new operation.

For the current multiplication family:

```text
IntegerMultiplication [S0]
   ├── FloatMultiplication  ✓
   ├── LongMultiplication   ✓
   ├── DoubleMultiplication ✓
   └── IntegerAddition      ✗
```

Therefore:

```text
IntegerMultiplication → FloatMultiplication   = type specialization
IntegerMultiplication → LongMultiplication    = type specialization
IntegerMultiplication → DoubleMultiplication  = type specialization
IntegerMultiplication → IntegerAddition       = rejected
```

Semantic growth such as `multiply → add` is intentionally reserved for a later stage and is not part of Stage 1.

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
Transient IntegerMultiplication-copy [S0-C]
        │
        ▼
Deterministic TypeSpecializationTransformer
        │
        │ consults explicit type_specialization_rules.py
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

## Before the float request

The persistent registry contains the programmer-defined capability:

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

## After the float request

When the request

```text
multiply(2.5, 4.0)
```

arrives, the dispatcher detects that `[float, float] -> float` is missing.

The existing `IntegerMultiplication [S0]` capability is selected as the source. The system then creates the generalization boundary dynamically:

```text
SerializeCapability [S0]
```

The **existing integer capability is reparented**, preserving its original ID and State 0 status.

A transient copy is then made for specialization. The deterministic transformer checks the source operation and the exact source/target type contract against the explicit rules. Only if a declared rule matches can the new capability be created.

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
| `FAILED` | Specialization or verification failed |

Therefore:

```text
IntegerMultiplication = S0
SerializeCapability   = S0
FloatMultiplication   = S1
```

Creating `SerializeCapability` does **not** promote `IntegerMultiplication` to S1. The original capability remains State 0; only the verified specialized result becomes State 1.

## Type specialization rules

`type_specialization_rules.py` is the explicit growth boundary for Stage 1.

A rule contains:

```text
source operation
source input types
source output type
target input types
target output type
runtime Python annotations
```

The matching process is:

```text
Source capability
       │
       ▼
Detect source operation
       │
       ▼
Detect requested target operation
       │
       ├── different operation ──→ REJECT
       │
       ▼
Exact source/target contract lookup
       │
       ├── no declared rule ─────→ REJECT
       │
       ▼
Transform only the type annotations
       │
       ▼
Preserve original multiplication body
       │
       ▼
Generate candidate → Verify → S1
```

The implementation therefore has no path in the Stage 1 transformer from multiplication to addition. To add such a transformation later, a **different semantic-growth mechanism** must be designed explicitly rather than silently extending the type-specialization rules.

## Future numeric specializations

The rule table already establishes the extension mechanism for additional numeric forms:

```text
IntegerMultiplication [S0]
       │
       ├── FloatMultiplication  [S1]
       ├── LongMultiplication   [S1]
       └── DoubleMultiplication [S1]
```

`long` is represented as a logical integer-width target and `double` as a logical floating-point target while Python runtime annotations map them to supported Python primitives. The logical type remains part of the capability contract.

Adding a new legal path is therefore a rule change, not a transformer rewrite.

## Complete runtime sequence

```text
1. IntegerMultiplication [S0] exists
2. User requests float multiplication
3. Dispatcher detects FloatMultiplication is missing
4. Existing IntegerMultiplication [S0] is selected as the source
5. System creates SerializeCapability [S0] when the family needs a generalization boundary
6. Existing IntegerMultiplication [S0] is reparented under it
7. IntegerMultiplication is replicated into transient S0-C
8. TypeSpecializationTransformer identifies the source operation
9. Stage 1 rule table validates the exact type transformation
10. Transformer changes the type annotations and preserves the multiplication body
11. Generated source enters GENERATED state
12. Verifier checks syntax, policy and functional cases
13. Verified FloatMultiplication becomes S1
14. FloatMultiplication is linked directly under SerializeCapability
15. Generated metadata and source are persisted
16. Later float requests reuse the persisted S1 capability
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

### `TypeSpecializationTransformer`

Performs the deterministic Stage 1 transformation using only the explicit rules from `type_specialization_rules.py`.

### `SpecializationEngine`

Facade for the Stage 1 deterministic specialization mechanism.

### `Verifier`

Checks candidate source before activation using syntax/AST restrictions and functional test cases.

### `EvolutionEngine`

Coordinates dynamic serialization/generalization, reparenting, replication, deterministic specialization, verification and activation.

### `CapabilityDispatcher`

Receives typed requests, chooses an existing capability when possible, and triggers evolution when the requested typed capability is missing.

## Event trace

The dynamic process is observable through events such as:

```text
SERIALIZE
REPARENT
REPLICATE
SPECIALIZE
TYPE_SPECIALIZE
GENERATED
VERIFY_PASS
ACTIVATE
CHILD_LINK
```

The events are persisted with capability metadata and exposed through registry inspection.

## Persistence

The capability registry is application-owned by default:

```text
data/capability-registry/
├── registry.json
├── records/
│   ├── <capability-id>.json
│   └── ...
└── sources/
    ├── <capability-id>_IntegerMultiplication.py
    ├── <capability-id>_FloatMultiplication.py
    └── ...
```

Set `SPS_CAPABILITY_REGISTRY_DIR` to override this location for CI or experiments.

The JSON record contains state, contracts, relationships, events and handler metadata. The Python file contains executable source.

After reload, the S1 float capability can be reused without another transformation step, while the original integer capability remains S0.

## Tests

No model server, Ollama installation, API key or network service is required:

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

Coverage includes:

- initial State 0 integer capability
- transient S0-C replication
- deterministic float specialization
- explicit type rule matching
- deterministic future numeric targets (`long`, `double`)
- rejection of multiplication → addition
- rejection of unsupported target types
- verifier acceptance/rejection
- verification diagnostics
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

Run the deterministic demo directly:

```python
%cd /content/self-specialization
!PYTHONPATH=. python experiments/self_specialization_demo.py
```

To start from a clean capability registry for a research run:

```python
!SPS_DEMO_RESET=1 PYTHONPATH=. python experiments/self_specialization_demo.py
```

## Research boundary

This is an experiment-grade proof of concept, not a production autonomous programming system.

It intentionally excludes:

- the full SPS ten-layer architecture
- semantic growth operators
- multi-agent orchestration
- cloud APIs
- paid credentials
- a production security sandbox
- unrestricted autonomous code execution

The narrow Stage 1 research question is:

> **Can an existing State 0 capability generate a copy of itself and deterministically transform that copy into an allowed type-specialized capability, while rejecting transformations that cross the declared type-specialization boundary?**

The next research stage can address a separate question:

> **Can the system perform semantic growth, such as multiplication → addition, under an independently defined and constrained growth mechanism?**

## Research observation

The key result is the separation between **generalization**, **copy generation**, **type specialization**, and future **semantic growth**:

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
Check explicit Type Specialization Rules
        ↓
Transform types only
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

The Stage 1 transformer is deliberately bounded: the rules file defines what type growth is legal, while semantic changes are left for a separate future growth mechanism.
