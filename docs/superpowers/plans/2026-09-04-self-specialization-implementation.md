# Self-Specialization Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved minimal capability self-specialization experiment in `Letter/self-specialization/` and provide a reproducible Colab notebook.

**Architecture:** A small Python package separates capability state, registry/lineage, replication, Ollama generation, verification, and orchestration. The canonical lifecycle is `S0 -> S0-C -> SPECIALIZING -> GENERATED -> VERIFIED -> S1`, with failures remaining inactive.

**Tech Stack:** Python 3.10+, pytest, standard-library AST/subprocess/HTTP tooling, local Ollama with `qwen2.5-coder:7b`, Jupyter/Google Colab.

**Spec:** `docs/superpowers/specs/2026-09-04-self-specialization-design.md`

## Global Constraints

- Only the integer multiplication capability is statically programmed in the canonical experiment.
- Ollama is local and defaults to `qwen2.5-coder:7b`.
- Generated code must be verified before activation.
- Unsafe/invalid generation must become `FAILED` and never active.
- No UI, full ten-layer SPS, paid cloud APIs, or production sandbox claims.
- Deterministic unit tests must not require Ollama.

---

### Task 1: Capability and replication core

**Files:** `sps_specialization/capability.py`, `sps_specialization/replication.py`, `tests/test_prototype.py`

- [x] Write failing tests for capability execution and parent-linked replication.
- [x] Implement the dataclass/event model and replication engine.
- [x] Run the focused tests and confirm they pass.

### Task 2: Registry, specialization and Ollama adapter

**Files:** `registry.py`, `specialization.py`, `ollama_client.py`, tests

- [x] Test registry lookup/lineage and specialization prompt/response handling.
- [x] Implement deterministic interfaces plus local Ollama HTTP generation.
- [x] Run focused tests without Ollama.

### Task 3: Verification and evolution lifecycle

**Files:** `verifier.py`, `evolution.py`, tests

- [x] Test valid float generation and invalid/unsafe rejection.
- [x] Implement AST policy, subprocess functional checks, fail-closed lifecycle and activation.
- [x] Run the full deterministic suite.

### Task 4: Experiment, documentation and Colab

**Files:** `experiments/self_specialization_demo.py`, `README.md`, `requirements.txt`, `colab/SPS_Self_Specialization_Test.ipynb`

- [x] Add the canonical real-model runner.
- [x] Document local and Colab execution.
- [x] Add a notebook that installs Ollama, pulls the model, runs tests, and executes the experiment.
- [x] Verify notebook JSON and local deterministic tests.
