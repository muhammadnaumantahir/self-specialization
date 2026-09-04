# Runtime Capability Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent, inspectable capability registry and update the self-specialization experiment/Colab so runtime-created capabilities become visible research artifacts.

**Architecture:** Extend the existing registry rather than replacing it. Runtime capabilities remain `Capability` objects; persistence writes canonical JSON metadata plus exact Python source files, and loading reconstructs executable capabilities. The experiment uses a clean demo storage directory while demonstrating that S1 can be inspected and reused.

**Tech Stack:** Python 3, dataclasses, JSON, pathlib, pytest, GitHub, Google Colab, Ollama/Qwen.

**Spec:** `docs/superpowers/specs/2026-09-04-capability-registry.md`

## Global Constraints

- Preserve existing registry/evolution/dispatcher APIs and behavior.
- `list_active()` means active `S1` capabilities.
- `get()` and `inspect()` accept either exact capability ID or unique capability name.
- Persist metadata as JSON and source as `.py`.
- Generated source remains research-only/untrusted code.
- Colab must install Ollama before cloning the repository and use the requested startup order.
- Run the complete pytest suite before claiming completion.

---

### Task 1: Add registry behavior tests

**Files:**
- Modify: `tests/test_prototype.py`

**Interfaces:**
- Tests establish `CapabilityRegistry(storage_dir=...)`, `list_active()`, `get()`, `inspect()`, `save()`, and `load()` behavior.

- [ ] **Step 1: Write failing tests** for persistent registration, active listing, ID/name lookup, inspection metadata, source persistence, and reload/reuse.
- [ ] **Step 2: Run the targeted tests** and confirm they fail for missing APIs/behavior.

### Task 2: Implement persistent registry

**Files:**
- Modify: `sps_specialization/registry.py`
- Modify: `sps_specialization/capability.py` only if serialization helpers are needed

**Interfaces:**
- `CapabilityRegistry(storage_dir=None)`
- `register(capability)`
- `get(capability_id_or_name)`
- `list_active()`
- `inspect(capability_id_or_name)`
- `save()` / `load()`

- [ ] **Step 1:** Implement minimal JSON/source persistence to satisfy Task 1.
- [ ] **Step 2:** Run registry tests and confirm green.
- [ ] **Step 3:** Refactor only where needed while preserving old APIs.
- [ ] **Step 4:** Run the full test suite.

### Task 3: Upgrade the research demo

**Files:**
- Modify: `experiments/self_specialization_demo.py`

**Interfaces:**
- Use persistent registry storage for the demonstration.
- Print `CAPABILITY CREATED AT RUNTIME` with ID, Name, State, Parent, Created, Location, Storage, Source.
- Demonstrate `registry.inspect("FloatMultiplication")` and `registry.list_active()`.
- Demonstrate loading/retrieving the generated S1 artifact and reusing it.

- [ ] **Step 1:** Add clean demo storage initialization.
- [ ] **Step 2:** Add rich creation/inspection output.
- [ ] **Step 3:** Add persisted artifact and reload evidence.
- [ ] **Step 4:** Run deterministic tests and the demo with a fake/local model where practical.

### Task 4: Update the Colab notebook

**Files:**
- Modify: `colab/SPS_Self_Specialization_Test.ipynb`

- [ ] **Step 1:** Reduce cells to a clean install/startup/test/demo flow.
- [ ] **Step 2:** Use the requested Ollama installation order exactly.
- [ ] **Step 3:** Explain where JSON and `.py` capability artifacts are created.
- [ ] **Step 4:** Add a final registry inspection/evidence section.

### Task 5: Verify and document

**Files:**
- Modify: `README.md` if required by the existing documentation structure.

- [ ] **Step 1:** Run the complete test suite.
- [ ] **Step 2:** Run the research demo and inspect generated artifacts.
- [ ] **Step 3:** Re-fetch changed files from GitHub and verify the committed content.
- [ ] **Step 4:** Compare the final commit against its parent and report exact verification evidence.
