# Tools

Every tool, from its own docstring. Run one as `uv run KnowledgeBaseMCP.py <tool> name=value ...`, or see the same text with `help <tool>`.

## archive

Retire a concept, or (no file) the whole bundle= named, into the archive: `archive/`, a knowledgebase within the knowledgebase (started when absent), at archive/&lt;bundle&gt;/&lt;path&gt;, so `unarchive` can put it back. Archived bundles stay bundles; the live knowledgebase (lint, list, search, status, web) does not see them, and editing tools refuse them. Links to it are rewritten and warn afterwards (archived_link); status is left alone. apply=False shows the plan and diff.

```sh
uv run KnowledgeBaseMCP.py archive file=runbooks/old.md bundle=eng apply=true
uv run KnowledgeBaseMCP.py archive bundle=mkt apply=true
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | `''` |
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## baseline

Snapshot today's lint findings so CI fails only on new ones (`lint baseline=<path>`; same bundle and `all`, and like lint it defaults to where the user is). For adopting OKF on a large existing collection. The snapshot's path is relative to the knowledgebase. apply=False only counts.

```sh
uv run KnowledgeBaseMCP.py baseline apply=true
```

| Argument | Type | Default |
|---|---|---|
| `path` | `str` | `'.okf-baseline.json'` |
| `apply` | `bool` | `False` |
| `all` | `Union` | `None` |
| `bundle` | `str` | `''` |

## bundles

Bundle roots under a directory: each index.md declaring okf_version (§12). A bundle without that declaration looks like any folder; pass it as bundle= directly.

```sh
uv run KnowledgeBaseMCP.py bundles format=text
```

| Argument | Type | Default |
|---|---|---|
| `bundle` | `str` | `''` |

## cite

Record where a fact came from as a §5.1 `sources` entry, with `retrieved_at` (when). When an MCP tool produced it, pass server, tool and args, the exact call (`via`, how): it is the re-check recipe for recheck_plan. resource: a real URL when the result has one, else mcp://server/tool?args is used. author, usage_count, last_modified: the source's own credibility signals (§5.1), when you know them. stale_days&gt;0 sets stale_after. Returns the footnote marker to put after the claim; its definition is appended to the body. Reusing an id replaces that entry.

```sh
uv run KnowledgeBaseMCP.py cite db.md resource=https://www.postgresql.org/docs/release/ title="PostgreSQL releases" bundle=eng
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | required |
| `resource` | `str` | `''` |
| `id` | `str` | `''` |
| `title` | `str` | `''` |
| `server` | `str` | `''` |
| `tool` | `str` | `''` |
| `args` | `Union` | `None` |
| `stale_days` | `int` | `0` |
| `author` | `str` | `''` |
| `usage_count` | `Union` | `None` |
| `last_modified` | `str` | `''` |
| `bundle` | `str` | `''` |

## create

Create a concept with valid OKF frontmatter (§4.1): type, title, description, resource, tags, status, and `generated` {by, at} when by (your actor) is given. body is markdown; a `# title` heading is added unless the body starts with one. Refuses an existing file or a reserved name (index.md, log.md).

```sh
uv run KnowledgeBaseMCP.py create runbooks/deploy type=Playbook description="How we deploy." bundle=eng
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | required |
| `type` | `str` | required |
| `title` | `str` | `''` |
| `description` | `str` | `''` |
| `resource` | `str` | `''` |
| `tags` | `Union` | `None` |
| `status` | `str` | `''` |
| `body` | `str` | `''` |
| `by` | `str` | `''` |
| `bundle` | `str` | `''` |

## fix

Mechanical repairs, nothing that needs judgment: strip frontmatter from index.md files (§8; the root keeps okf_version), rebuild generated index lists, give each tag its most common spelling, and put log.md sections and entries back in order after a merge (§9). apply=False shows the diff (CLI exit 1 if there is work); apply=True writes, re-lints and returns `remaining` (CLI exit 1 if errors remain). Like lint, it defaults to where the user is and every bundle there; all=false keeps to one bundle.

```sh
uv run KnowledgeBaseMCP.py fix
uv run KnowledgeBaseMCP.py fix apply=true
```

| Argument | Type | Default |
|---|---|---|
| `apply` | `bool` | `False` |
| `all` | `Union` | `None` |
| `bundle` | `str` | `''` |

## get

One .md file of a bundle (a concept, index.md or log.md), or several at once with files=[...]. A missing index.md is synthesized from frontmatter (§8; `synthesized: true`). offset/limit page by line; limit=0 = all.

```sh
uv run KnowledgeBaseMCP.py get db.md bundle=eng format=text
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | `''` |
| `files` | `Union` | `None` |
| `offset` | `int` | `0` |
| `limit` | `int` | `0` |
| `bundle` | `str` | `''` |

