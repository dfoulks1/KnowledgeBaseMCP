---
type: Brief
title: KnowledgeBaseMCP rewrite brief
status: draft
---

# KnowledgeBaseMCP rewrite brief

AI-generated. Reviewed by the agent against the code; awaiting human sign-off.

## Goal

Rewrite `KnowledgeBaseMCP.py` as a generic, content-agnostic tool for OKF v0.2
bundles. `SPEC.md` in this repo is the normative reference (upstream
GoogleCloudPlatform/knowledge-catalog, `okf/SPEC.md`, commit `bad9bdb`,
Apache-2.0). The tool controls how concepts are written, checked and
maintained, never what they say.

One contract, three users: an agent over MCP (primary), CI (GitHub Actions,
pre-commit), and a developer at a terminal with no AI.

## Constraints

- One PEP 723 script. Dependencies: `mcp>=1.10,<2`, `pyyaml`.
- Local files only. No network. No git writes. Git read-only (`log`,
  `ls-files`, `status`, `remote get-url`, `rev-parse`).
- Bundle content is untrusted: `yaml.safe_load`, no code execution, no
  following symlinks out of the bundle.
- Server mode never writes to stdout except the protocol.
- Frontmatter edits are text-level: only the edited key is re-serialized, so
  every other key survives byte for byte (§4.1).
- Frontmatter parsing is strict everywhere (no lenient fallback). CRLF and BOM
  survive a write. A closing `---` at end of file parses.
- Writes that touch many files take `apply=False` by default and return the
  plan plus a unified diff. Writes are atomic (temp file, rename).
- Deterministic: sorted, stable output; `fix`, `index` and `ingest` are
  idempotent.
- Every tool: docstring is the agent's manual (when to call it, what it
  returns). Errors carry a `| fix: <what to do>` hint.
- Names are bare (`lint`, `verify`, ...). Hand-use is secondary but documented.

## Bundle model

- `bundle=` argument on every tool. Default: `KB_ROOT`. Read tools accept any
  directory. Write tools must resolve inside `KB_ROOT`.
- One scan per call builds a model `{path: (text, frontmatter)}` that every
  check reads. No per-check re-reads.
- Concept = any `.md` except reserved `index.md` / `log.md` (§3.1), outside
  `.git`. Concept ID = path without `.md` (§2). Non-UTF-8 files are reported,
  never crash a run.
- No layout assumptions: no buckets, topics, catalogs or project tables. A
  bundle with only concepts must lint without error.

## Output contract

- Tools return JSON-serializable dict/list. CLI prints JSON.
- Exit codes: 0 ok, 1 findings, 2 usage.
- Paging: `limit`, `offset` on `lint`, `list`, `search`, `get`; a `total`
  alongside.
- `schema: 1` field in `lint` output.
- CLI `format=text|json|github|sarif` for `lint` (`github` emits
  `::error file=...::msg`).
- Tool annotations on every tool (`ToolAnnotations`: readOnlyHint,
  destructiveHint, idempotentHint, openWorldHint=false). Reads read-only;
  `fix`, `index`, `set` non-destructive + idempotent; `ingest` and `move`
  destructive (they can delete a renamed original); `verify`, `cite`,
  `create`, `log` non-destructive, not idempotent.
- Server `instructions` string: the workflow (lint, fix, verify, cite), what
  needs a human, what never to do (claim `human:`).
- CLI parses arguments from the function signature (not `str(annotation)`).

## Tools

### lint (rewrite)

```
{"schema": 1, "ok": bool, "conformant": bool, "counts": {kind: n},
 "findings": [{"kind","scope":"okf|house","severity":"error|warning",
               "file","message","fix","fixable"}]}
```

- `lint(scope="all", limit=100, offset=0, baseline="", since="")`. `scope`
  filters findings and the exit code; `since=<ref>` keeps files changed since
  the ref's merge base.
- `conformant` = §11 only: parseable frontmatter, non-empty `type`, reserved
  files well-formed. `ok` = no error findings in scope.
- `fixable` = `fix` will clear it.

Checks (okf, error): no_frontmatter, bad_yaml, no_type, non_utf8 (§4),
okf_index (§8), okf_log (§9: date headings, newest first), okf_trust (§5.2/§7;
timestamps need an explicit UTC offset, §5), bad_status (§5.4),
bad_stale_after (§5.5), bad_source (§5.1: `resource` required, ids unique),
bad_computation (§10: `runtime`, `parameters`, a computation). Warnings:
okf_version other than `"0.2"` (§12), a `[^label]` with no matching
`sources[].id` when the concept has `sources`, no `description` (§4.1).

