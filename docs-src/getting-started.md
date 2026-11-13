# Getting started

!!! note "AI-generated"
    Written with Claude Opus 5.5 and Claude Sonnet 5.5, under human review. Every command on this page was run for real. Long output lines are shortened (marked `...`), and a few fields are left out where noted.

In about ten minutes you will have a small knowledgebase on your own disk, ask it a question and get an answer
with the file and line to cite, catch a mistake with the checker, record where a fact came from and who checked
it, and connect an AI assistant to it. You do not need to know anything about AI tooling to start, and nothing
here sends your notes anywhere.

## What this is, in plain words

A **knowledgebase** here is a folder of Markdown files, one idea per file. Each file starts with a short header
of facts about it: what kind of thing it is, a one-line description, where it came from, who checked it. The
file format is called [Open Knowledge Format](understanding-okf.md) (OKF), and it is deliberately plain: if you
can open a text file, you can read it, and if you use git, you can version it.

KnowledgeBaseMCP is the tool that looks after such a folder. It does three jobs, for three kinds of user:

- **A person at a terminal** can search the notes, check them, and keep them tidy. No AI involved.
- **An AI assistant** (through MCP, the protocol assistants use to call tools) can look things up in the notes
  and answer from them, saying which file and line it used and how far to trust it.
- **CI**, your automated checks, can fail a change that leaves the notes in a bad shape.

It cares about *how a note is written*, never about *what it says*. It will tell you a note has no header, a link
is broken or a fact has no source. It will not tell you the fact is wrong. That judgement stays with people.

## 1. Install uv

