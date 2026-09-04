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
- `sps_specialization/ollama_client.py` — local Ollama HTTP adapter with actionable connection/model errors.
- `sps_specialization/verifier.py` — AST policy and isolated functional test runner.
- `sps_specialization/evolution.py` — S0 → S0-C → S1 orchestration and failure diagnostics.
- `sps_specialization/dispatcher.py` — typed request dispatch and specialization triggering.
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

If Ollama is unavailable, the experiment now reports the connection/model failure instead of only returning `Specialization failed: FAILED`.

## Google Colab

Start from a fresh clone so an older `/content/self-specialization` or `/content/Letter/self-specialization` copy cannot shadow the current code:

```python
%cd /content
!rm -rf self-specialization
!git clone --branch main --single-branch https://github.com/muhammadnaumantahir/self-specialization.git
%cd /content/self-specialization
!git rev-parse HEAD
!pip install -q -r requirements.txt
!PYTHONPATH=. pytest -q
```

Then install/start Ollama, pull `qwen2.5-coder:7b`, and run:

```python
%cd /content/self-specialization
!nohup ollama serve >/tmp/ollama.log 2>&1 &
!sleep 5
!ollama pull qwen2.5-coder:7b
!PYTHONPATH=. python experiments/self_specialization_demo.py
```

The deterministic suite is intentionally independent of Ollama. Colab resource availability varies.

## Research boundary

This is an experiment-grade prototype, not a secure production sandbox. It excludes UI, the full SPS ten-layer architecture, multi-agent orchestration, cloud APIs and paid credentials.