Checks (house): dead_link (relative and `/` links; `/` resolves from the bundle
root, §6.1), index_stale (only when the root index carries the generated
block, root or directory), via_server (see `cite`). Warnings: case-colliding
filenames, odd filename characters, orphans, dead #anchors, tags differing
only by case.

Removed: bad_tag, missing_backlink, dead_related_file, unknown_topic,
unindexed_reference, index_drift.

### baseline

`baseline(path=".okf-baseline.json", apply=False)` snapshots current findings
(fingerprint: kind + file + message). `lint(baseline=path)` counts only new
findings toward `ok` and the exit code.

### verify (rewrite)

`verify(file, by="")`. Records a §5.2 `verified` entry `{by, at}`; `at` is UTC
with offset. Existing entries keep their values; a bare mapping becomes a list.

- Machine path (over MCP): `by` is a non-`human:` actor; recorded as given.
  A `human:` actor over MCP is refused.
- Human path: no `by`. The server calls `ctx.elicit` with path, title, excerpt,
  body length; the human confirms and types their own id (default from
  `KB_USER`). On accept, write `human:<id>`. Re-read the file first and refuse
  if the body changed. If the client lacks elicitation, refuse with a `fix:`
  hint. CLI: `by=human:<id>` writes directly.

### cite, recheck_plan, recheck_apply (replace the kb-verify machinery)

A fact fetched through an MCP tool is recorded as a `sources[]` entry:

```yaml
sources:
  - id: infra-123
    resource: <real URL if the tool result has one, else mcp://server/tool?args>
    title: ...
    via: {server: jira, tool: get_issue, args: {issue_key: INFRA-123}}
    observed: In Progress
    rev: <optional version/sha>
    retrieved_at: 2026-10-27T11:20:00Z
    by: <caller's actor>
```

- `cite(file, resource, id="", title="", server="", tool="", args=None,
  observed="", rev="", by, stale_days=0)`. Writes the entry (`server` empty =
  plain source), returns the `[^id]` marker for the claim, optionally sets
  `stale_after`.
- `recheck_plan(older_than_days=0)`: for each stale source with `via`, emits
  the call to replay. Executes nothing.
- `recheck_apply(results)`: compare `observed`. Match: bump `retrieved_at` and
  `stale_after`. Drift: update the entry, list every line carrying that
  footnote for review.
- If the bundle has `.mcp.json` (also `servers` key for VS Code style), read
  server names only, never values (`env`, `headers`). `lint` flags a `via.server`
  not listed (`via_server`, house). No file, no check.
- Recorded `via` is self-reported, not proof. Say so in the docs.

### Other tools

| Tool | Behavior |
|---|---|
| `status` | counts by type; by `status` (absent = stable); by trust tier (§5.3); stale count (`stale_after`); `okf_version`; `conformant`; lint counts |
| `list` | filter by `type`, `tag`, `status`, `tier`, `stale`; paged; returns concept IDs |
| `links` | out/in edges for a concept, broken ones marked; inbound computed at read time |
| `set` | `set(file or files, fields, apply=False)`: bulk frontmatter edit, text-level, validates `status`, `stale_after`, `type`, `tags`; refuses `generated`/`verified`/`sources` (dedicated tools) |
| `init` | `init(apply=False)`: root `index.md` with `okf_version: "0.2"`, `log.md`; refuses if `index.md` exists |
| `fix` | mechanical fixes (generated index lists, `okf_index`); `apply=True` re-lints, returns what remains; exit 1 if findings remain, or if a dry run has pending work |
| `index` | generated lists from frontmatter (`description`); `dirs=true` gives every directory a §8 index |
| `search`, `get` | as today, without buckets; paged; confined to the bundle |
| `provenance` | stays for notes already in a bundle; uses the shared history reader |

### History reader (shared)

One `git log` pass, not per-file spawns. Body-change detection (frontmatter-only
edits and renames do not count) compares blobs through one long-lived
`git cat-file --batch` process. Uses `%aE` and mailmap. Actor rules: AI trailer
(`Co-Authored-By`, `Generated-by`, against an editable list of known producers)
wins; `[bot]` authors become `process:<name>`; GitHub noreply login or ASF id
otherwise; else the raw email (convention, not content). Refuse on a shallow
clone, with `fetch-depth: 0` as the fix. No git, no provenance (never file
mtime).

### ingest

`ingest(source, bundle="", rules=None, status="draft", stale_days=0,
apply=False, limit=50, offset=0)`.

- `source` is a local directory or clone. Enumerate with `git ls-files` when it
  is a repo. In-place adoption (`bundle` = `source`) requires a clean git tree.
- Markdown only. Skip and report: non-`.md`, non-UTF-8, LFS pointers, symlinks
  leaving the tree, files over a size limit.
- `rules`: `{glob: type}`; default type is a generic one. `title` from the H1 or
  filename. Existing frontmatter keys kept.
