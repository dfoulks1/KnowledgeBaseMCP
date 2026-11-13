# Understanding OKF

!!! note "AI-generated"
    Written with Claude Opus 5.5 and Claude Sonnet 5.5, under human review. It explains the format in plain words and points at [the specification][okf] for the exact rules; where the two differ, the specification wins.

## What OKF is

**Open Knowledge Format** (OKF) is a way of writing down what you know so that people and AI assistants can both
use it. The whole format is this: **a folder of Markdown files, each starting with a short block of facts about
the file.** The specification calls that block *frontmatter* and writes it in YAML. That is the entire
technology. There is no database, no server, no registry of allowed types and no required software. In the
specification's own words: if you can `cat` a file you can read OKF, and if you can `git clone` a repository you
can ship it.

OKF is published as a specification (this site follows version 0.2) in the `knowledge-catalog` repository on
GitHub. Bowerbird is one tool that implements it: it writes, checks and searches OKF folders. Nothing in
the format depends on this tool, which is the point.

## Why a format at all?

A pile of Markdown notes is already easy to read. The trouble starts when the pile grows, other people add to it,
and AI assistants begin to *write* parts of it. Then readers need answers a plain note does not give:

1. **Where did this come from?** (provenance)
2. **Has anyone checked it, and was it a person or a script?** (trust)
3. **Is it still true?** (freshness)
4. **Is this the current version, or an old draft?** (lifecycle)

Without a convention, every team invents its own answers, and no tool can rely on them. OKF fixes a *small* set of
conventions for exactly these questions and leaves everything else to you.

## The pieces

### A concept

A **concept** is one Markdown file about one thing: a procedure, a database table, a metric, a decision, a
glossary term. Here is a complete one:

```markdown
---
type: Playbook
title: Deploy
description: How we ship a release.
tags: [ops]
sources:
  - id: runbook
    resource: https://example.com/runbook
    title: Ops runbook
verified: { by: human:ann, at: 2026-11-13T15:00:00Z }
status: stable
stale_after: 2027-05-13T00:00:00Z
---

# Deploy

Run the deploy script, then check the dashboard.[^runbook] If something looks
wrong, follow [the rollback steps](rollback.md).

[^runbook]: Ops runbook
```

The block between the two `---` lines is the **frontmatter**. Everything after it is ordinary Markdown: headings,
lists, tables, code. The spec asks writers to prefer structure (headings, lists, tables) over loose prose,
because structure helps both a reader skimming and an assistant retrieving.

### The header fields

Only one is required. `type` says what kind of thing the file is (`Playbook`, `Reference`, `Metric` and so on).
Types are not registered anywhere: pick words that explain themselves, and readers must cope with ones they have
not seen. A file with nothing but `type` is fully valid.

The others are recommended or optional, in three families:

| Family | Fields | Answers |
|---|---|---|
| **Describing** | `title`, `description` (one sentence), `tags`, `resource` (a URI for the thing it describes) | What is this, for indexes and search results |
| **Provenance and trust** | `sources` (what it was built from), `generated` (who or what wrote the current text, and when), `verified` (who confirmed it, and when) | Where it came from and how far to trust it |
| **Lifecycle** | `status` (`draft`, `stable`, `deprecated`; absent means stable), `stale_after` (a date after which the content counts as stale) | Is it current |

Every date is ISO 8601 with an explicit UTC offset, such as `2026-11-13T15:00:00Z`. Anything else you add is
yours: tools must keep keys they do not understand and must not reject a file for having them.

### Trust tiers

The tier is *derived*, never typed in. Look at who is in `verified`:

- nobody: **unverified**;
- only scripts, processes or agents: **machine-confirmed**;
- at least one person: **human-reviewed**.

Who is who is decided by a naming convention for **actors**: `human:<id>` for a person (`human:ann`),
`process:<id>` for an automated process (`process:finance-nightly`), and `<producer>/<version>` for an agent or
tool (`reference_agent/gemini-2.5-pro`). Because the tier keys off the `human:` prefix, anything a person wrote or
confirmed must use it. Two things to keep in mind: `generated` and `verified` are kept apart on purpose, because
who *wrote* a note need not be who *checked* it; and tiers are advisory labels, not access control.

### Links and citations