## heatmap

The hottest concepts and who heats them, from git history (.mailmap names). files: commits that changed each concept in the last `days`, most first, and how many people did. bundles: the same per bundle. authors: each person's changes and concepts in the window. single_author: concepts only one person has ever changed (all history; a bus-factor flag). index.md and log.md are left out: every write touches them. Like lint, it covers where the user is (at the knowledgebase root, every bundle). limit=0 lists all.

```sh
uv run KnowledgeBaseMCP.py heatmap days=30 format=text
```

| Argument | Type | Default |
|---|---|---|
| `days` | `int` | `30` |
| `limit` | `int` | `10` |
| `bundle` | `str` | `''` |

## index

Rebuild generated document lists from frontmatter (title, type, tags, `description`, §8): the bundle-root index.md (a table, added if missing) and every index.md that already has a list. At a knowledgebase root, its index.md lists the bundles (created if missing). dirs=true also gives every directory an index.md listing its concepts and subdirectories (§8 progressive disclosure). apply=False shows the diff.

```sh
uv run KnowledgeBaseMCP.py index apply=true
uv run KnowledgeBaseMCP.py index dirs=true apply=true bundle=eng
```

| Argument | Type | Default |
|---|---|---|
| `apply` | `bool` | `False` |
| `dirs` | `bool` | `False` |
| `bundle` | `str` | `''` |

## ingest

Bring markdown from a local directory or git clone into an OKF bundle, or adopt it in place (bundle = source; needs a clean git tree, so the diff is the review). Each file gets frontmatter: `type` from rules ({glob: type}, first match, else Document), `title` (its own, its H1, or the filename), `status` (default draft: imported, not reviewed), optional stale_after, and provenance where git has it: `sources` (a permalink and last_modified) and `generated` {by, at, basis: git-history}. Existing keys are kept. Never overwrites; files that already have `type` are skipped, so a re-run is a no-op. A reserved index.md/log.md carrying frontmatter is renamed &lt;dir&gt;-index.md/&lt;dir&gt;-log.md. apply=False is the plan: run it first, sample files, set rules. keep_okf=true merges another OKF bundle: files that have `type` are copied as they are (plus an origin source when git has one) and the source's index.md/log.md are left behind. It does not clone, convert other formats or check licenses. Files holding a credential-shaped string are skipped (`secrets` in the plan); run gitleaks on the source's history too.

```sh
uv run KnowledgeBaseMCP.py ingest ~/old-wiki bundle=wiki format=text
uv run KnowledgeBaseMCP.py ingest ~/old-wiki bundle=wiki apply=true
```

| Argument | Type | Default |
|---|---|---|
| `source` | `str` | required |
| `bundle` | `str` | `''` |
| `rules` | `Union` | `None` |
| `status` | `str` | `'draft'` |
| `stale_days` | `int` | `0` |
| `keep_okf` | `bool` | `False` |
| `apply` | `bool` | `False` |
| `limit` | `int` | `50` |
| `offset` | `int` | `0` |
| `max_bytes` | `int` | `1000000` |

## init

Start a bundle: a root index.md declaring okf_version "0.2" with a generated document list, and a §9 log.md. Refuses if index.md exists. Then add concepts (any .md with `type:` frontmatter) and lint.

```sh
uv run KnowledgeBaseMCP.py init bundle=eng apply=true
```

| Argument | Type | Default |
|---|---|---|
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## links