The tool runs through [uv](https://docs.astral.sh/uv/), a fast Python launcher. If you do not have it:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

There is nothing else to install and nothing to clone. This line runs the tool straight from its repository,
fetching what it needs the first time. Make a shortcut so the rest of this page is short:

```sh
alias kb='uvx --from git+https://github.com/dfoulks1/KnowledgeBaseMCP knowledgebasemcp'
kb help          # every tool, one line each (35 of them)
```

## 2. Make a knowledgebase

Make an empty folder and start a knowledgebase in it:

```sh
mkdir notes && cd notes
kb init apply=true format=text
```

Most commands that change files show you a plan first and only act when you add `apply=true`. Here is what
`init` wrote:

```text
edited: {".": ["index.md", "log.md"]}
gitattributes: ["log.md merge=union", "index.md merge=union"]
```

`index.md` is a generated table of contents for the folder, and `log.md` is its history, newest first. It also
made a `.gitattributes`, which lets two people who edit `log.md` and `index.md` on different branches merge
without a conflict. Now
write two notes. Each has a few real sentences, because a note with an empty body gives the search nothing to
find:

```sh
kb create deploy type=Playbook title="Deploy" description="How we ship a release." tags=ops \
   body='Run the deploy script, then check the dashboard. If something looks wrong, follow [the rollback steps](rollback.md).' format=text

kb create rollback type=Playbook title="Rollback" description="How to undo a bad release." tags=ops \
   body='To roll back a release, redeploy the previous tag, then confirm the dashboard is green. Back to [Deploy](deploy.md).' format=text
```

Open `deploy.md` in any editor. This is the whole file, and the whole format:

```markdown
---
type: Playbook
title: Deploy
description: How we ship a release.
tags:
- ops
---

# Deploy

Run the deploy script, then check the dashboard. If something looks wrong, follow [the rollback steps](rollback.md).
```

The part between the `---` lines is the header (OKF calls it *frontmatter*); the rest is ordinary Markdown. The
only header line OKF insists on is `type`. You can edit these files by hand at any time: the tool is a
convenience, not a gatekeeper.

## 3. Ask it a question

```sh
kb passages 'how do I undo a bad release' format=text
```

```text
total: 2
gap: false
hits:
  - bundle: ., file: rollback.md, line: 10, heading: Rollback, match: 100, title: Rollback, type: Playbook, status: stable, tier: unverified, stale: false, links: 1, text: To roll back a release, redeploy the previous tag, ...
  - bundle: ., file: deploy.md, line: 10, heading: Deploy, match: 58, title: Deploy, type: Playbook, status: stable, tier: unverified, stale: false, links: 1, text: Run the deploy script, then check the dashboard. ...
```

(`title`, `type`, `status` and `links`, the count of notes that link here, are in the real output too.) The first
search also builds a small search index in a `.kbmcp/` folder beside your notes. It is a cache: safe to delete,
and it ignores itself in git.

`passages` cuts every note into sections at its headings and returns the sections that best answer the
question, best first. For each one you get:

- **file and line**, so an answer can say exactly where it came from;
- **match**, a percentage of the *best hit's* score. The top hit is always 100, so read it as "how the others
  compare", not "how good the best one is";
- **tier** and **stale**, so a reader knows whether anyone has checked the passage and whether it has expired
  (section 5);
- **gap: true** when nothing matches at all. That is a real answer: the knowledgebase has nothing on the
  subject, and an assistant should say so, not guess.

Search is by words (rarer words count more), so "undo" finds the note whose description says "undo". It does not
know that "revert" means "undo". If you want that, [semantic search](guide.md#reading-the-knowledgebase) matches
by meaning, at the cost of a model download. Other ways in: `dirs` (a map of what is there), `search` (whole
notes by words), `get` (read one note) and `list` (filter by type, tag, status or trust).

## 4. Let it catch mistakes

```sh
kb lint format=text
```

```text
knowledgebasemcp lint: ok: 2 concept(s) in 1 bundle(s) checked, 0 finding(s), conformant: True
```

`lint` checks every file against the format and some house rules (broken links, empty notes, notes nothing links
to, duplicate titles, secrets that look like keys). It always ends with that one verdict line, pass or fail, so
you can see it ran. Now drop in a file with no header:

```sh
echo 'just some notes, no header' > scratch.md
kb lint format=text
```

```text
scratch.md: error: no_frontmatter: no frontmatter (§4) | fix: start the file with a `---` block holding at least `type:`
knowledgebasemcp lint: FAILED: 3 concept(s) in 1 bundle(s) checked, 1 finding(s), conformant: False
```

Every finding names the file, what is wrong and how to fix it, and the command exits with a failure code, which
is what makes it useful in CI. Some problems are purely mechanical (a stale table of contents, inconsistent tag
spelling), and `kb fix apply=true` repairs those for you. Delete `scratch.md` before going on.

## 5. Say where a fact came from, and who checked it

Notes get trusted too easily or not at all. OKF gives you two small, honest tools for that:

```sh
kb cite deploy.md resource=https://example.com/runbook title="Ops runbook" format=text
kb verify deploy.md by=process:docs-check format=text
```

`cite` records a source and prints a footnote tag, `[^runbook]`, to put next to the claim it backs. `verify`
records that someone or something confirmed the note, and when. Both write to the header:

```yaml
sources:
- id: runbook
  resource: https://example.com/runbook
  title: Ops runbook
  retrieved_at: 2026-11-13T15:49:32Z
verified:
- by: process:docs-check
  at: 2026-11-13T15:49:32Z
```

The trust tier comes only from who verified: nobody means **unverified**, a script or agent means
**machine-confirmed**, and a person (`human:<id>`) means **human-reviewed**. `passages` shows the tier on every
hit, and `kb list tier=unverified` finds what still needs a person. A person's review is recorded only with
that person's own confirmation (a prompt over MCP, or `--attest` at your terminal), never by an AI on your
behalf. These tiers are advisory labels, not access control. If
a note should expire, set `stale_after` in its header, and `passages` will flag it once the date passes.

## 6. Connect an AI assistant

First, give the knowledgebase a settings file. `kbmcp.yaml` sits at the root of the knowledgebase and is what
tells any server where it is:

```sh
kb config apply=true format=text
```

It writes a file where every setting is commented out at its default, and adds `kbmcp.yaml` to your
`.gitignore` if the folder is a git repository, because it is local to you. Uncomment `about:` and write a
sentence on what this knowledgebase holds. That matters most when you load several at once, because the
assistant is told it.

Then add the tool to your assistant's servers file (`.mcp.json` in your project for Claude Code; the same entry
works in `claude_desktop_config.json` for Claude Desktop and `.cursor/mcp.json` for Cursor):

```json
{
  "mcpServers": {
    "notes": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/dfoulks1/KnowledgeBaseMCP", "knowledgebasemcp",
               "--config", "/full/path/to/notes/kbmcp.yaml"]
    }
  }
}
```

Restart the assistant (in Claude Code, `/mcp` reconnects). It now has the tools and a short instruction on how to
use them: look at `dirs`, then `passages`, then `get` only what it needs, cite the file and line, and say so
when the answer is a gap or the passage is unverified or stale.

All 35 tools cost an assistant about 9,500 tokens of tool descriptions (an estimate: the length of each
description in characters, divided by four) before it has said a word. Give each
assistant only what it needs by adding `"--role", "read"` (find and read only, 10 tools, safe to auto-approve),
`write` (write a concept and check it), `structure` (reorganize) or `lifecycle` (keep it current). Each role is
about a quarter of the total. You can register the same
knowledgebase several times, one per role, and you can load several different knowledgebases side by side, each
with its own `--config`. [The guide](guide.md#roles-a-smaller-tool-list-per-agent) has the tool lists.

## 7. Keep it checked automatically

The easiest habit is a check on every commit. With [pre-commit](https://pre-commit.com/), add this to
`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: okf-lint
        name: OKF lint
        entry: uvx --from git+https://github.com/dfoulks1/KnowledgeBaseMCP knowledgebasemcp lint format=text
        language: system
        pass_filenames: false
        verbose: true
```

`verbose: true` is what makes pre-commit print the verdict line even when the check passes. For pull requests,
`lint` can also write GitHub annotations or SARIF, keep a baseline so only new problems fail the build, and check
only what changed: see [the guide](guide.md#ci).

## If something goes wrong

- **`KB_ROOT is no longer read`**: the old environment variable is gone. Put the folder's `kbmcp.yaml` where the
  tool runs, or name it with `--config`.
- **`uvx` runs an old build while you test local changes**: add `--no-cache`.
- **`passages` says `gap: true` for something you know is there**: search is by words and has no stemming, so
  "rolling" does not match "roll". Try the note's own words, or turn on semantic search.
- **A note exists but `passages` cannot find it**: it may be an empty stub. `lint` warns about notes with almost
  no body.

## Where next

- [Understanding OKF](understanding-okf.md): what the format is and why it is built this way.
- [The guide](guide.md): layout, the archive, several bundles, CI, and every setting in `kbmcp.yaml`.
- [Tools](tools.md): every command, with its arguments and examples.