Concepts point at each other with ordinary Markdown links, either relative (`[the rollback steps](rollback.md)`)
or from the bundle root with a leading slash (`/runbooks/rollback.md`, which survives moving files around inside
a folder). A link says "these are related"; the sentence around it says how. A broken link is allowed by the
format: it may simply be knowledge nobody has written yet. (Bowerbird's `status` lists the pages that
links ask for and nobody has written.)

A **citation** is different: it records where a *fact* came from. It lives in `sources`, and the claim in the text
points at it with a Markdown footnote (`[^runbook]`). Links are for navigation, citations are for lineage.

### Bundles, `index.md` and `log.md`

A **bundle** is a folder of concepts, with subfolders as you like. Two filenames are reserved at any level:

- **`index.md`** lists what is in a folder, with each concept's one-line description, so a reader (or an
  assistant) can see what is available before opening anything. The spec calls this *progressive disclosure*. At
  the top of a bundle it may carry one frontmatter key, `okf_version`. OKF makes it optional; Bowerbird
  uses it to recognise a folder as a bundle. Tools may generate `index.md`, and Bowerbird's `index` does.
- **`log.md`** is the history of changes to that folder, newest first, grouped by date.

A bundle can travel as a git repository (recommended, for the history and the diffs), a zip, or a subfolder of a
bigger repository. The word **knowledgebase**, as this site uses it, is not part of OKF: it means a bundle, or a
folder of bundles, that Bowerbird manages together.

## Why it is good

These are the properties that follow from the format itself.

- **Readable with no tools.** It is text. Open a file, read it. If this project vanished tomorrow, you would keep
  every note, in a form any editor shows you. The way out of the format is "stop using the tool".
- **Diffable and reviewable.** Because it is plain text in a folder, git shows exactly what changed, who changed
  it and when, and a pull request can review a knowledge change like a code change.
- **Portable.** No schema registry or central authority, so a bundle moves between teams, tools and years
  without a conversion step.
- **Written for agents without a special SDK.** An assistant can read the files directly, and the structure
  (headings, a one-line description, tags, a type) is what a retrieval tool needs to cut a note into useful
  pieces and rank them.
- **Honest about trust.** Provenance, verification and freshness are part of the file, not a separate system.
  A reader, human or machine, can tell a checked fact from an unchecked one, and a current one from an expired
  one, *at the moment of reading*.
- **Minimal on purpose.** Only `type` is required, unknown fields are tolerated, and there is no fixed list of
  concept types. You can start with a few notes and add structure as you need it.

## What it does not do

It is worth being plain about the limits.

- **It does not check that anything is true.** `verified` records that someone or something *said* they checked.
  The format makes the claim visible; it cannot make it correct.
- **It does not control access.** Trust tiers and statuses are signals for readers, not permissions.
- **It is not a database or a search engine.** It prescribes no storage, serving or query system. Finding things
  is up to the tool you use on top.
- **It does not define your vocabulary.** Concept types, tags and structure are yours to choose and keep
  consistent. (`vocab` in Bowerbird lists what you actually use, so spellings do not drift.)
- **It will not replace domain schemas.** Where an asset already has a precise schema (an API description, a
  table definition), OKF points at it with `resource`; it does not copy it.

## Where Bowerbird fits

OKF is the format; Bowerbird is a way to keep a folder of it healthy. It cares how a concept is written,
never what it says:

- **`lint`** checks every file against the specification's conformance rules plus house rules (broken links,
  empty notes, orphans, duplicate titles, key-shaped secrets), and `fix` repairs the mechanical ones.
- **`index`** regenerates the tables of contents from the concepts' own descriptions.
- **`cite`, `verify`, `provenance`** write the provenance and trust fields correctly. A person's review is recorded
  only with that person's own confirmation (a prompt over MCP, or `--attest` at their terminal), never by an
  assistant on their behalf.
- **`passages`, `search`, `dirs`, `get`** find and read, and `passages` returns each section with its file, line,
  trust tier and staleness, so an answer can show its sources and say when it is on thin ice.
- **`status`** says what needs a person next: the oldest unreviewed notes, drafts, notes with no sources, what
  goes stale soon.

The practical effect is that a knowledgebase kept this way can answer a question *and* say how far to trust the
answer. That is the whole idea.

## Read on

- [Getting started](getting-started.md): build one in ten minutes.
- [The specification][okf]: the exact rules, including attested computations, which this page leaves out.
- [The guide](guide.md): layout, the archive, several bundles, CI and settings.

[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/bad9bdbafa82c672b00d437d4f2cc8f17e9e5f58/okf/SPEC.md
