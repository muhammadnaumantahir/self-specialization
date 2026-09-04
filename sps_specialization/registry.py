import json
import re
from pathlib import Path


class CapabilityRegistry:
    """Runtime capability registry with optional human-readable persistence."""

    SCHEMA_VERSION = 1

    def __init__(self, storage_dir=None):
        self._caps = {}
        self.storage_dir = Path(storage_dir) if storage_dir is not None else None
        self.records_dir = self.storage_dir / "records" if self.storage_dir else None
        self.sources_dir = self.storage_dir / "sources" if self.storage_dir else None
        if self.storage_dir:
            self._ensure_storage()
            self.load()

    def _ensure_storage(self):
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.sources_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(name):
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._") or "capability"

    def _paths(self, capability):
        record = self.records_dir / f"{capability.id}.json"
        source = self.sources_dir / f"{capability.id}_{self._safe_name(capability.name)}.py"
        return record, source

    @staticmethod
    def _event_to_dict(event):
        return {
            "event": event.event,
            "detail": event.detail,
            "timestamp": event.timestamp,
        }

    def _record_for(self, capability):
        record_path, source_path = self._paths(capability)
        return {
            "schema_version": self.SCHEMA_VERSION,
            "id": capability.id,
            "name": capability.name,
            "version": capability.version,
            "state": capability.state,
            "input_types": list(capability.input_types),
            "output_type": capability.output_type,
            "parent_id": capability.parent_id,
            "created_at": capability.created_at,
            "activated_at": capability.activated_at,
            "status": "active" if capability.state == "S1" else capability.state.lower(),
            "source_path": str(source_path),
            "record_path": str(record_path),
            "source_code": capability.source_code,
            "events": [self._event_to_dict(event) for event in capability.events],
        }

    def register(self, capability):
        self._caps[capability.id] = capability
        if self.storage_dir:
            self._persist_capability(capability)
            self.save()
        return capability

    def _persist_capability(self, capability):
        self._ensure_storage()
        record_path, source_path = self._paths(capability)
        source_path.write_text(capability.source_code, encoding="utf-8")
        record_path.write_text(
            json.dumps(self._record_for(capability), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def save(self):
        if not self.storage_dir:
            return None
        self._ensure_storage()
        index = {
            "schema_version": self.SCHEMA_VERSION,
            "capabilities": [
                {
                    "id": capability.id,
                    "name": capability.name,
                    "state": capability.state,
                    "record_path": str(self._paths(capability)[0]),
                    "source_path": str(self._paths(capability)[1]),
                }
                for capability in sorted(self._caps.values(), key=lambda item: (item.created_at, item.id))
            ],
        }
        registry_path = self.storage_dir / "registry.json"
        registry_path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
        return registry_path

    def load(self):
        if not self.storage_dir:
            return self
        registry_path = self.storage_dir / "registry.json"
        if not registry_path.exists():
            return self

        from .capability import Capability, Event

        index = json.loads(registry_path.read_text(encoding="utf-8"))
        self._caps.clear()
        for item in index.get("capabilities", []):
            record_path = Path(item["record_path"])
            if not record_path.is_absolute():
                record_path = self.storage_dir / record_path
            if not record_path.exists():
                continue
            data = json.loads(record_path.read_text(encoding="utf-8"))
            capability = Capability(
                id=data["id"],
                name=data["name"],
                version=data["version"],
                state=data["state"],
                input_types=list(data["input_types"]),
                output_type=data["output_type"],
                source_code=data["source_code"],
                parent_id=data.get("parent_id"),
                created_at=data["created_at"],
                activated_at=data.get("activated_at"),
                events=[Event(e["event"], e.get("detail", ""), e["timestamp"]) for e in data.get("events", [])],
            )
            capability._load_handler()
            self._caps[capability.id] = capability
        return self

    def get(self, capability_id_or_name):
        """Retrieve a capability by exact ID or unique name."""
        capability = self._caps.get(capability_id_or_name)
        if capability is not None:
            return capability
        matches = [c for c in self._caps.values() if c.name == capability_id_or_name]
        if not matches:
            raise KeyError(capability_id_or_name)
        if len(matches) > 1:
            raise KeyError(f"Capability name is not unique: {capability_id_or_name}")
        return matches[0]

    def active(self, capability_id):
        cap = self._caps.get(capability_id)
        return cap if cap and cap.state == "S1" else None

    def list_active(self):
        return [
            capability
            for capability in sorted(self._caps.values(), key=lambda item: (item.created_at, item.id))
            if capability.state == "S1"
        ]

    def all(self):
        return list(self._caps.values())

    def find(self, name, input_types=None, active_only=False):
        """Find the newest capability matching a name and optional type contract."""
        candidates = [c for c in self._caps.values() if c.name == name]
        if input_types is not None:
            candidates = [c for c in candidates if c.input_types == list(input_types)]
        if active_only:
            candidates = [c for c in candidates if c.state == "S1"]
        return candidates[-1] if candidates else None

    def lineage(self, capability_id):
        result = []
        current = self.get(capability_id)
        while current:
            result.append(current)
            current = self._caps.get(current.parent_id) if current.parent_id else None
        return list(reversed(result))

    def inspect(self, capability_id_or_name):
        """Return a structured inspection record suitable for research output/UI."""
        capability = self.get(capability_id_or_name)
        if self.storage_dir:
            record_path, source_path = self._paths(capability)
            storage = {
                "registry": str(self.storage_dir / "registry.json"),
                "record": str(record_path),
                "source": str(source_path),
            }
        else:
            storage = {
                "registry": None,
                "record": None,
                "source": None,
            }
        return {
            "id": capability.id,
            "name": capability.name,
            "version": capability.version,
            "state": capability.state,
            "parent_id": capability.parent_id,
            "created_at": capability.created_at,
            "activated_at": capability.activated_at,
            "input_types": list(capability.input_types),
            "output_type": capability.output_type,
            "source_code": capability.source_code,
            "storage": storage,
            "events": [self._event_to_dict(event) for event in capability.events],
        }
