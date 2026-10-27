# 00 — Context

Baseline context for KnowledgeBaseMCP. The brief (`rewrite-brief.md`) builds
on this.

## What it is

An MCP server (stdio) and CLI for [Open Knowledge Format][okf] (OKF) v0.2
bundles. It checks, maintains and imports concepts: how they are written,
never what they say. Local files only. No network. Never writes to git.

Design rule: everything a tool does is also doable by hand. The tools make the
work cheaper and more consistent, not possible.

## Shape

- A single [PEP 723][pep723] script (`KnowledgeBaseMCP.py`) with inline deps
  (`mcp`, `pyyaml`). Runs as an stdio MCP server, or as a CLI for any tool.
- The knowledgebase is `KB_ROOT` (default: found from the current directory):
  one bundle, or sibling bundles (no nesting) listed by a root `index.md`. An
  `index.md` declaring `okf_version` marks a bundle root. Files are named the OKF
  way (§2): `bundle=` plus the path within it, in every input and output.
  Without `bundle=`, tools follow the working directory; the CLI reads paths
  from where you are.
- A self-check (`test_KnowledgeBaseMCP.py`) runs every tool against throwaway
  bundles, including SPEC.md's own examples.

## Tools

Read: `lint`, `status`, `list`, `links`, `search`, `get`, `recheck_plan`, `heatmap`, `web`, `log`,
`bundles`; the spec as resource `okf://spec`.
Write: `init`, `create`, `set`, `move`, `migrate`, `split`, `rename`, `archive`,
`unarchive`, `record`, `fix`, `index`,
`verify`, `cite`, `recheck_apply`, `provenance`, `upgrade`, `ingest`, `baseline`.

## Constraints

- Apache-2.0. Personal project under the [ASF generative-tooling
  guidelines][asf-gt].
- CI is GitHub Actions or pre-commit, lint only (README).
- `SPEC.md` (OKF v0.2) is normative; `lint` enforces it.

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
[asf-gt]: https://www.apache.org/legal/generative-tooling.html
[pep723]: https://peps.python.org/pep-0723/
