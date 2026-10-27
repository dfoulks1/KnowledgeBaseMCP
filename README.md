# KnowledgeBaseMCP

An MCP server (stdio) and CLI for [Open Knowledge Format][okf] (OKF) v0.2
bundles: directories of Markdown concepts with YAML frontmatter. It checks,
maintains and imports them. It cares how a concept is written, never what it
says. Local files only. No network. Never writes to git.

One contract, three users: an agent over MCP, CI, and a person at a terminal
with no AI.

Personal project. Apache-2.0, built under the [ASF generative-tooling
guidelines][asf-gt].

## Run

Requires [uv](https://docs.astral.sh/uv/).

A knowledgebase is wherever you point the tool: `KB_ROOT`, else the current
directory. It holds one bundle or several. A directory whose `index.md`
declares `okf_version` is a bundle root; bundles nest, and each bundle's
checks stop at the bundles inside it. `bundles` lists them; `split` makes a
directory its own bundle; `ingest keep_okf=true` merges one in.

`lint` follows where you are: in a bundle, that bundle and everything in it;
at the knowledgebase root, everything. Name files or directories to check
just those (`lint notes/a.md docs/`).

```sh
uv run KnowledgeBaseMCP.py help                 # every tool, one line each
uv run KnowledgeBaseMCP.py lint format=text
uv run KnowledgeBaseMCP.py init apply=true       # start a new bundle
```

Any tool runs as `<name> name=value ...` or `<name> '<json object>'`. Write
tools that touch many files default to `apply=false` and show a diff.

Exit codes: 0 ok, 1 findings, 2 usage error.

## Register with an MCP client

Claude Code, for one bundle:

```sh
claude mcp add knowledgebase --env KB_ROOT=/path/to/bundle -- uv run /path/to/KnowledgeBaseMCP.py
```

`KB_USER` prefills the reviewer id in `verify`'s confirmation prompt. The
client loads the tool list at start. After editing the script, restart
the client or reconnect the server (`/mcp` in Claude Code).

## Before you push

```sh
uv run KnowledgeBaseMCP.py lint format=text      # what's wrong, each with a fix
uv run KnowledgeBaseMCP.py fix apply=true        # mechanical repairs, then re-lint
uv run KnowledgeBaseMCP.py lint format=text      # what's left needs you
```

`scope=okf` limits the check to the spec; `scope=house` to hygiene (links,
anchors, orphans, filenames, tags, generated indexes).

## CI

Vendor `KnowledgeBaseMCP.py` into the bundle's repo, then:

```yaml
# .github/workflows/okf.yml
name: okf
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # provenance needs full history
      - uses: astral-sh/setup-uv@v6
      - run: uv run KnowledgeBaseMCP.py lint scope=okf format=github
```

Findings show as annotations on the PR. `format=sarif` suits code scanning.
On PRs, `since=origin/${{ github.base_ref }}` limits findings to the files the PR
changed.
On a large existing collection, commit a `baseline apply=true` snapshot and
run `lint baseline=.okf-baseline.json`, so only new findings fail. CI lints;
it does not push fixes (fork PRs get a read-only token anyway).

pre-commit, lint only (a hook that edits files leaves the commit unstaged):

```yaml
repos:
  - repo: local
    hooks:
      - id: okf-lint
        name: OKF lint
        entry: uv run KnowledgeBaseMCP.py lint format=text
        language: system
        pass_filenames: false
```

## Known limits

- Every write refreshes `log.md` and the generated index lists when they
  exist. In a busy repo those files conflict across PRs.
- Provenance from git history is inferred (`basis: git-history`). Actors may
  contain email addresses.
- A `sources[].via` call is what the agent says it ran, not proof.
- A human `verify` over MCP needs a client that supports elicitation
  (confirmation prompts); otherwise the human runs it from the CLI.
- `move` rewrites links inside code blocks too; read its diff.
- `ingest` does not convert other formats, scan for secrets or check
  licenses. Its plan says so.

## Self-check

```sh
uv run test_KnowledgeBaseMCP.py
```

## Spec

`SPEC.md` is OKF v0.2, copied unchanged from
[GoogleCloudPlatform/knowledge-catalog][okf] at commit `bad9bdb`,
Apache-2.0.

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/bad9bdbafa82c672b00d437d4f2cc8f17e9e5f58/okf/SPEC.md
[asf-gt]: https://www.apache.org/legal/generative-tooling.html
