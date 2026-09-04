# SPS Self-Specialization Prototype

A minimal research prototype demonstrating how a general capability can manage specialized child capabilities and how a missing capability can be created through **replication → AI-assisted specialization → verification → activation**.

This prototype intentionally focuses on the small concept described by the research problem. It does **not** attempt to implement the full SPS ten-layer architecture.

## Research idea

The experiment demonstrates two related abilities:

1. A capability family can have a **general parent** that manages specialized capabilities.
2. When a required specialization does not exist, an existing capability can be **replicated into a transient S0-C copy**, transformed by an external reasoning/code-generation model, verified, and activated as a new S1 capability.

The important distinction is:

```text
Replication = system mechanism
Specialization = transformation/reasoning process
Ollama + Qwen = external brain used for code generation
Verification = gate before activation
Capability Handler = runtime owner of execution/resources/lifecycle
Registry = persistent capability knowledge
```

## Complete experiment flow

```text
                         GENERAL CAPABILITY
                       SerializeCapability [S0]
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
              ▼                                   ▼
     IntegerMultiplication [S1]          FloatMultiplication [S1]
          statically defined                 generated at runtime

Missing float request:

SerializeCapability [S0]
        │
        │ detect missing [float, float] → float
        ▼
IntegerMultiplication [S1]  ← source capability
        │
        │ REPLICATE
        ▼
Transient copy [S0-C]
        │
        │ SPECIALIZE
        ▼
Ollama + Qwen Coder
        │
        │ generate Python execute(a, b)
        ▼
Generated FloatMultiplication [GENERATED]
        │
        │ VERIFY
        ├── syntax / AST policy
        └── functional test cases
        │
        ▼
FloatMultiplication [S1]
        │
        │ link to general parent
        ▼
SerializeCapability [S0]
        │
        └── FloatMultiplication [S1]
```

### Final capability hierarchy

The **persistent hierarchy is intentionally not**:

```text
IntegerMultiplication
        └── IntegerMultiplication-child
                └── FloatMultiplication
```

Instead it is:

```text
                    SerializeCapability [S0]
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
       IntegerMultiplication       FloatMultiplication
               [S1]                       [S1]
```

The S0-C copy is an internal evolution artifact. It proves the replication step without becoming a misleading permanent parent in the capability hierarchy.

## Capability Handler

Each capability has an explicit `CapabilityHandler` responsible for the runtime concerns of that capability.

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

The handler answers the research question: **when a capability exists, where is its handling and what does it own?**

The handler is deliberately lightweight. It is not a process supervisor or security sandbox. It owns the execution-facing runtime state needed by this prototype.

## State model

| State | Meaning |
|---|---|
| `S0` | General/static capability state |
| `S0-C` | Transient replicated copy used during specialization |
| `GENERATED` | Source generated but not yet activated |
| `S1` | Verified and active specialized capability |
| `FAILED` | Generation or verification failed |

The core transition is:

```text
S0
 │
 │ missing capability detected
 ▼
replicate
 │
 ▼
S0-C
 │
 │ AI-assisted specialization
 ▼
GENERATED
 │
 │ verification
 ▼
S1
```

For the final hierarchy, the generated S1 capability is linked directly to the general `SerializeCapability` parent.

## Concrete example

The prototype starts with:

```text
SerializeCapability [S0]
        │
        └── IntegerMultiplication [S1]
```

The integer capability is statically supplied by the programmer:

```python
def execute(a: int, b: int) -> int:
    return a * b
```

The request:

```text
multiply(6, 7)
```

is already supported, so the system executes the existing capability. **No AI call is required.**

Then the system receives:

```text
multiply(2.5, 4.0)
```

Required contract:

```text
[float, float] -> float
```

No active capability matches that contract, so the evolution process starts.

The external model is asked to transform the replicated integer capability into a float-specialized capability. For the experiment, the expected generated function is equivalent to:

```python
def execute(a: float, b: float) -> float:
    return a * b
```

The generated code is **not activated immediately**. It first passes syntax/policy checks and functional test cases.

After verification:

```text
SerializeCapability [S0]
        ├── IntegerMultiplication [S1]
        └── FloatMultiplication [S1]
```

The float capability can then be reused without another AI generation step.

## Role of each component

### `SerializeCapability`

The general/root capability for the experiment. It represents the capability family and becomes the parent of specialized capabilities.

### `IntegerMultiplication`

