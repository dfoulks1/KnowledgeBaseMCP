# Bowerbird

Keep a folder of Markdown notes in order, and let an AI assistant, a script or
you search and check them. It is for anyone who keeps notes, runbooks or documentation
as Markdown in a folder or repository. It works on knowledgebases in [Open Knowledge Format][okf]
(OKF) v0.2: one Markdown file per *concept*, each starting with a small header of
facts (its type, a description, where it came from, who checked it). A *bundle* is
a folder of concepts; a knowledgebase is a bundle, or a folder of bundles.

It is an MCP server (MCP, the Model Context Protocol, is how AI assistants call
tools) and a command line. It
checks, maintains and imports concepts, and finds the passages that answer a
question. It cares how a concept is written, never what it says. Local files only,
no network (but see semantic search, which downloads a model once). Never writes
to git. One contract, three users: an agent over MCP, CI, and a person at a
terminal with no AI.

Try it (needs [uv](https://docs.astral.sh/uv/); its installer is `curl -LsSf
https://astral.sh/uv/install.sh | sh`, which downloads and runs a script, so read it first
if you prefer). In an empty folder:

```sh
alias kb='uvx --from git+https://github.com/dfoulks1/bowerbird-mcp bowerbird-mcp'
kb init apply=true format=text
kb create deploy type=Playbook title="Deploy" description="How we deploy." \
   body="Run the deploy script, then check the dashboard. To roll back, redeploy the previous tag." format=text
kb passages 'how do we roll back' format=text     # the best passages, with file and line
kb lint format=text                               # ends: bowerbird-mcp lint: ok: ...
```

Personal project. Apache-2.0 (see [LICENSE](https://github.com/dfoulks1/bowerbird-mcp/blob/main/LICENSE); [NOTICE](https://github.com/dfoulks1/bowerbird-mcp/blob/main/NOTICE) credits the
spec), built under the [ASF generative-tooling guidelines][asf-gt]. Bugs and ideas:
[GitHub Issues](https://github.com/dfoulks1/bowerbird-mcp/issues); security reports: [SECURITY.md](https://github.com/dfoulks1/bowerbird-mcp/blob/main/SECURITY.md).

<!-- --8<-- [start:run] -->
## Run

Requires [uv](https://docs.astral.sh/uv/). Install on the fly, nothing to clone; this is
the form to use:

```sh
uvx --from git+https://github.com/dfoulks1/bowerbird-mcp bowerbird-mcp help
```

In the examples below, `uv run bowerbird_mcp.py ...` means the same command run
from a checkout of this repository (or beside a saved copy of that one file).
PyPI later: `uvx bowerbird-mcp`.

A `kbmcp.yaml` at the root of a knowledgebase (not in a bundle) marks its base
and configures it, so any `bowerbird-mcp` server knows where the
knowledgebase and its assets (index, archive, bundles) are, and the server
needs no env block. The tool finds the file from the current directory up, or
you name it with `--config`. It replaces the old `KB_ROOT` variable, which is
now refused. `KB_USER`, `KB_AI_PRODUCERS` and `KB_ROLE` still override it.
It is local config, never committed: each person or machine has its own, and a
fresh clone has none until `bowerbird-mcp config apply=true` writes one from
a built-in example (every setting commented out at its default). That also
lists `kbmcp.yaml` in the `.gitignore` beside it, and it never overwrites an
existing file. `lint` flags a `kbmcp.yaml` anywhere below the root
(`nested_config`): a second one would make that folder a second knowledgebase.

```yaml
about: Engineering runbooks.   # shown to the agent; tells knowledgebases apart when several are loaded
user: your-id         # prefills your id in confirmation prompts (KB_USER)
ai_producers: [zed]   # extra AI names for the provenance check (KB_AI_PRODUCERS)
passages: true        # false removes the passages and reindex tools
hubs: true            # concepts many others link to rank a little higher
semantic: false       # also match by meaning. `uvx bowerbird-mcp` carries what it needs; the bare script needs
                      # `uv run --with fastembed`. The model (~65 MB) downloads once into
                      # ~/.cache/bowerbird-mcp/models; passages are embedded and kept in the index
semantic_model: BAAI/bge-small-en-v1.5
min_similarity: 0.6   # how close in meaning a passage must be
index: .kbmcp/index.db   # one SQLite file: passages, BM25 index, links, vectors; "" = in memory
build: auto           # auto: passages keeps the index current; manual: only `reindex` does, passages reads
roles: [read, write, structure, lifecycle]   # roles the MCP server may offer; drop one to turn it off (see Register)
```

With no `kbmcp.yaml` the defaults apply. The index is a cache derived from
the concepts: safe to delete, never committed (a new `.kbmcp/` folder ignores
itself). To build it apart from the server, run `reindex` (incremental: only
changed files are read) and set `build: manual`, so `passages` only reads it:

```sh
uvx bowerbird-mcp reindex format=text     # first semantic run embeds everything: minutes, once
```

```yaml
# .pre-commit-config.yaml: refresh after you commit and after pulls
repos:
  - repo: local
    hooks:
      - id: kbmcp-reindex
        name: Bowerbird reindex
        entry: uvx bowerbird-mcp reindex
        language: system
        pass_filenames: false
        always_run: true
        verbose: true
        stages: [pre-commit, post-merge, post-checkout]
```

A knowledgebase is where its `kbmcp.yaml` is: the tool looks for one from the
current directory up (or takes `--config path/to/kbmcp.yaml`) and treats that
file's folder as the base. With none, it uses the current directory. It is one bundle at its root, or a set of sibling bundles. A
directory whose `index.md` declares `okf_version` is a bundle root; bundles do
not nest. An `index.md` at the knowledgebase root lists its bundles (`index
apply=true` there writes it), and tools find the root from inside a bundle
through it. `bundles` lists them, `split` makes a directory its own bundle,
`rename` moves or renames one, `migrate` moves a concept between bundles,
`archive` and `unarchive` retire and restore a concept or a whole bundle,
`ingest keep_okf=true` merges one in, and `upgrade` converts OKF v0.1.

Tools follow where you are: in a bundle, that bundle; at the knowledgebase
root, every bundle (`lint`, `fix`, `baseline`, `status`, `list`, `search`,
`recheck_plan`). Name files or directories to lint just those
(`lint notes/a.md docs/`). Files are named the OKF way: a bundle and the
path within it (`bundle=eng file=runbooks/deploy.md`), in every input and
output. On the command line, without `bundle=`, paths are relative to where
you are. Write tools act in the bundle the file belongs to. In a git work
tree, files git ignores are skipped.

```sh
wget https://raw.githubusercontent.com/dfoulks1/bowerbird-mcp/main/bowerbird_mcp.py
uv run bowerbird_mcp.py help                 # every tool, one line each
uv run bowerbird_mcp.py help move            # one tool: what it does, its arguments
uv run bowerbird_mcp.py lint format=text
uv run bowerbird_mcp.py init apply=true       # start a new bundle
```

Any tool runs as `<name> name=value ...` or `<name> '<json object>'`. Bare
arguments fill the required ones in order (`move a.md b.md`); on `set`, any
other `key=value` is frontmatter (`set a.md status=deprecated tags=[x,y]`).
Write tools that touch many files default to `apply=false` and show a diff.

`--attest` records you, as `human:<KB_USER>` (else your git `user.email`), on
`create` and `provenance` (`generated`), `verify` and `recheck_apply`
(`verified`). It exists
only on the command line: no MCP call can pass it.

Output is JSON; `format=text` prints one key per line and diffs as is.

Exit codes: 0 ok, 1 findings, 2 usage error.

<!-- --8<-- [end:run] -->
<!-- --8<-- [start:layout] -->
## Layout

```
kb/                          the knowledgebase (kbmcp.yaml sits here)
  index.md                   lists the bundles; no frontmatter
  .gitattributes             log.md and index.md merge=union
  eng/                       a bundle
    index.md                 okf_version, then the list of its concepts
    log.md                   its history (§9)
    runbooks/
      index.md               optional: this directory's concepts
      deploy.md              a concept
  archive/                   the archive: a knowledgebase of its own, set apart
    index.md                 lists the archived bundles
    eng/old-runbook.md       archived from eng (archive/eng is a bundle)
```

### index.md

OKF §8: an index lists what is in its directory, for progressive disclosure.
Every index has the same body shape, sections under headings with one entry
per item:

```markdown
# Engineering

Hand-written text is kept.

<!-- kb-index:start (generated by KnowledgeBaseMCP index; do not edit between the markers) -->

### runbooks

* [Deploy](./runbooks/deploy.md) - How we deploy.

<!-- kb-index:end -->
```

- The tool owns what is between the markers and rebuilds it from frontmatter
  (title, else first heading, else file name; `description`, else the first
  sentence). Write anything else around them.
- **Knowledgebase root:** no frontmatter (it is not a bundle). The list has one
  entry per bundle, titled by that bundle's first heading. Tools find the
  knowledgebase by walking up from a bundle to the nearest `index.md` that links
  to it.
- **Bundle root:** frontmatter holds only `okf_version: "0.2"`, which is what
  makes the directory a bundle (§12). The list covers every concept, a section
  per top-level folder.
- **Any other directory:** no frontmatter. The list covers that directory's
  concepts and subdirectories (`index dirs=true` writes one everywhere).
- Being listed counts as being linked, so a listed concept is not an orphan.
- `get` synthesizes a missing index from frontmatter (§8 allows this).

### log.md

OKF §9: date headings, newest first, one entry per line. Each tool write adds an
entry to the nearest `log.md` above the change, with a hidden unix-time stamp:

```markdown
## 2026-10-27

* <!-- 1761588000 --> **Update**: Moved deploy.md to [ship.md](/runbooks/ship.md).
```

`record "note"` writes one by hand (link the concept it is about). `log file=x.md`
reads a concept's history: the entries linking to it in every `log.md` above it,
and the git commits that changed it. `log` alone shows the bundle's recent
entries.

`init` adds `log.md merge=union` and `index.md merge=union` to the
knowledgebase's `.gitattributes`, so git keeps both sides when parallel
branches log or index. After such a merge, `fix` merges duplicate log date
sections, orders stamped entries by time, and rebuilds the generated index
lists. A section with a
hand-written, unstamped entry keeps its order.

### The archive

`archive/` is a knowledgebase within the knowledgebase, and a special one. Its
`index.md` lists its bundles, like the knowledgebase root's. `archive file=x.md
bundle=eng` moves a concept to `archive/eng/x.md` (starting `archive/eng` as a
bundle); `archive bundle=eng` moves the whole bundle to `archive/eng/`, still a
bundle. `unarchive eng/x.md` or `unarchive eng` puts them back. Links follow
both ways.

The live knowledgebase does not see the archive: lint, list, search, status
and web leave it out, nothing in it counts as nesting, and lint warns on links
into it (`archived_link`). Editing tools refuse archived concepts. That is the
only enforcement: the files are plain files, so an editor or a commit can still
change them. It works whether the knowledgebase root is a set of bundles or a
bundle itself.

<!-- --8<-- [end:layout] -->
<!-- --8<-- [start:register] -->
## Register with an MCP client

Add this to your MCP client's servers file: `.mcp.json` in the project for
Claude Code, `claude_desktop_config.json` for Claude Desktop, `.cursor/mcp.json`
for Cursor. VS Code's `.vscode/mcp.json` takes the same entry under `"servers"`.

```json
{
  "mcpServers": {
    "bowerbird": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/dfoulks1/bowerbird-mcp", "bowerbird-mcp"]
    }
  }
}
```

The server runs in the project folder, so it finds the `kbmcp.yaml` there (your
id is `user:` in it). To point at one elsewhere, add `"--config",
"/path/to/kb/kbmcp.yaml"` to `args`. Or, in Claude Code:

```sh
claude mcp add bowerbird -- uvx --from git+https://github.com/dfoulks1/bowerbird-mcp bowerbird-mcp --config /path/to/kb/kbmcp.yaml
```

Several knowledgebases at once: one entry each, with its own `--config`. The
client prefixes tool names with the entry name, and each file's `about:` tells
the agent what that knowledgebase holds. Each keeps its own index.

The client loads the tool list at start. After editing the script, restart
the client or reconnect the server (`/mcp` in Claude Code).

### Roles: a smaller tool list per agent

All 35 tools cost an agent about 9,500 tokens of schema (an estimate: each tool's description
length in characters, divided by four); each role is about a quarter of that. Register the same
script more than once, each with a role (`--role`, or `KB_ROLE`; several with
commas), and each server offers only that role's tools:

| Role | Tools | Schema |
|---|---|---|
| `read` | find and read, nothing written: `dirs` `get` `heatmap` `links` `list` `log` `passages` `search` `status` `vocab` | 10, ~2,460 tokens |
| `structure` | shape and reorganization: `archive` `bundles` `dirs` `ingest` `migrate` `move` `rename` `split` `unarchive` `web` | 10, ~2,450 tokens |
| `write` | write a concept and check it: `cite` `create` `fix` `lint` `record` `set` `verify` | 7, ~2,450 tokens |
| `lifecycle` | keep it current: `baseline` `config` `index` `init` `provenance` `recheck_apply` `recheck_plan` `reindex` `upgrade` | 9, ~2,270 tokens |

```json
{
  "mcpServers": {
    "kb-read":  { "command": "uvx", "args": ["--from", "git+https://github.com/dfoulks1/bowerbird-mcp", "bowerbird-mcp", "--role", "read"] },
    "kb-write": { "command": "uvx", "args": ["--from", "git+https://github.com/dfoulks1/bowerbird-mcp", "bowerbird-mcp", "--role", "write"] }
  }
}
```

The `read` server is read-only, so a client can approve it without asking; the other
three change files. A tool can belong to more than one role (`dirs` is in `read` and
`structure`), and a server with no `--role` offers them all. With no `--role` the server offers every role that `roles:` in
`kbmcp.yaml` leaves on; naming a role that is off refuses to start. The CLI
always has every tool.

<!-- --8<-- [end:register] -->
<!-- --8<-- [start:ci] -->
## Before you push

```sh
uv run bowerbird_mcp.py lint format=text      # what's wrong, each with a fix
uv run bowerbird_mcp.py fix apply=true        # mechanical repairs, then re-lint
uv run bowerbird_mcp.py lint format=text      # what's left needs you
```

`scope=okf` limits the check to the spec; `scope=house` to hygiene (links,
anchors, orphans, islands, stubs, duplicate titles, reference links,
filenames, tags, generated indexes). `only=` and `ignore=` keep or drop finding
kinds: `lint only=stub,island`.

## CI

Vendor `bowerbird_mcp.py` into the bundle's repo, then:

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
      - run: uv run bowerbird_mcp.py lint scope=okf format=github
```

Findings show as annotations on the PR. `format=sarif` suits code scanning.
On PRs, `since=origin/${{ github.base_ref }}` limits findings to the files the PR
changed.
On a large existing collection, commit a `baseline apply=true` snapshot and
run `lint baseline=.okf-baseline.json`, so only new findings fail. The
snapshot sits at the knowledgebase root and matches from any directory. CI lints;
it does not push fixes (fork PRs get a read-only token anyway).

To skip files outright, list them in a `kbmcp.nolint` file. It works like
`.gitignore`: it may sit in any directory, patterns are relative to it, the
last match wins and `!` re-includes. At the knowledgebase root it covers every
bundle. Skipped files are still read, so links to them resolve. One file can
skip itself with the line `<!-- kbmcp-nolint -->`.

```gitignore
# kbmcp.nolint: agent instructions are not concepts
AGENTS*
CLAUDE.md
.kiro/
```

pre-commit, lint only (a hook that edits files leaves the commit unstaged).
`lint` always ends with a verdict line, such as `bowerbird-mcp lint: ok: 214
concept(s) in 3 bundle(s) checked, 0 finding(s), conformant: True`, so you can
see it ran. pre-commit prints a passing hook's output only with `verbose: true`:

```yaml
repos:
  - repo: local
    hooks:
      - id: okf-lint
        name: OKF lint
        entry: uv run bowerbird_mcp.py lint format=text
        language: system
        pass_filenames: false
        verbose: true
```

<!-- --8<-- [end:ci] -->
<!-- --8<-- [start:limits] -->
## Reading the knowledgebase

- Find things in three steps, each small: `dirs` maps the bundle (each
  directory and how many concepts it holds); `search` ranks concepts by where
  every word matches (title, then id, tags, type, description, body), with
  `type=`, `tag=` and `dir=` filters; `get` reads only the top hit. `vocab`
  lists the tags and types in use, the words those filters take.

  ```sh
  uv run bowerbird_mcp.py dirs format=text
  uv run bowerbird_mcp.py search deploy rollback dir=runbooks format=text
  uv run bowerbird_mcp.py get runbooks/deploy.md format=text
  ```

- `passages` answers a question. It cuts concepts at
  headings and returns the best sections, each with file, line, heading,
  trust tier and staleness, so the answer can cite and qualify its sources.
  Ranking is BM25 (rarer words count more; any one word may match; no
  stemming), with title, tags, type and description counting too, and
  concepts many others link to a little higher (`hubs`). With `semantic` on,
  passages are also matched by meaning and the two rankings are fused. No hit
  returns `gap: true`: say the knowledgebase has nothing, don't guess. Passages
  are indexed in one SQLite file (`index` in `kbmcp.yaml`), updated from the
  files that changed. `reindex` builds it ahead of time, for a hook, and with
  `build: manual` `passages` only reads it; `reindex info=true` reports what it
  holds and how far behind it is, `drop=true` deletes it. `passages: false` removes
  both tools.

  ```sh
  uv run bowerbird_mcp.py reindex format=text
  uv run bowerbird_mcp.py passages 'how do we roll back a deploy' format=text
  ```

- `web` maps links and citations: bundles at the knowledgebase root, concepts
  in a bundle. `format=text` for the terminal, `format=mermaid` for anything
  that draws Mermaid (GitHub, GitLab).
- `heatmap days=30` ranks concepts by how many commits changed them (the ones
  most likely to collide across branches) and by how many people did; who
  changes the most; and concepts only one person has ever touched. index.md and
  log.md are left out.
- `status` lists what needs a person next: longest since review, oldest
  drafts, concepts without sources, the longest concepts, and what goes stale
  within `due_days`; the most linked-to concepts (`hubs`); and the pages links
  want that do not exist yet (`wanted`), most wanted first.
- `log file=x.md` is a concept's history.

## Known limits

- A human `verify` over MCP needs a client that supports elicitation
  (confirmation prompts); otherwise the human runs it from the CLI.
- `move`, `migrate`, `split`, `rename`, `archive` and `unarchive` rewrite links
  (code blocks included; read the diff) and §6.2 path fields (`resource`,
  `computation`, `executor`/`attester`, `sources[].resource`). A value naming
  an existing file is a path; one naming nothing is a path only if it has a
  file extension or a leading `/`, `./` or `../`, else a scope description.
- OKF makes `okf_version` optional; here it is how a bundle is found. An
  undeclared bundle is any folder until you pass it as `bundle=`.
- `ingest` does not convert other formats or check licenses. Its plan says so.
- `passages` has no stemming ("rolling" will not match "roll"), and with
  `build: manual` it does not notice files changed since the last `reindex`.
  Semantic search downloads its model (~65 MB) once into
  `~/.cache/bowerbird-mcp/models`. `fastembed` and its dependencies (about 150 MB) come
  with the installed package (`uvx bowerbird-mcp`) but not with the bare script, which
  needs `uv run --with fastembed` for `semantic: true`. The index lives in the file
  `index` names and is safe to delete; nothing in the
  knowledgebase changes.

<!-- --8<-- [end:limits] -->
## Self-check

```sh
uv run test_bowerbird_mcp.py
```

## Spec

`SPEC.md` is OKF v0.2, copied unchanged from
[GoogleCloudPlatform/knowledge-catalog][okf] at commit `bad9bdb`,
Apache-2.0.

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/bad9bdbafa82c672b00d437d4f2cc8f17e9e5f58/okf/SPEC.md
[asf-gt]: https://www.apache.org/legal/generative-tooling.html
