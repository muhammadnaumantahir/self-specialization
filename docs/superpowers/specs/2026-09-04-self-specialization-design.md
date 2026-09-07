# Self-Specialization Prototype Design

## Goal

Demonstrate a bounded self-specialization mechanism in which a programmer-defined capability can replicate itself and a replicated copy can be transformed into a new typed capability without changing its operation.

Stage 1 is deterministic and does not require AI or a model server.

Canonical example:

```text
IntegerMultiplication [S0]
        |
        v
Transient copy [S0-C]
        |
        v
Type Specialization Rules
        |
        +--> FloatMultiplication [GENERATED]
        |
        v
Verification
        |
        v
FloatMultiplication [S1]
```

## Research Question

> Can a running system create a managed copy of an existing capability, apply an explicit type-only specialization rule to that copy, verify the result, and activate the new capability while preserving the original capability?

## Stage 1 Growth Boundary

Type specialization is governed exclusively by:

```text
sps_specialization/type_specialization_rules.py
```

A transformation is allowed only when:

1. The source and target operations are the same.
2. The complete source contract matches a declared rule.
3. The complete target contract matches a declared rule.

Therefore:

```text
IntegerMultiplication -> FloatMultiplication   ALLOWED
IntegerMultiplication -> LongMultiplication    ALLOWED
IntegerMultiplication -> DoubleMultiplication  ALLOWED
IntegerMultiplication -> IntegerAddition       REJECTED
```

`multiply -> add` is semantic growth, not type specialization, and is reserved for a later mechanism.

## Scope

Included:

- Capability identity and lifecycle state.
- Runtime capability registry and parent/child lineage.
- Transient replication (`S0-C`).
- Deterministic type-only specialization.
- Explicit type-specialization rules.
- Verification before activation.
- Persistent capability metadata and Python source.
- Runtime dispatch and reuse of active `S1` capabilities.
- Deterministic unit tests.
- Google Colab reproduction without AI/model dependencies.

Excluded:

- Semantic growth (`multiply -> add`).
- Full ten-layer SPS architecture.
- Autonomous multi-agent planning.
- General-purpose autonomous software engineering.
- Production-grade sandbox/security guarantees.
- OS-level executable replacement.

## Components

### Capability

Typed executable unit with immutable identity, source, input/output contract, parent relationship, lifecycle state, handler and event history.

### CapabilityRegistry

Stores capabilities, lineage, metadata, events and source artifacts. The default application-owned location is:

```text
data/capability-registry/
```

The location can be overridden with `SPS_CAPABILITY_REGISTRY_DIR`.

### ReplicationEngine

Creates a transient independent `S0-C` copy from an existing capability. The copy is used as the specialization substrate and is not published as a final hierarchy node.

### TypeSpecializationTransformer

Performs the deterministic type-only transformation. It parses the source, detects the supported operation, checks the explicit rule table, replaces only type annotations, and preserves the original operation body.

### Type Specialization Rules

`type_specialization_rules.py` is the policy boundary. It is deliberately separate from the transformer so legal growth paths are explicit and reviewable.

### Verifier

Checks candidate source for syntax, restricted AST policy and functional behavior before activation. Verification failure produces `FAILED` and the capability remains inactive.

### EvolutionEngine

Coordinates generalization, reparenting, replication, deterministic specialization, verification and activation.

### CapabilityDispatcher

Resolves an existing typed capability when available. When a typed specialization is missing, it invokes the evolution path using the requested specialization contract.

## Lifecycle

```text
S0
 |
 +--> S0-C
       |
       +--> rule rejected -> FAILED
       |
       v
    GENERATED
       |
       +--> verification failed -> FAILED
       |
       v
      S1
```

For the current experiment:

```text
Before request:
IntegerMultiplication [S0]

After float request:
SerializeCapability [S0]
├── IntegerMultiplication [S0]
└── FloatMultiplication [S1]
```

Creating `SerializeCapability` does not change the original integer capability's state.

## Persistence

An active generated capability is persisted as:

```text
data/capability-registry/
├── registry.json
├── records/<capability-id>.json
└── sources/<capability-id>_<name>.py
```

The transient `S0-C` copy is not persisted as a final capability.

## Testing Strategy

The test suite must prove:

- IntegerMultiplication starts as S0 and executes correctly.
- Replication creates S0-C.
- Integer -> float specialization works without AI.
- Integer -> long and integer -> double are recognized as legal Stage 1 paths.
- Multiplication -> addition is rejected by the rule boundary.
- Non-declared type transformations are rejected.
- The transformation preserves the multiplication body.
- Verification gates S1 activation.
- The original integer capability remains S0.
- The generated float capability is persisted, reloaded and reused.

Run:

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

## Research Boundary

This prototype demonstrates bounded runtime self-specialization at capability level. It should not be presented as complete general self-programming or unrestricted self-modification.
