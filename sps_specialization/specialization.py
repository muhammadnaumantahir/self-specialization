import ast
import re

from .capability import Capability


class SpecializationEngine:
    def __init__(self, ollama):
        self.ollama = ollama

    @staticmethod
    def _normalize_source(source: str) -> str:
        """Extract and validate the execute function from an Ollama response."""
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Ollama returned empty source")

        text = source.strip()
        blocks = re.findall(
            r"```(?:python|py)?\s*\n?(.*?)```",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        candidates = [block.strip() for block in blocks if block.strip()]
        candidates.append(text)

        for match in re.finditer(r"(?m)^\s*def\s+execute\s*\(", text):
            candidates.append(text[match.start():].strip())

        last_error = None
        for candidate in candidates:
            try:
                tree = ast.parse(candidate)
            except SyntaxError as exc:
                last_error = exc
                continue

            functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            execute_functions = [node for node in functions if node.name == "execute"]
            if len(execute_functions) != 1:
                continue

            node = execute_functions[0]
            lines = candidate.splitlines()
            end = getattr(node, "end_lineno", len(lines))
            normalized = "\n".join(lines[:end]).strip() + "\n"
            try:
                ast.parse(normalized)
            except SyntaxError as exc:
                last_error = exc
                continue
            return normalized

        if last_error:
            raise ValueError(f"Ollama generated invalid Python: {last_error}") from last_error
        raise ValueError("Ollama response does not contain exactly one execute() function")

    def specialize(self, child: Capability, target_name: str, input_types, output_type, final_parent_id=None) -> Capability:
        """Transform an S0-C runtime copy into a generated specialization."""
        if child.state != "S0-C":
            raise ValueError(f"specialization requires S0-C child, got {child.state}")
        child.record("SPECIALIZE", f"target={target_name}")
        prompt = f"""You are specializing an existing capability, not inventing an unrelated function.
Parent capability: {child.name}
Parent contract: inputs={child.input_types}, output={child.output_type}
Parent source:
{child.source_code}
Target specialization: {target_name}
Target contract: inputs={input_types}, output={output_type}
Return ONLY valid Python source. Do not use Markdown fences or explanatory text. Define exactly one function: execute(a, b)."""
        source = self._normalize_source(self.ollama.generate(prompt))
        specialized = Capability.create(
            target_name,
            child.version,
            "GENERATED",
            list(input_types),
            output_type,
            source,
            final_parent_id if final_parent_id is not None else child.id,
        )
        specialized.events = child.events.copy()
        specialized.record("GENERATED", target_name)
        return specialized