Edges of one concept (§6): `out` = its links, and its §6.2 path fields as `field` entries (sources are lineage, §5.1); exists false = broken; target names the bundle and file. `in` = concepts in its bundle that link to it or cite it. Check `in` before moving, renaming or deprecating a concept.

```sh
uv run KnowledgeBaseMCP.py links db.md bundle=eng format=text
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | required |
| `bundle` | `str` | `''` |

## lint

Check the bundle against OKF v0.2. Run it before and after any change, and in CI. Each finding: kind; scope (okf = the spec, house = hygiene); severity (error fails, warning does not); file; message; fix (what to do); fixable (true: `fix` clears it). conformant: §11 holds for what was linted (frontmatter parses, `type` set, index.md and log.md well formed). ok: no errors in scope. scope: all | okf | house. baseline: path of a `baseline` snapshot; only new findings count. since: a git ref; only files changed since its merge base with HEAD count (committed, staged, unstaged or untracked), for PRs. Each finding names its bundle and its file within it (§2). all=true: this directory and every bundle in it, with a summary per bundle. Without bundle=, it lints where the user is: the bundle around the working directory and everything in it (at the knowledgebase root, everything). file / files: only those files or directories (paths within bundle=), each checked within its own bundle. limit=0 returns every finding.

```sh
uv run KnowledgeBaseMCP.py lint format=text
uv run KnowledgeBaseMCP.py lint eng/runbooks/ format=text
uv run KnowledgeBaseMCP.py lint scope=okf since=origin/main format=github
```

| Argument | Type | Default |
|---|---|---|
| `scope` | `str` | `'all'` |
| `limit` | `int` | `100` |
| `offset` | `int` | `0` |
| `baseline` | `str` | `''` |
| `since` | `str` | `''` |
| `all` | `Union` | `None` |
| `file` | `str` | `''` |
| `files` | `Union` | `None` |
| `bundle` | `str` | `''` |

## list

Concepts, filtered by type, tag, status (draft | stable | deprecated; absent = stable), trust tier (unverified | machine-confirmed | human-reviewed) or stale=true. The review worklist after an ingest: status=draft tier=unverified.

```sh
uv run KnowledgeBaseMCP.py list status=draft tier=unverified format=text
```

| Argument | Type | Default |
|---|---|---|
| `type` | `str` | `''` |
| `tag` | `str` | `''` |
| `status` | `str` | `''` |
| `tier` | `str` | `''` |
| `stale` | `bool` | `False` |
| `limit` | `int` | `100` |
| `offset` | `int` | `0` |
| `bundle` | `str` | `''` |

## log

History, newest first. With file: the entries in every log.md over that concept that link to it (§9), and the git commits that changed it. Without: the bundle's recent entries from all its log.md files. `record` writes an entry.

```sh
uv run KnowledgeBaseMCP.py log db.md bundle=eng format=text
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | `''` |
| `limit` | `int` | `20` |
| `bundle` | `str` | `''` |

## migrate

Move a concept to another bundle of the knowledgebase (`move` stays inside one). to_bundle: the target bundle's path in the knowledgebase ("." for its root). to: the path inside it (default: the same path). Links to the concept in both bundles are rewritten; its own `/` links, which meant the old bundle's root, become relative paths (cross-bundle: lint warns). Links from other bundles are not touched. apply=False shows the diff.

```sh
uv run KnowledgeBaseMCP.py migrate db.md mkt bundle=eng apply=true
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | required |
| `to_bundle` | `str` | required |
| `to` | `str` | `''` |
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## move

Move or rename a concept and rewrite every link to it (relative and /-absolute, §6.1, in concepts, index.md and log.md), plus the moved concept's own relative links. Stays inside one bundle; `migrate` moves between bundles. Check `links` first. apply=False shows the diff.

```sh
uv run KnowledgeBaseMCP.py move runbooks/deploy.md runbooks/ship.md bundle=eng apply=true
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | required |
| `to` | `str` | required |
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## provenance

