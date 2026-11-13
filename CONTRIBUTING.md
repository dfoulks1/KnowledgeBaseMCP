# Contributing

KnowledgeBaseMCP is a personal project, Apache-2.0 licensed, built under the
[ASF generative-tooling guidelines][asf-gt]. AI assists; a human reviews before
anything public-facing ships.

## Feedback

Bugs, ideas and OKF edge cases: [GitHub Issues](https://github.com/dfoulks1/KnowledgeBaseMCP/issues). Doc fixes are welcome too.
Security problems: see [SECURITY.md](https://github.com/dfoulks1/KnowledgeBaseMCP/blob/main/SECURITY.md), and please do not open a public issue for them.

## What it serves

Bundles in the [Open Knowledge Format][okf] (OKF). Everything a tool does is
also doable by hand (edit the file, run `lint`). The tools make it cheaper and
more consistent, not possible.

## How we build

One brief, then refinement. [`docs-src/prompts/rewrite-brief.md`](https://github.com/dfoulks1/KnowledgeBaseMCP/blob/main/docs-src/prompts/rewrite-brief.md) is the current brief (AI source
material kept in the repository, not on the website; a draft in the beta process);
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

## Releasing

1. Set `version` in `pyproject.toml`, add a section to `CHANGELOG.md`, and run the checks above (the tests
   run on Python 3.10 to 3.14: `uv run --python 3.10 test_KnowledgeBaseMCP.py`).
2. Rebuild the docs site (below) and commit. Merge to `main`.
3. Tag and publish a GitHub release, `git tag -a vX.Y.Z` then `gh release create vX.Y.Z`, with the
   `CHANGELOG.md` section as the notes. Publishing the release runs `.github/workflows/publish.yml`, which
   tests, builds and uploads to PyPI. The workflow refuses a tag that does not match `version`.

PyPI uses *trusted publishing*, so no token is stored anywhere. One-time setup, by the project owner:
create the project's pending publisher at https://pypi.org/manage/account/publishing/ with owner
`dfoulks1`, repository `KnowledgeBaseMCP`, workflow `publish.yml` and environment `pypi`, and create a
GitHub environment named `pypi` (Settings, Environments), ideally with the owner as a required reviewer
so each upload waits for approval. To try it first, `uv publish --publish-url https://test.pypi.org/legacy/`
uploads the files from `uv build` to TestPyPI.

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
