import ast
import subprocess
import sys
import tempfile
import textwrap

FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "shutil", "pathlib", "sys", "ctypes"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "__import__"}

class Verifier:
    def verify(self, source: str, cases: list[tuple[float, float, float]], timeout=3) -> bool:
        try:
            tree = ast.parse(source)
            functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "execute"]
            if len(functions) != 1:
                return False
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(a.name.split('.')[0] in FORBIDDEN_IMPORTS for a in node.names):
                    return False
                if isinstance(node, ast.ImportFrom) and (node.module or "").split('.')[0] in FORBIDDEN_IMPORTS:
                    return False
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    return False
            script = textwrap.dedent(f"""
{source}

for a,b,expected in {cases!r}:
    actual = execute(a,b)
    if actual != expected:
        raise SystemExit(2)
print('PASS')
""")
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                f.write(script)
                path = f.name
            result = subprocess.run([sys.executable, path], capture_output=True, text=True, timeout=timeout)
            return result.returncode == 0 and result.stdout.strip() == "PASS"
        except (SyntaxError, ValueError, OSError, subprocess.SubprocessError):
            return False
