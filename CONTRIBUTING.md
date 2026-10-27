# Contributing

KnowledgeBaseMCP is a personal project, Apache-2.0 licensed, built under the
[ASF generative-tooling guidelines][asf-gt]. AI assists; a human reviews before
anything public-facing ships.

## What it serves

Bundles in the [Open Knowledge Format][okf] (OKF). Everything a tool does is
also doable by hand (edit the file, run `lint`). The tools make it cheaper and
more consistent, not possible.

## How we build

One brief, then refinement. `prompts/rewrite-brief.md` is the current brief;
use cases drive changes to it. Core stays one file.

## ASF generative-tooling compliance

- ICLA §§4/5/7/8 and conditions 2.1–2.3 apply.
- Third-party licensing must allow Apache-2.0 output. No GPL or
  Apache-incompatible reproduced code.
- A human reviews AI-generated public-facing output before it ships; label it
  AI-generated if unreviewed.
- Provenance trailer on commits: the exact string your tool is configured
  with, confirmed before committing, never fabricated. For example:

  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```

## Running the checks

```sh
uv run KnowledgeBaseMCP.py lint     # exits 1 on problems; use as a pre-merge gate
uv run test_KnowledgeBaseMCP.py     # self-check against throwaway bundles
```

## Docs site

`docs-src/` is the source and `docs/` the built site, committed so GitHub Pages
serves it from `main` `/docs`. No CI builds it. After changing the README, a
tool or `docs-src/`, rebuild locally and commit both:

```sh
uv run docs_tools.py                          # docs-src/tools.md, from the tools' docstrings
uvx --with pymdown-extensions mkdocs build    # docs-src/ -> docs/
```

[asf-gt]: https://www.apache.org/legal/generative-tooling.html
[okf]: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
