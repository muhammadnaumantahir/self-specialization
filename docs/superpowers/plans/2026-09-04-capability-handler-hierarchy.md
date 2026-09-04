# Capability Handler and Dynamic State-0/State-1 Hierarchy Implementation Plan

> **Goal:** Demonstrate the research lifecycle exactly as approved: start with only programmer-defined `IntegerMultiplication [S0]`; when a float request is missing, dynamically serialize/generalize it into `SerializeCapability [S0]`, reparent the existing integer capability without changing its ID, replicate the integer into transient `S0-C`, specialize the copy, verify it, and activate `FloatMultiplication [S1]` as a sibling.

## Core architecture

The prototype deliberately separates three concepts:

1. **Generalization/serialization** — creates a general family boundary on demand.
2. **Replication** — creates a transient copy used as the transformation substrate.
3. **Specialization** — transforms that copy into a new typed capability.

The initial hierarchy is **not** rooted at `SerializeCapability`.

```text
BEFORE
IntegerMultiplication [S0]

AFTER FLOAT REQUEST
              SerializeCapability [S0]
                        │
               ┌────────┴────────┐
               ▼                 ▼
 IntegerMultiplication    FloatMultiplication
        [S0]                    [S1]
```

## State contract

- `S0`: original/general capability state.
- `S0-C`: transient copy used during specialization.
- `GENERATED`: generated source exists but is not active.
- `S1`: verified and active specialized capability.
- `FAILED`: generation or verification failed.

Creating `SerializeCapability` does **not** change `IntegerMultiplication` from S0 to S1.

## Implementation requirements

- `CapabilityHandler` owns lightweight runtime execution/resource metadata.
- `CapabilityRegistry` stores parent/child relationships, events, source and metadata and supports reparenting.
- `EvolutionEngine` creates `SerializeCapability` only when the missing specialization requires it.
- Existing `IntegerMultiplication` keeps its original ID and remains S0.
- `ReplicationEngine` creates only a transient `S0-C` artifact.
- `SpecializationEngine` uses Ollama/Qwen to transform the copy.
- `Verifier` gates activation.
- `FloatMultiplication` is activated as S1 and linked directly under SerializeCapability.
- The transient copy never appears in the final persistent hierarchy.

## Verification requirements

Deterministic tests must prove:

- initial registry contains only `IntegerMultiplication [S0]`;
- no SerializeCapability exists before the float request;
- float request dynamically creates SerializeCapability [S0];
- existing integer ID is preserved and its state remains S0;
- integer is reparented under SerializeCapability;
- transient S0-C copy is created and not persisted as a final node;
- generated float capability reaches S1 only after verification;
- final children are exactly integer S0 and float S1;
- reload preserves the hierarchy and reusable float capability.

## Documentation requirements

README and Colab must show the same lifecycle and must never describe the initial integer capability as S1. They must explicitly explain that State 1 belongs to the verified specialization.
