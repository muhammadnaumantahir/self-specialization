# Runtime Capability Registry & Persistence — Design Spec

**Goal:** Make runtime-created SPS capabilities inspectable and persistable as first-class artifacts while preserving the existing State 0 → replication → specialization → verification → State 1 flow.

## Design

The existing in-memory `CapabilityRegistry` becomes a persistent registry with an optional storage directory. Each capability remains a Python `Capability` object at runtime, while the registry persists human-readable JSON metadata and the capability source as a `.py` file. The JSON is the canonical metadata record; the source file is the executable/research artifact.

### Registry API

- `CapabilityRegistry(storage_dir=None)` — in-memory by default; when supplied, creates a persistent registry.
- `register(capability)` — registers and persists a capability.
- `get(capability_id_or_name)` — retrieve by exact ID or unique name.
- `list_active()` — return active `S1` capabilities in deterministic order.
- `inspect(capability_id_or_name)` — return a structured, thesis-friendly dictionary containing identity, state, lineage, storage, source, verification, and events.
- `save()` — persist the complete registry.
- `load()` — reload persisted capabilities into runtime objects.
- Existing `active`, `all`, `find`, and `lineage` APIs remain compatible.

### Storage layout

```text
capabilities/
├── registry.json
├── records/
│   └── <capability-id>.json
└── sources/
    └── <capability-id>_<safe-name>.py
```

`registry.json` provides an index and schema version. Individual JSON records make each capability independently inspectable. Source files contain the exact generated Python source.

### Lifecycle

1. S0 exists before the new request.
2. A missing contract triggers replication to S0-C.
3. Ollama generates specialized source.
4. Verification succeeds or fails.
5. Successful specialization becomes S1 and is registered.
6. Registration writes JSON + `.py` source.
7. A later request resolves the existing S1 capability without regeneration.
8. A new registry instance can load the persisted S1 and reuse it.

### Safety boundary

Generated source is arbitrary code and the prototype already executes source during verification/runtime. This persistence feature does not claim production-grade sandboxing. It is explicitly a research prototype; persisted generated code must be treated as untrusted.

### Demonstration output

The demo will print a rich `CAPABILITY CREATED AT RUNTIME` block containing ID, Name, State, Parent, Created, Location, Storage, and Source, followed by registry inspection and reuse evidence.
