# SPS Self-Specialization Prototype

A minimal research prototype for capability self-specialization.

## Canonical experiment

```text
IntegerMultiplication (S0)
        |
        v
replicate
        |
IntegerMultiplication-child (S0-C)
        |
        v
Ollama + Qwen Coder
        |
        v
FloatMultiplication (GENERATED)
        |
        v
verify -> activate
        |
FloatMultiplication (S1)
```

The key research distinction is **generation != activation**. Generated source stays inactive until syntax, policy and functional checks pass.

## Layout

- `sps_specialization/capability.py` — capability contract, execution and lifecycle events.
- `sps_specialization/registry.py` — registration, active lookup and lineage.
- `sps_specialization/replication.py` — parent-to-child replication.
- `sps_specialization/specialization.py` — specialization prompt and generated capability.
- `sps_specialization/ollama_client.py` — local Ollama HTTP adapter.
- `sps_specialization/verifier.py` — AST policy and isolated functional test runner.
- `sps_specialization/evolution.py` — S0 → S0-C → S1 orchestration.
- `tests/` — deterministic tests using a fake Ollama adapter.
- `experiments/self_specialization_demo.py` — real-model experiment.
- `colab/SPS_Self_Specialization_Test.ipynb` — Google Colab runner.

## Deterministic tests

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

No Ollama installation is required for the unit tests.

## Local Ollama experiment

```bash
ollama serve
ollama pull qwen2.5-coder:7b
export OLLAMA_MODEL=qwen2.5-coder:7b
PYTHONPATH=. python experiments/self_specialization_demo.py
```

## Google Colab

Open `colab/SPS_Self_Specialization_Test.ipynb`. It installs the Python dependency, installs/starts Ollama, pulls `qwen2.5-coder:7b`, runs deterministic tests, and then runs the real-model experiment.

Colab resource availability varies. The deterministic suite is intentionally independent of Ollama.

## Research boundary

This is an experiment-grade prototype, not a secure production sandbox. It excludes UI, the full SPS ten-layer architecture, multi-agent orchestration, cloud APIs and paid credentials.
