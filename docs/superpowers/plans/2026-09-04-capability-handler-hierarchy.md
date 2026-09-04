# Capability Handler and General-Parent Hierarchy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `SerializeCapability` the general S0 parent, make integer and float multiplication sibling specialized capabilities, introduce an explicit `CapabilityHandler`, and document the complete self-specialization flow.

**Architecture:** A `CapabilityHandler` owns execution-facing runtime responsibilities and lightweight resource/lifecycle metadata. `Capability` delegates execution to its handler while retaining its persisted identity and source. The registry records explicit parent/child relationships so `SerializeCapability [S0]` is the root and `IntegerMultiplication [S1]` / `FloatMultiplication [S1]` are children.

**Tech Stack:** Python 3, dataclasses, pytest, local Ollama HTTP API, Qwen Coder model.

**Spec:** `docs/superpowers/specs/2026-09-04-capability-registry.md` plus the approved hierarchy design from the user conversation.

## Global Constraints

- Keep the prototype minimal and research-focused.
- Do not reintroduce the SPS ten-layer architecture.
- Replication remains an internal mechanism; the persisted capability hierarchy uses the general capability as parent.
- Generated capabilities become active only after verification.
- Unit tests must not require Ollama.
- Preserve human-readable JSON metadata and Python source persistence.

---

### Task 1: Define the explicit Capability Handler contract

**Files:**
- Modify: `sps_specialization/capability.py`
- Modify: `sps_specialization/__init__.py`
- Test: `tests/test_prototype.py`

**Interfaces:**
- `CapabilityHandler(capability_id, resources=None, status="ready")`
- `CapabilityHandler.execute(function, a, b)`
- `Capability.handler` becomes a `CapabilityHandler` instance after source loading.
- `Capability.inspect_handler()` returns serializable handler metadata.

- [ ] **Step 1: Write failing tests**

Add assertions that a created capability has a handler, that handler metadata contains capability identity/status/resources, and that execution delegates through the handler.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

Run: `PYTHONPATH=. pytest -q tests/test_prototype.py -k "handler"`

Expected: FAIL because the explicit handler interface does not yet exist.

- [ ] **Step 3: Implement the minimal handler**

Introduce a small dataclass with identity, resource metadata, status, and an execution method. Keep the actual callable as a runtime-only field so it is not serialized.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `PYTHONPATH=. pytest -q tests/test_prototype.py -k "handler"`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add explicit capability handler`

---

### Task 2: Make SerializeCapability the hierarchy root

**Files:**
- Modify: `sps_specialization/capability.py`
- Modify: `sps_specialization/registry.py`
- Modify: `sps_specialization/evolution.py`
- Modify: `sps_specialization/dispatcher.py`
- Modify: `tests/test_prototype.py`

**Interfaces:**
- `Capability.children_ids` stores direct child capability IDs.
- `Capability.add_child(child_id)` records a relationship.
- `CapabilityRegistry.children(parent_id)` returns direct children.
- `CapabilityRegistry.lineage(capability_id)` follows `parent_id` to `SerializeCapability`.
- Evolution receives the general parent ID and creates the specialized capability with that parent ID.

- [ ] **Step 1: Write failing hierarchy tests**

Test that a `SerializeCapability` root has `IntegerMultiplication` as a child, that float specialization is also a direct child of the root, and that the float lineage is exactly `["SerializeCapability", "FloatMultiplication"]`.

- [ ] **Step 2: Run the hierarchy tests and verify failure**

Run: `PYTHONPATH=. pytest -q tests/test_prototype.py -k "hierarchy or lineage or children"`

Expected: FAIL because the current prototype uses `IntegerMultiplication` as the parent.

- [ ] **Step 3: Implement the hierarchy change**

Keep the generic root capability separate from executable multiplication capabilities. Register integer as a child of the root. When a missing float contract is detected, use the root as the evolution parent and register the generated float capability directly under it. Preserve replication as an internal event/mechanism, but do not expose the transient replicated child as the final capability hierarchy.

- [ ] **Step 4: Run the hierarchy tests and verify they pass**

Run: `PYTHONPATH=. pytest -q tests/test_prototype.py -k "hierarchy or lineage or children"`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: make general capability the specialization parent`

---

### Task 3: Persist and inspect handler/hierarchy metadata

**Files:**
- Modify: `sps_specialization/registry.py`
- Modify: `tests/test_prototype.py`

**Interfaces:**
- Registry JSON records include `parent_id`, `children_ids`, and `handler` metadata.
- Reload reconstructs the handler and parent/child metadata.
- `inspect()` exposes the same hierarchy and handler information.

- [ ] **Step 1: Write failing persistence tests**

Assert that registry records persist handler status/resources and child relationships, then reload and verify the same hierarchy can be inspected and executed.

- [ ] **Step 2: Run the persistence tests and verify failure**

Run: `PYTHONPATH=. pytest -q tests/test_prototype.py -k "persist or reload or inspect"`

Expected: FAIL because handler/hierarchy fields are not currently persisted.

- [ ] **Step 3: Implement persistence**

Extend the existing JSON schema with backward-compatible optional fields and reconstruct the handler during load.

- [ ] **Step 4: Run the persistence tests and verify they pass**

Run: `PYTHONPATH=. pytest -q tests/test_prototype.py -k "persist or reload or inspect"`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: persist capability handler hierarchy metadata`

---

### Task 4: Update the research demo and README

**Files:**
- Modify: `experiments/self_specialization_demo.py`
- Modify: `README.md`
- Modify: `tests/test_prototype.py`

**Interfaces:**
- Demo displays `SerializeCapability [S0]` as root.
- Demo displays sibling specialized children for integer and float multiplication.
- Demo explicitly prints handler responsibilities/resources and the complete runtime flow.
- README documents the research model, state transitions, hierarchy, handler, Ollama role, verification boundary, persistence, reload, and reuse.

- [ ] **Step 1: Write failing output-contract tests**

Add a deterministic test helper or assertions for the hierarchy representation used by the demo and the README examples.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `PYTHONPATH=. pytest -q tests/test_prototype.py -k "demo or hierarchy"`

Expected: FAIL until the new hierarchy/output contract is represented.

- [ ] **Step 3: Update the demo and README**

Replace the old `IntegerMultiplication -> child -> FloatMultiplication` public lineage with `SerializeCapability -> specialized child`. Explain that replication is an internal transformation mechanism while the general capability owns the resulting specialized children.

- [ ] **Step 4: Run the full deterministic suite**

Run: `PYTHONPATH=. pytest -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

Commit message: `docs: document complete capability handler and specialization flow`

---

### Task 5: Final verification

**Files:**
- No source changes unless verification exposes a regression.

- [ ] **Step 1: Run the complete test suite**

Run: `PYTHONPATH=. pytest -q`

Expected: zero failures.

- [ ] **Step 2: Review the resulting repository state**

Verify the README flow and demo agree with the persisted hierarchy and that no `IntegerMultiplication-child [SPECIALIZING]` appears as a final parent/child lineage.

- [ ] **Step 3: Run the demo in deterministic/fake-brain mode if available**

Confirm the displayed flow is `SerializeCapability [S0] -> IntegerMultiplication [S1]` and `SerializeCapability [S0] -> FloatMultiplication [S1]`, with the handler visible.

- [ ] **Step 4: Verify the pushed commit and CI status**

Inspect the resulting main commit and its GitHub Actions status before reporting completion.
