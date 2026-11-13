# Changelog

## 1.0.1 (2026-11-13)

### Renamed
- The project is now **Bowerbird**. The PyPI package and the command are `bowerbird-mcp` (was
  `knowledgebasemcp`), the script is `bowerbird_mcp.py` (was `KnowledgeBaseMCP.py`), and the repository is
  `dfoulks1/bowerbird-mcp`. The settings files stay `kbmcp.yaml` and `kbmcp.nolint`. The model cache moved to
  `~/.cache/bowerbird-mcp/models`. The 1.0.0 release keeps its old names.
- The generated-index marker in `index.md` files still says "KnowledgeBaseMCP", so existing knowledgebases are
  not rewritten.
- A new logo (a bower of sticks rising from an open book), on the site, in the README and as the favicon, with a
  social-preview image for link cards.
- The install lines use the PyPI name (`uvx bowerbird-mcp`); the repository form is kept for unreleased code.
- The website moved to <https://bowerbird.voltpop.com/>.

### Changed
- `fastembed` is declared once, as a dependency of the package. It is no longer in the script's own header, so
  `uv run KnowledgeBaseMCP.py` (and a lint-only hook that runs the script) no longer installs it. `uvx
  knowledgebasemcp` still has semantic search out of the box; the bare script needs `--with fastembed` for
  `semantic: true`, and says so.

## 1.0.0 (2026-11-13)

The first release. It collects everything built since the project started (2026-10-27) and adds the
following in the last stretch.

### Added
- **Install in one line:** `uvx --from git+https://github.com/dfoulks1/KnowledgeBaseMCP knowledgebasemcp`.
  One command, `knowledgebasemcp`; the file still runs as a script (`uv run KnowledgeBaseMCP.py`).
- **`kbmcp.yaml`:** local settings at the root of a knowledgebase. It marks the base, tells any server where
  the knowledgebase and its assets are, and is kept out of git. `--config` names one elsewhere, and `config`
  writes a commented example (and ignores it in git). `lint` flags a second one below the root (`nested_config`).
- **`passages`:** the best sections of the knowledgebase for a question, ranked by BM25 (SQLite FTS5) in one index
  file, with file, line, a percent `match`, trust tier and staleness on each hit, and `gap: true` when
  nothing fits. Concepts many others link to rank a little higher. Optional semantic matching by meaning
  (`semantic: true`, fastembed; the model, about 65 MB, downloads once). `reindex` builds, inspects (`info`) or
  drops the index, so a hook can keep it current (`build: manual`).
- **Roles:** `read`, `write`, `structure` and `lifecycle` (`--role` or `KB_ROLE`, `roles:` in `kbmcp.yaml`)
  split the 35 tools into four servers of about 2,300 to 2,500 tokens each, instead of about 9,500 for all.
- **`lint` always ends with a verdict line** (and a GitHub notice), so a hook shows it ran.
- **`about:`** in `kbmcp.yaml` tells an agent what a knowledgebase holds, for when several are loaded.
- **Docs:** Getting started and Understanding OKF pages, the site at https://knowledgebasemcp.voltpop.com/,
  `NOTICE` (credits the copied OKF specification) and `SECURITY.md`.

### Changed
- **`KB_ROOT` is no longer read** (the server exits with a message). Use `kbmcp.yaml`, found from the
  working directory upward or named with `--config`.
- `init` and `create` print the "land it via a branch and PR" hint only inside a git work tree.

### Fixed
- `lint` raised a `KeyError` when a file with no frontmatter linked to a concept.

### Known limits
- `passages` has no stemming ("rolling" does not match "roll"), and with `build: manual` it does not notice
  files changed since the last `reindex`.
- `fastembed` and its dependencies add about 150 MB to the install even with semantic search off (1.0.0; from
  1.0.1 only the installed package carries it, not the bare script).
- A human `verify` over MCP needs a client that supports confirmation prompts.
