# Self-Specialization Prototype Design

## Goal
Build a small research prototype demonstrating that a statically programmed capability can replicate itself and have the replicated child transformed into a specialized capability using an external local coding model.

The canonical experiment is:

`IntegerMultiplication (S0) -> replicated child (S0-C) -> Ollama specialization -> FloatMultiplication (S1)`

The prototype is intentionally narrow and is not an implementation of the full ten-layer SPS architecture.

## Research Question
Can a capability create a managed copy of itself and, using an external reasoning/code-generation model, transform that copy into a new specialized capability that is verified before activation?

## Scope
Included:
- Capability contract and lifecycle state.
- Capability registry and parent/child lineage.
- Replication of an existing capability.
- Specialization request to local Ollama.
- Generated Python implementation for the specialized capability.
- AST/safety checks and isolated functional verification.
- Activation only after verification succeeds.
- Event/lineage trace sufficient to show the evolutionary transition.
- Deterministic unit tests using a fake Ollama client.
- A Colab notebook for an end-to-end Ollama experiment.

Excluded:
- UI.
- Full SPS ten-layer architecture.
- Autonomous multi-agent orchestration.
- Production-grade sandboxing.
- Cloud model APIs or paid API keys.
- General-purpose autonomous software engineering.

## Architecture

```text
IntegerMultiplication (S0)
        |
        v
Replication Engine
        |
        v
IntegerMultiplication-child (S0-C)
        |
        v
Specialization Engine -> Ollama
        |
        v
Generated FloatMultiplication source
        |
        v
Verifier
  - syntax
  - restricted imports/AST checks
  - isolated functional tests
        |
   PASS | FAIL
        |       \
        v        v
      S1       FAILED
        |
        v
     Registry + lineage
```

## Components

### Capability
A capability is a typed executable unit with immutable identity and mutable lifecycle state. It records its parent capability, source code, input/output contract, and lifecycle timestamps.

Minimum fields:
- `id`
- `name`
- `version`
- `state`
- `parent_id`
- `input_types`
- `output_type`
- `source_code`
- `created_at`
- `activated_at`

The executable entry point is `execute(a, b)` for this prototype.

### Registry
Stores capabilities by ID and provides lineage traversal. A capability cannot be activated twice and a failed capability is not returned as active.

### Replication Engine
Creates a new capability record from a parent. Replication preserves the parent's executable behavior and contract but assigns a new ID and records `parent_id`.

### Specialization Engine
Takes a replicated capability and a target specialization. It sends the parent contract and target requirements to Ollama and parses the returned Python source. Generated code is attached to the child but remains inactive.

### Ollama Adapter
Uses the local Ollama HTTP API at `http://localhost:11434/api/generate`. The model is configurable through `OLLAMA_MODEL` and defaults to `qwen2.5-coder:7b`. No credentials are required.

The prompt must explicitly state that the model is generating a specialization of the supplied capability rather than inventing an unrelated function.

### Verifier
Generation is not activation. Generated source must pass:
1. Python AST parsing.
2. A restricted AST policy that rejects dangerous imports/calls and requires `execute`.
3. Execution in an isolated subprocess with a timeout.
4. Functional tests for float multiplication.

The verifier must fail closed: any generation, parse, policy, or runtime failure produces `FAILED` and the generated capability is never activated.

This is an experiment-grade execution boundary, not a security guarantee against hostile native code.

### Lineage/Event Trace
Record events such as `REGISTER`, `REPLICATE`, `SPECIALIZE`, `GENERATED`, `VERIFY_PASS`, `VERIFY_FAIL`, `ACTIVATE`, and `FAILED`. The final experiment prints the lineage from the original capability through its specialized descendant.

## Lifecycle

```text
S0 -> S0-C -> SPECIALIZING -> GENERATED -> VERIFIED -> S1
                                  |
                                  +-> FAILED
```

- `S0`: programmer-created IntegerMultiplication.
- `S0-C`: replicated child before specialization.
- `SPECIALIZING`: child is awaiting model-generated specialization.
- `GENERATED`: source has been returned by Ollama.
- `VERIFIED`: source has passed all verification gates.
- `S1`: specialized capability is active and registered.
- `FAILED`: specialization or verification failed; never active.

## Canonical Demonstration

The initial source is only integer multiplication. The experiment then asks Ollama to specialize the replicated child into float multiplication. The expected generated contract is equivalent to:

```python
def execute(a: float, b: float) -> float:
    return a * b
```

The exact generated formatting may vary; the behavior and contract are what are verified.

Expected lineage:

```text
IntegerMultiplication (S0)
  └── IntegerMultiplication-child (S0-C)
        └── FloatMultiplication (S1)
```

## Failure Experiment

The test suite must include a generated specialization that violates the verifier policy or functional contract. The system must report failure, keep the capability inactive, and preserve the failed lineage event. This demonstrates the distinction between `Generation` and `Activation`.

## Testing Strategy

Unit tests use a fake Ollama adapter so the core lifecycle is deterministic and does not require a running model. Tests cover:
- capability creation and execution;
- replication and parent linkage;
- specialization prompt/response handling;
- generated-source parsing;
- verifier acceptance of valid float multiplication;
- verifier rejection of unsafe/invalid code;
- registry activation rules;
- lineage events;
- failed specialization never becoming active.

The Colab notebook performs the real Ollama integration separately and runs the same experiment against `qwen2.5-coder:7b` when the model is available.

## Success Criteria

The prototype succeeds when:
1. Only IntegerMultiplication is initially programmed.
2. The system creates a distinct child with parent linkage.
3. Ollama supplies the specialization source.
4. The verifier accepts a correct float specialization.
5. The specialized capability becomes `S1` and executes float multiplication.
6. The lineage clearly shows `S0 -> S0-C -> S1`.
7. A failed/unsafe generated specialization is rejected and never activated.
8. The full deterministic test suite passes without Ollama.
9. The Colab notebook contains a reproducible real-model experiment.

## Repository Placement

The prototype lives under `self-specialization/` in the existing private `muhammadnaumantahir/Letter` repository. Work is isolated on branch `feat/self-specialization-prototype`; `main` is not modified by this implementation.