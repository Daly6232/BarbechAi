#!/usr/bin/env python3
"""
Verifies that every `from app.X.Y import a, b, c` statement in the backend
actually finds a, b, c as real top-level names in app/X/Y.py.

This exists because of a real incident: an edit silently dropped a function
from crm_pipeline.py while leaving the file syntactically valid (the
function's body became dead code trailing inside a different function).
`python -m py_compile` doesn't catch that — it only checks syntax. This
script catches it by actually resolving every cross-module import target.

Usage: python3 backend/scripts/check_imports.py
Exit code 0 = all good, 1 = at least one broken import found.
"""
import ast
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent / "app"


def module_name_for(path: Path) -> str:
    rel = path.relative_to(APP_ROOT.parent).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def top_level_names(path: Path) -> set:
    names = set()
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return names  # a separate syntax check already covers this case
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.ImportFrom) or isinstance(node, ast.Import):
            # Re-exported names count too.
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def main():
    py_files = list(APP_ROOT.rglob("*.py"))
    module_map = {module_name_for(p): p for p in py_files}
    names_cache = {mod: top_level_names(p) for mod, p in module_map.items()}

    errors = []
    for path in py_files:
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError as e:
            errors.append(f"{path}: SYNTAX ERROR: {e}")
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if not node.module.startswith("app."):
                continue
            target_names = names_cache.get(node.module)
            if target_names is None:
                continue  # external/unresolvable module path, skip
            for alias in node.names:
                if alias.name == "*":
                    continue
                if alias.name not in target_names:
                    errors.append(
                        f"{path}: imports '{alias.name}' from '{node.module}', "
                        f"but that name doesn't exist there (line {node.lineno})"
                    )

    if errors:
        print("Broken imports found:\n")
        for e in errors:
            print(" -", e)
        print(f"\n{len(errors)} broken import(s). This is exactly the bug class "
              "that broke production in July 2026 — fix these before committing.")
        return 1

    print(f"OK — checked {len(py_files)} files, all cross-module imports resolve correctly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