The statically programmed source capability. It provides the existing implementation from which a missing multiplication specialization can be derived.

### `CapabilityHandler`

The runtime owner of execution and lightweight capability resources.

### `ReplicationEngine`

Creates the transient `S0-C` copy used by the specialization process. The copy is an evolution artifact rather than a permanent hierarchy node.

### `SpecializationEngine`

Builds the specialization request and asks the external model to generate the target implementation.

### `OllamaClient`

Connects to the local Ollama server. The default model is `qwen2.5-coder:7b`.

### `Verifier`

Checks generated source before activation. The prototype applies AST-level restrictions and executes functional test cases in a separate Python process with a timeout.

### `CapabilityRegistry`

Stores capability identity, contracts, parent/child relationships, events, source code and handler metadata. It also supports lookup, inspection, lineage and reload.

### `CapabilityDispatcher`

Receives typed requests, chooses an existing capability when possible, and triggers specialization when the requested typed capability is missing.

### `EvolutionEngine`

Coordinates the runtime sequence:

```text
source capability
      ↓
transient replication
      ↓
AI specialization
      ↓
verification
      ↓
S1 activation
      ↓
direct link to general parent
```

## Capability Handler and resources

A handler exposes serializable information such as:

```json
{
  "capability_id": "...",
  "status": "ready",
  "resources": {
    "source_code": "...",
    "input_types": ["float", "float"],
    "output_type": "float"
  }
}
```

Runtime-only callable state is kept inside the handler and is reconstructed from persisted source when a capability is reloaded.

## Persistence

The registry writes three useful artifacts:

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

The JSON record contains the capability contract, state, parent/child relationship, events and handler metadata. The Python file contains the executable source.

A new registry instance can reload the persisted S1 capability and execute it without calling Ollama again.

## Event trace

The generated capability records lifecycle events such as:

```text
REPLICATE
SPECIALIZE
GENERATED
VERIFY_PASS
ACTIVATE
CHILD_LINK
```

The actual event list is stored with the capability record and is available through `registry.inspect()`.

## Project layout

```text
sps_specialization/
├── capability.py       # capability contract and lifecycle
├── handler.py          # explicit runtime capability handler
├── registry.py         # lookup, hierarchy and persistence
├── replication.py      # transient S0-C replication
├── specialization.py   # AI-assisted source specialization
├── ollama_client.py    # local Ollama adapter
├── verifier.py         # generated-code verification
├── evolution.py        # replication → specialization → verification
└── dispatcher.py       # typed request routing

experiments/
└── self_specialization_demo.py  # complete research demonstration

tests/
└── test_prototype.py             # deterministic tests using fake Ollama

colab/
└── SPS_Self_Specialization_Test.ipynb
```

## Deterministic tests

The test suite does not require Ollama:

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

The tests cover:

- S0 integer execution
- S0-C replication
- generated float specialization
- generated-source normalization
- verifier acceptance/rejection
- verification failure diagnostics
- Ollama failure diagnostics
- dispatcher reuse vs specialization
- capability handler execution/resources
- general-parent hierarchy
- sibling specialized capabilities
- registry persistence
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

Then run:

```bash
cd self-specialization
PYTHONPATH=. python experiments/self_specialization_demo.py
```

The demo shows the complete runtime flow, final hierarchy, handler information, generated source, event trace, persistence paths, reload and reuse.

## Google Colab

Use a fresh clone so an older repository copy cannot shadow the current code:

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
- process/resource isolation beyond the prototype verifier

The research target is deliberately narrow:

> **Can a general capability manage specialized children, and can a missing specialization be created by replicating an existing capability, transforming the copy with an external AI model, verifying it, and activating it as a reusable capability?**

## Research contribution of this prototype

The prototype makes the proposed concept observable rather than leaving it as a theoretical diagram:

```text
GENERAL CAPABILITY
       ↓
CAPABILITY HANDLER
       ↓
MISSING CAPABILITY DETECTION
       ↓
REPLICATION (S0-C)
       ↓
AI-ASSISTED SPECIALIZATION
       ↓
GENERATED SOURCE
       ↓
VERIFICATION
       ↓
ACTIVATION (S1)
       ↓
PARENT/CHILD REGISTRATION
       ↓
PERSISTENCE
       ↓
RELOAD
       ↓
REUSE
```

The key research observation is that **the specialized capability becomes a managed child of the general capability**, while replication remains an internal mechanism used to produce the specialization.
