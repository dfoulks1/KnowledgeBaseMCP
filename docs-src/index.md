<div class="hero">
  <img src="img/logo.svg" alt="A card-catalog drawer front: wood, a brass label frame, a round knob" width="136" height="136">
  <h1 id="knowledgebasemcp">KnowledgeBaseMCP</h1>
  <p class="lead">Keep an <a href="https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/bad9bdbafa82c672b00d437d4f2cc8f17e9e5f58/okf/SPEC.md">Open Knowledge Format</a> knowledgebase in order: checked, maintained and imported, by agents and people alike. It cares how a concept is written, never what it says.</p>
  <p>
    <a class="btn btn-brand me-2" href="guide/">Get started</a>
    <a class="btn btn-outline-secondary" href="https://github.com/dfoulks1/KnowledgeBaseMCP">View on GitHub</a>
  </p>
</div>

<div class="row g-3 users my-4">
  <div class="col-md-4"><div class="card p-3">
    <h3>An agent, over MCP</h3>
    <p>Every tool, with a diff before each write and a confirmation prompt before anything records a person.</p>
  </div></div>
  <div class="col-md-4"><div class="card p-3">
    <h3>CI</h3>
    <p><code>lint</code> as GitHub annotations or SARIF, a baseline for old findings, and <code>since=</code> for pull requests.</p>
  </div></div>
  <div class="col-md-4"><div class="card p-3">
    <h3>A person at a terminal</h3>
    <p>No AI needed: <code>help</code>, readable text output, and <code>--attest</code> to sign your own reviews.</p>
  </div></div>
</div>

<p class="note">Local files only. No network. Never writes to git. One Python file, run with <a href="https://docs.astral.sh/uv/">uv</a>. These pages were written with Claude Opus 5.5 and are under human review.</p>

## Quickstart

One file. [uv](https://docs.astral.sh/uv/) fetches its dependencies on the first run.

```sh
wget https://raw.githubusercontent.com/dfoulks1/KnowledgeBaseMCP/main/KnowledgeBaseMCP.py
uv run KnowledgeBaseMCP.py help
```

No uv yet? `curl -LsSf https://astral.sh/uv/install.sh | sh`

Then add it to your MCP client's servers file (`.mcp.json` for Claude Code;
[other clients](guide.md#register-with-an-mcp-client)):

```json
{
  "mcpServers": {
    "knowledgebase": {
      "command": "uv",
      "args": ["run", "/path/to/KnowledgeBaseMCP.py"],
      "env": { "KB_ROOT": "/path/to/kb", "KB_USER": "your-id" }
    }
  }
}
```

Or work from the terminal, no AI needed:

```sh
# start a bundle
uv run KnowledgeBaseMCP.py init bundle=eng apply=true

# write a concept
uv run KnowledgeBaseMCP.py create eng/runbooks/deploy \
    type=Playbook description="How we deploy."

# what's wrong, each with a fix; then the mechanical repairs
uv run KnowledgeBaseMCP.py lint format=text
uv run KnowledgeBaseMCP.py fix apply=true

# any tool: what it does, its arguments
uv run KnowledgeBaseMCP.py help move
```

## What a knowledgebase looks like

A knowledgebase is a folder of bundles. A bundle is a folder of concepts, one
Markdown file each. Two small bundles:

```text
kb/
  index.md                 lists the bundles
  eng/                     a bundle: its index.md declares okf_version "0.2"
    index.md
    log.md                 what changed, newest first
    db.md
    runbooks/ship.md
    refs/pg.md
  mkt/
    index.md
    log.md
    launch.md
```

Each concept is frontmatter (what kind of thing it is, where its facts came
from, who checked it) over an ordinary Markdown body. Here is `eng/db.md`:

```markdown
---
type: Reference
title: Database
description: The PostgreSQL cluster behind every service.
sources:
  - id: pg
    resource: refs/pg.md
verified: { by: human:dfoulks, at: 2026-10-27T14:00:00Z }
---

We run PostgreSQL 16.4.[^pg] Deploys follow [the ship runbook](/runbooks/ship.md).

[^pg]: PostgreSQL release notes
```

Concepts point at each other in two ways: a Markdown **link** in the body,
and a **citation** in `sources`, which records where a fact came from. `web
format=mermaid` draws both for the whole knowledgebase:

```mermaid
graph LR
  subgraph eng
    db["db.md"]
    ship["runbooks/ship.md"]
    pg["refs/pg.md"]
  end
  subgraph mkt
    launch["launch.md"]
  end
  db -.->|cites| pg
  db -->|links| ship
  ship -->|links| db
  ship -->|links| launch
  launch -->|links| db
```

Solid arrows are links; dotted ones are citations. The boxes are bundles, so
an arrow that leaves its box crosses into another bundle. That is allowed,
but lint flags it because the link breaks if one bundle is published alone.
From here, `lint` checks every file against the spec, `status` says what
needs a person next, and `heatmap` shows where the work is.

Next: the [guide](guide.md) for layout and workflows, the [tools](tools.md)
for every command, and the [OKF v0.2 specification][okf] it implements.

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/bad9bdbafa82c672b00d437d4f2cc8f17e9e5f58/okf/SPEC.md