- Reserved names: a source `index.md` / `log.md` is renamed `<parent>-index.md`
  / `<parent>-log.md`, reported in the plan.
- Provenance per file (reported as coverage: full / partial / none):

| Source | Lands in |
|---|---|
| remote URL + commit | `sources[].resource` (permalink) |
| last commit touching the file | `sources[].last_modified` |
| last body-changing commit | `generated: {by, at, basis: git-history}` |
| source frontmatter canonical URL | an extra `sources` entry; original keys kept |

- No `verified`. Trust tier is unaffected by inferred provenance.
- Idempotent: a file whose destination exists, or that already has `type`, is
  skipped, never overwritten. Sync is out of scope.
- Plan output states: license file found (no SPDX guess), "not checked";
  unresolved `/` links; recommends a secret scanner (for example gitleaks), does
  not scan; links that will break after ingest (renamed or not brought).

## Hot files

Write tools keep refreshing `log.md` (a §9 entry) and the root index block,
each only when the file exists. Merge conflicts on these in a busy repo are a
documented, deferred limit.

## Removed

`new` (rebuilt generically on its own track), `citations`, `verify_plan`,
`apply_checks`, `record_check`, `check_stale`, `call_for`, `catalog`,
`reindex`, `edit_row`, `related`, `backlinks`, `known_topics`, `overview`,
`project_dir`, `catalog_row`, `add_catalog_row`, `append_related`, `notes`,
`BUCKETS`, `SLUG`, `TAG`, `KV`, `TOOLS`, `REVFIELDS`, `DUE`, `OKF_SPEC`, the
lenient `fm()` fallback, the duplicate `docs()` / `okf_docs()`. All references
to any outside server or workflow in code, docstrings and docs.

## Tests

Extend `test_KnowledgeBaseMCP.py` (temp bundle, asserts, `uv run`):

- SPEC.md §4.3, §4.4 and Appendix A (v0.2 form) as fixtures: `conformant` and
  no okf errors. Bad fixture per check.
- A bundle with only concepts lints without crashing.
- `fix`, `index`, `ingest` are idempotent (second run does nothing).
- Every write tool preserves unknown frontmatter keys.
- A `/` dead link is found; a non-UTF-8 file is reported, not fatal.
- `verify` human path refused over MCP; machine path writes an offset
  timestamp.
- Elicitation is tested live by hand after the rewrite.

## Docs

README: register the server and restart after edits; "Before you push"
(`lint`, `fix`, `lint` again; exit codes); a GitHub Actions workflow
(`fetch-depth: 0`, `lint scope=okf`, no auto-push on PRs; fork PRs are
read-only); pre-commit hook runs `lint` only; known limits (hot files, actors
may contain emails, `via` is self-reported). Source note for `SPEC.md` (URL,
commit, Apache-2.0). `CONTRIBUTING.md` keeps the ASF generative-tooling policy,
drops the numbered-prompt system (one brief, then refinement) and the old Kiro
trailer. `prompts/00-context.md` gets the current tool list; its resolved open
questions go.

## Build order

1. Scan model, bundle param, generic `lint` core.
2. Remaining lint checks, `conformant`, scope, paging, baseline.
3. `verify` (machine, human, elicitation).
4. `status`, `list`, `links`, `init`, `fix`, `index`, `set`.
5. History reader, `provenance`.
6. `cite`, `recheck_plan`, `recheck_apply`, `.mcp.json` names.
7. `ingest`.
8. Annotations, instructions, CLI formats, signature parsing.
9. Removals, tests green, README.

Each step leaves the self-check passing.

## Later

Built since the first pass: `create` (the generic `new`), `move`, `log`,
`migrate`, per-directory `index`, `bundles`, the spec resource, and lint
warnings for orphans, anchors, tag case, missing `description` and the §10
contract (an error). Still later: `action.yml`, `.pre-commit-hooks.yaml`,
ingest sync. `lint since=<ref>` is built.

A knowledgebase is a workspace of bundles (wherever the user points). Nested
bundle roots (`index.md` with `okf_version`) are boundaries. Built: `split`,
`ingest keep_okf`, `lint all` / file paths / working-directory context,
`verify promote`, `get files`, and warnings `cross_bundle`, `deprecated_link`,
`source_changed`; `fix` normalizes tag case.

## Defaults chosen without asking

- Untrusted note content is returned as is, not fenced.
- Ingest renames reserved names rather than stripping them.
- Warnings do not fail a run.

## Commit hygiene

Brief drafted with Claude Sonnet 5.5; the rewrite is built with Claude Opus
5.5. Nothing is committed without the user confirming the provenance trailer
(`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`) and who reviews
public-facing output.