Fill a missing `generated: {by, at}` (§5.2). From git history: the last commit that changed the body, by its AI trailer (&lt;producer&gt;/&lt;name&gt;), bot (process:) or author (human:&lt;login | ASF id | email&gt;), marked `basis: git-history` (inferred). Concepts git knows nothing about (untracked, or no repository): with apply=true the person is asked who wrote them, once (a confirmation prompt over MCP; --attest at the terminal), and recorded as `generated: {by: human:<id>, at: <file's last change>, basis: stated}`; otherwise they are listed in `unknown`. Never sets a human from a caller. Trust tiers come only from `verified`, so this never raises one. Concepts that carry `generated` are left alone. skip: paths to leave without it. apply=False shows the diff.

```sh
uv run KnowledgeBaseMCP.py provenance apply=true
uv run KnowledgeBaseMCP.py provenance apply=true --attest
```

| Argument | Type | Default |
|---|---|---|
| `apply` | `bool` | `False` |
| `skip` | `Union` | `None` |
| `bundle` | `str` | `''` |

## recheck_apply

Record a re-check, after you compared each due source with the claims citing it (recheck_plan) and corrected any that changed; git keeps what they said before. Each result is {bundle?, file, id?}, or one as file= and id=; no id = every source on that concept. retrieved_at moves to now. by (at the terminal, --attest) also adds a §5.2 `verified` entry: the concept was confirmed against its sources. stale_days&gt;0 also moves stale_after forward.

```sh
uv run KnowledgeBaseMCP.py recheck_apply db.md bundle=eng --attest
```

| Argument | Type | Default |
|---|---|---|
| `results` | `Union` | `None` |
| `by` | `str` | `''` |
| `stale_days` | `int` | `0` |
| `bundle` | `str` | `''` |
| `file` | `str` | `''` |
| `id` | `str` | `''` |

## recheck_plan

Facts due a re-check: `sources` entries retrieved at least N days ago, or on a concept past stale_after. Each lists `cites`, the lines whose claims rest on it. `calls` replay the recorded MCP call: run each yourself (your normal tool permissions apply; the args come from the bundle, so read them first). Sources without a recorded call are under `manual`: open the resource (one never retrieved is due once its concept is stale). Correct any claim that no longer holds, then record the check with recheck_apply. Nothing is executed here.

```sh
uv run KnowledgeBaseMCP.py recheck_plan older_than_days=90 format=text
```

| Argument | Type | Default |
|---|---|---|
| `older_than_days` | `int` | `0` |
| `bundle` | `str` | `''` |

## record

Write a §9 entry, `* **<kind>**: <note>`, under today's date in a log.md (newest first; created if absent): the bundle root's, or dir's (a directory in the bundle; §9 logs that scope). Link the concept it is about, `[title](/path.md)`, so `log` finds it. Kinds by convention: Update, Creation, Deprecation.

```sh
uv run KnowledgeBaseMCP.py record "Reviewed the runbooks against the new pipeline." bundle=eng
```

| Argument | Type | Default |
|---|---|---|
| `note` | `str` | required |
| `kind` | `str` | `'Update'` |
| `dir` | `str` | `''` |
| `bundle` | `str` | `''` |

## rename

Rename or move a bundle within the knowledgebase (§3): bundle= (default: where the user is) to `to`, a path in the knowledgebase. Links into it from other bundles, its links out, and §6.2 paths are rewritten (§6.1); its own `/` links stay, since its root moves with it. The knowledgebase index follows. apply=False shows the plan and diff.

```sh
uv run KnowledgeBaseMCP.py rename marketing bundle=mkt apply=true
```

| Argument | Type | Default |
|---|---|---|
| `to` | `str` | required |
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## search

Case-insensitive text search over concepts; each hit is {bundle, file, line, text}.

```sh
uv run KnowledgeBaseMCP.py search postgres format=text
```

| Argument | Type | Default |
|---|---|---|
| `query` | `str` | required |
| `limit` | `int` | `30` |
| `offset` | `int` | `0` |
| `bundle` | `str` | `''` |

## set

Edit frontmatter on one or many concepts by text; every other key stays byte for byte (§4.1). fields: {key: value}; null drops a key. Checks type, status (§5.4), stale_after (§5.5, ISO with a UTC offset) and tags (a list). generated, verified and sources have their own tools (provenance, verify, cite). apply=False shows the diff.

