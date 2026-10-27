#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.10,<2", "pyyaml"]
# ///
"""Write docs-src/tools.md from the tools' own docstrings and signatures: a paragraph and an argument table each."""
import html
import inspect
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import KnowledgeBaseMCP as k


def prose(doc: str) -> str:
    """The docstring as one paragraph; <...> escaped outside `code` so Markdown keeps it."""
    parts = " ".join(inspect.cleandoc(doc or "").split()).split("`")
    return "`".join(html.escape(p, quote=False) if i % 2 == 0 else p for i, p in enumerate(parts))


out = ["# Tools", "", ("Every tool, from its own docstring. Run one as `uv run KnowledgeBaseMCP.py <tool> "
                       "name=value ...`, or see the same text with `help <tool>`."), ""]
for name, fn in sorted(k.REG.items()):
    out += [f"## {name}", "", prose(fn.__doc__), ""]
    if name in k.EXAMPLES:
        out += ["```sh", *(f"uv run KnowledgeBaseMCP.py {e}" for e in k.EXAMPLES[name]), "```", ""]
    args = [(n, p) for n, p in inspect.signature(fn).parameters.items() if n != "ctx"]
    if args:
        out += ["| Argument | Type | Default |", "|---|---|---|"]
        for n, p in args:
            ann = (getattr(p.annotation, "__name__", None) or str(p.annotation)).replace("typing.", "").replace(" | ", " or ")
            out.append(f"| `{n}` | `{ann}` | " + ("required" if p.default is p.empty else f"`{p.default!r}`") + " |")
        out.append("")
(HERE / "docs-src/tools.md").write_text("\n".join(out))
