# Real Ollama Self-Specialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the canonical S0 → S0-C → Ollama generation → verification → S1 experiment reliable, diagnosable, and directly executable from the user's original float request.

**Architecture:** Keep the existing capability/registry/replication/specialization/verifier/evolution/dispatcher separation. Strengthen the boundaries so Ollama output is normalized and verified as the actual generated source, failures preserve actionable diagnostics, and the dispatcher reuses the activated S1 capability without another AI call.

**Tech Stack:** Python 3.11+, pytest, local Ollama HTTP API, Qwen Coder model.

**Spec:** `README.md` canonical experiment and thesis boundary.

## Global Constraints

- State 0 remains statically programmed and executable.
- Replication creates an independent `S0-C` child with parent lineage.
- Generated source remains non-active until verification passes.
- The verifier must execute the actual generated source.
- Unsafe generated imports/calls remain rejected.
- Ollama is used for the real experiment; deterministic fake Ollama remains for unit tests.

---

- [ ] Add regression coverage for real Ollama failure diagnostics and malformed responses.
- [ ] Improve specialization error handling and normalization without bypassing verification.
- [ ] Improve evolution failure records so the failing stage/reason is visible and the failed generated capability is retained when available.
- [ ] Ensure dispatcher diagnostics expose specialization failure reason instead of only state.
- [ ] Update the real experiment output to show generation, verification, activation, lineage, and reuse clearly.
- [ ] Run the complete deterministic pytest suite and the real-model experiment where Ollama is available.
- [ ] Commit and push the verified implementation to `main`.