```sh
uv run KnowledgeBaseMCP.py set db.md status=deprecated tags=[db,ops] bundle=eng apply=true
```

| Argument | Type | Default |
|---|---|---|
| `fields` | `dict` | required |
| `file` | `str` | `''` |
| `files` | `Union` | `None` |
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## split

Make a directory its own bundle (§3): its index.md declares okf_version "0.2" (created if missing, with a generated list), a log.md is started, and `/` links and §6.2 paths inside it are rewritten for the new root (§6.1). Links that now cross between the two bundles are listed, not changed; lint warns on them. shortcut: links inside code blocks are rewritten too; read the diff.

```sh
uv run KnowledgeBaseMCP.py split notes apply=true
```

| Argument | Type | Default |
|---|---|---|
| `dir` | `str` | required |
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## status

Bundle summary: concepts by type, by status (absent = stable, §5.4), by trust tier (§5.3), stale count (`stale_after` passed, §5.5), unparseable files, declared okf_version, conformance and lint totals; and the upkeep queues, five oldest or largest each: review (days since last `verified`), drafts (days since `generated.at`), sources (concepts with and without), words (total, longest: split candidates), due (`stale_after` within due_days). At a knowledgebase root without bundle=, `bundles` holds the same for each bundle.

```sh
uv run KnowledgeBaseMCP.py status format=text
```

| Argument | Type | Default |
|---|---|---|
| `due_days` | `int` | `30` |
| `bundle` | `str` | `''` |

## unarchive

Put an archived concept or bundle back where it came from: path is its place in the archive, &lt;bundle&gt;/&lt;path&gt; for a concept (its bundle must exist) or &lt;bundle&gt; for a whole bundle. apply=False shows the plan and diff.

```sh
uv run KnowledgeBaseMCP.py unarchive eng/runbooks/old.md apply=true
```

| Argument | Type | Default |
|---|---|---|
| `path` | `str` | required |
| `apply` | `bool` | `False` |

## upgrade

OKF v0.1 to v0.2 (§13). A legacy `timestamp` becomes `generated: {by, at, basis: git-history}` with by from git history (`by` is required, so without history it stays and is listed in needs_by); a body `# Citations` list becomes `sources` entries and the list is removed; the root index.md declares okf_version "0.2". apply=False shows the diff.

```sh
uv run KnowledgeBaseMCP.py upgrade
uv run KnowledgeBaseMCP.py upgrade apply=true
```

| Argument | Type | Default |
|---|---|---|
| `apply` | `bool` | `False` |
| `bundle` | `str` | `''` |

## verify

Record a §5.2 `verified` entry {by, at} (at = now, UTC). Two paths: you (an agent or process) checked it: by=&lt;tool&gt;/&lt;version&gt; or process:&lt;id&gt;; the concept is machine-confirmed. A human checked it: omit `by`; the human gets a confirmation prompt and types their own id. Never pass human:&lt;id&gt; yourself. Present the concept to them first. At the terminal a human runs it with --attest. promote=true also moves a draft to stable (§5.4); only a human review may.

```sh
uv run KnowledgeBaseMCP.py verify db.md bundle=eng --attest promote=true
```

| Argument | Type | Default |
|---|---|---|
| `file` | `str` | required |
| `by` | `str` | `''` |
| `promote` | `bool` | `False` |
| `bundle` | `str` | `''` |

## web

The link graph (§6): which concepts link to (`link`) or cite (`cite`: sources and §6.2 path fields, lineage, §5.1) which. Where the user is, like lint: at the knowledgebase root, bundles with edges counted; in a bundle (or concepts=true), concepts. Broken links are left out (lint reports them); archived and deprecated nodes are marked. Returns {level, nodes, edges}; mermaid=true returns a Mermaid diagram instead (CLI: format=mermaid), which GitHub and most markdown viewers draw.

```sh
uv run KnowledgeBaseMCP.py web format=text
uv run KnowledgeBaseMCP.py web format=mermaid
```

| Argument | Type | Default |
|---|---|---|
| `concepts` | `bool` | `False` |
| `mermaid` | `bool` | `False` |
| `bundle` | `str` | `''` |
