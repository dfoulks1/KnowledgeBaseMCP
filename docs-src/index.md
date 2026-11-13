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
    <p>No AI needed: <code>help</code>, ranked <code>search</code>, <code>passages</code> for questions, readable text output, and <code>--attest</code> to sign your own reviews.</p>
  </div></div>
</div>

<p class="note">Local files only. No network, except the one-time model download if you turn on semantic search. Never writes to git. One Python file, installed or run with <a href="https://docs.astral.sh/uv/">uv</a>. These pages were written with Claude Opus 5.5 and Claude Sonnet 5.5 and are under human review.</p>

## Quickstart

Nothing to clone. [uv](https://docs.astral.sh/uv/) installs it and its dependencies on the fly:

```sh
uvx --from git+https://github.com/dfoulks1/KnowledgeBaseMCP knowledgebasemcp help
```

Or take the one file and run it:

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
      "command": "uvx",
      "args": ["--from", "git+https://github.com/dfoulks1/KnowledgeBaseMCP", "knowledgebasemcp"]
    }
  }
}
```

A `kbmcp.yaml` marks the base of a knowledgebase: the server finds it from the
project folder up (or take `--config path`), and it sets your id, what the
knowledgebase is about, and the search settings. It is local config, kept out of git (`config apply=true` writes one and ignores it); everyone has their own ([the guide](guide.md#run) has every key). To give an agent fewer
tools, register the server with a role: `read` (find and read, nothing written), `structure`
(reorganize), `write` (author and check) or `lifecycle` (keep it current). [The guide](guide.md#roles-a-smaller-tool-list-per-agent) has the lists.

Or work from the terminal, no AI needed:

```sh
# start a bundle
uv run KnowledgeBaseMCP.py init bundle=eng apply=true

# write a concept (a few real sentences, or `passages` has nothing to find)
uv run KnowledgeBaseMCP.py create eng/runbooks/deploy type=Playbook title="Deploy" \
    description="How we deploy." \
    body="Run the deploy script, then check the dashboard. To roll back, redeploy the previous tag."

# find it: the map, then the best matches
uv run KnowledgeBaseMCP.py dirs format=text
uv run KnowledgeBaseMCP.py search deploy format=text

# ask a question: the best sections, each with file, line and trust to cite
uv run KnowledgeBaseMCP.py passages 'how do we deploy' format=text

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
From here, `dirs` and `search` find a concept, `passages` answers a question
from the best sections (and says so when there is nothing to find), `lint` checks every file
against the spec, `status` says what needs a person next (including the
pages links want that nobody has written), and `heatmap` shows where the
work is.

Next: [getting started](getting-started.md) for a ten-minute walkthrough,
[understanding OKF](understanding-okf.md) for what the format is and why it is built this way,
the [guide](guide.md) for layout and workflows, the [tools](tools.md)
for every command, and the [OKF v0.2 specification][okf] it implements.

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/bad9bdbafa82c672b00d437d4f2cc8f17e9e5f58/okf/SPEC.md
