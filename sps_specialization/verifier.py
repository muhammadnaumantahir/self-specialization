import ast
import subprocess
import sys
import tempfile
import textwrap

FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "shutil", "pathlib", "sys", "ctypes"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__"}


class Verifier:
    def __init__(self):
        self.last_error = None

    def verify_detailed(self, source: str, cases: list[tuple[float, float, float]], timeout=3) -> tuple[bool, str]:
        """Verify generated code and return an actionable failure reason."""
        self.last_error = None
        path = None
        try:
            tree = ast.parse(source)
            functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "execute"]
            if len(functions) != 1:
                return self._fail("source must define exactly one execute() function")

            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(a.name.split('.')[0] in FORBIDDEN_IMPORTS for a in node.names):
                    return self._fail("forbidden import")
                if isinstance(node, ast.ImportFrom) and (node.module or "").split('.')[0] in FORBIDDEN_IMPORTS:
                    return self._fail("forbidden import")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    return self._fail(f"forbidden call: {node.func.id}")

            script = textwrap.dedent(f"""
{source}

for a,b,expected in {cases!r}:
    try:
        actual = execute(a,b)
    except Exception as exc:
        print(f"EXECUTION_ERROR: {{type(exc).__name__}}: {{exc}}")
        raise SystemExit(3)
    if actual != expected:
        print(f"WRONG_RESULT: inputs=({{a!r}}, {{b!r}}) expected={{expected!r}} actual={{actual!r}}")
        raise SystemExit(2)
print('PASS')
""")
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                f.write(script)
                path = f.name

            result = subprocess.run(
                [sys.executable, path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0 and result.stdout.strip() == "PASS":
                return True, "PASS"

            detail = (result.stdout.strip() or result.stderr.strip() or f"process exited with code {result.returncode}")
            return self._fail(detail)
        except SyntaxError as exc:
            return self._fail(f"syntax error: {exc}")
        except subprocess.TimeoutExpired:
            return self._fail(f"verification timed out after {timeout}s")
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            return self._fail(f"verification error: {type(exc).__name__}: {exc}")
        finally:
            if path:
                try:
                    import os
                    os.unlink(path)
                except OSError:
                    pass

    def _fail(self, reason: str) -> tuple[bool, str]:
        self.last_error = reason
        return False, reason

    def verify(self, source: str, cases: list[tuple[float, float, float]], timeout=3) -> bool:
        """Backward-compatible boolean verification API."""
        ok, _ = self.verify_detailed(source, cases, timeout=timeout)
        return ok
