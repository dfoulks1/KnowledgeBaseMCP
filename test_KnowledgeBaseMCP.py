#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.10,<2", "pyyaml"]
# ///
"""Self-check: throwaway bundles, every tool. Run: uv run test_KnowledgeBaseMCP.py"""
import asyncio
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
kb = Path(tempfile.mkdtemp()) / "kb"
kb.mkdir()
os.environ.update(KB_ROOT=str(kb), GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
sys.path.insert(0, str(HERE))
import KnowledgeBaseMCP as k

TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def kinds(**kw):
    return {f["kind"] for f in k.lint(limit=0, **kw)["findings"]}


def raises(fn, *a, **kw):
    try:
        out = fn(*a, **kw)
        if asyncio.iscoroutine(out):
            asyncio.run(out)
    except ValueError as e:
        return str(e)
    raise SystemExit(f"{fn.__name__} did not refuse")


def cli(*argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        code = k.cli(list(argv))
    k.CLI = False
    return code, buf.getvalue()


# init: a new bundle is conformant and clean; a second init refuses.
assert k.init()["would_edit"] == ["index.md", "log.md"]
k.init(apply=True)
assert k.lint()["ok"] and k.lint()["conformant"], k.lint()
raises(k.init, apply=True)

# A bundle with only a concept lints (no index, no log, no layout).
(kb / "bare").mkdir()
(kb / "bare/a.md").write_text("---\ntype: Note\n---\nhi\n")
assert k.lint(bundle="bare")["ok"]

# SPEC.md's own examples: conformant, no okf errors. Their /tables/... links are dead here (house).
spec = (HERE / "SPEC.md").read_text()
blocks = re.findall(r"```markdown\n(.*?)```", spec, re.DOTALL)
(kb / "spec").mkdir()
for i, b in enumerate(x for x in blocks if x.startswith("---\n")):
    (kb / f"spec/ex{i}.md").write_text(b)
(kb / "spec/log.md").write_text(next(b for b in blocks if b.startswith("# Directory Update Log")))
assert len(list((kb / "spec").glob("ex*.md"))) >= 6
L = k.lint(scope="okf", bundle="spec", limit=0)
assert L["ok"] and L["conformant"], L
assert "dead_link" in kinds(bundle="spec")  # §6.1: / is the bundle root, and is checked
shutil.rmtree(kb / "spec")
shutil.rmtree(kb / "bare")

# One bad fixture per check.
(kb / "bad").mkdir()


def check(text, kind, name="x.md"):
    p = kb / "bad" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text) if isinstance(text, bytes) else p.write_text(text)
    got = kinds(bundle="bad")
    p.unlink()
    assert kind in got, (kind, got)


check("no frontmatter\n", "no_frontmatter")
check("---\na: b: c\n---\n", "bad_yaml")
check("---\ntype: x\nunclosed\n", "bad_yaml")
check("---\ntitle: x\n---\n", "no_type")
check(b"---\ntype: x\n---\n\xff\n", "non_utf8")
check("---\ntype: x\ngenerated: {by: drew}\n---\n", "okf_trust")
check("---\ntype: x\nverified: {by: human:a, at: 2026-10-27}\n---\n", "okf_trust")  # no UTC offset
check("---\ntype: x\nstatus: done\n---\n", "bad_status")
check("---\ntype: x\nstale_after: soon\n---\n", "bad_stale_after")
check("---\ntype: x\nsources:\n  - id: a\n---\n", "bad_source")
check("---\ntype: x\nsources: [{id: a, resource: r}, {id: a, resource: s}]\n---\n", "bad_source")
check("---\ntype: x\nsources: [{id: a, resource: r}]\n---\nclaim[^b]\n\n[^b]: x\n", "unknown_footnote")
check("---\ntype: x\n---\n[a](/nope.md) [b](./nope.md)\n", "dead_link")
check("---\ntitle: x\n---\n# I\n", "okf_index", "sub/index.md")
check("# Log\n\n## Recent\n", "okf_log", "log.md")
check("# Log\n\n## 2026-01-01\n\n## 2026-02-01\n", "okf_log", "log.md")
check("---\nokf_version: '9.9'\n---\n", "okf_version", "index.md")
check("---\ntype: x\n---\n", "odd_filename", "a b.md")
check("---\ntype: x\n---\n", "no_description")
check("---\ntype: x\n---\n", "orphan")
check("---\ntype: Attested Computation\n---\n", "bad_computation")
check("---\ntype: x\n---\n# Real\n\n[a](#nope)\n", "dead_anchor")
check("---\ntype: x\ntags: [Sales, sales]\n---\n", "tag_case")
check("---\ntype: x\ngenerated: {by: human:a, at: '2026-01-01T00:00:00Z'}\n"
      "sources: [{id: s, resource: r, last_modified: '2026-02-01T00:00:00Z'}]\n---\n", "source_changed")
(kb / "bad/dep.md").write_text("---\ntype: x\nstatus: deprecated\n---\n")
check("---\ntype: x\n---\n[o](dep.md)\n", "deprecated_link")
(kb / "bad/dep.md").unlink()
(kb / "bad/y.md").write_text("---\ntype: x\n---\n# Real Thing\n\n[a](#real-thing)\n")
assert "dead_anchor" not in kinds(bundle="bad")
(kb / "bad/y.md").unlink()
assert not kinds(bundle="bad")
(kb / "bad/e.md").write_text("---\ntype: x\n---")  # closing --- at end of file, no newline
assert k.lint(bundle="bad")["ok"] and "bad_yaml" not in kinds(bundle="bad")
(kb / "bad/e.md").unlink()
(kb / "bad/w.md").write_text("---\ntype: x\n---\n")
(kb / "bad/W.md").write_text("---\ntype: x\n---\n")
if not (kb / "bad/w.md").samefile(kb / "bad/W.md"):  # case-sensitive file system
    assert "case_collision" in kinds(bundle="bad") and k.lint(bundle="bad")["ok"]  # warnings do not fail
for p in (kb / "bad").glob("*.md"):
    p.unlink()

# baseline: old findings stop counting, new ones still fail.
(kb / "bad/old.md").write_text("no frontmatter\n")
assert not k.lint(bundle="bad")["ok"]
k.baseline(apply=True, bundle="bad")
assert k.lint(bundle="bad", baseline=".okf-baseline.json")["ok"]
(kb / "bad/new.md").write_text("no frontmatter either\n")
L = k.lint(bundle="bad", baseline=".okf-baseline.json")
assert not L["ok"] and L["total"] == 1 and L["baselined"] == 1
shutil.rmtree(kb / "bad")

# fix: strips sub-index frontmatter, rebuilds the root list, re-lints; idempotent.
(kb / "note.md").write_text("---\ntype: Note\ntitle: Note\ndescription: A note.\ncustom: {a: [1, 2]}  # mine\n---\n"
                            "\n# Note\n\nBody.\n")
(kb / "sub").mkdir()
(kb / "sub/index.md").write_text("---\ntitle: Sub\n---\n# Sub\n")
assert {"okf_index", "index_stale"} <= kinds()
assert set(k.fix()["would_edit"]) == {"index.md", "sub/index.md"}
out = k.fix(apply=True)
assert out["remaining"]["ok"], out
assert k.fix()["would_edit"] == []
assert "(./note.md)" in (kb / "index.md").read_text() and (kb / "sub/index.md").read_text() == "# Sub\n"
assert "Ran fix" in (kb / "log.md").read_text()

# set: text-level edits keep other lines byte for byte; CRLF and BOM survive; bad values refused.
raises(k.set_, {"status": "done"}, file="note.md")
raises(k.set_, {"verified": []}, file="note.md")
assert "+status: draft" in k.set_({"status": "draft"}, file="note.md")["diff"]
k.set_({"status": "draft", "tags": ["a", "b"]}, file="note.md", apply=True)
t = (kb / "note.md").read_text()
assert "custom: {a: [1, 2]}  # mine\n" in t and "status: draft\n" in t
k.set_({"status": None}, file="note", apply=True)
assert "status:" not in (kb / "note.md").read_text()
(kb / "crlf.md").write_bytes(b"\xef\xbb\xbf---\r\ntype: Note\r\n---\r\nx\r\n")
k.set_({"title": "C"}, file="crlf.md", apply=True)
raw = (kb / "crlf.md").read_bytes()
assert raw.startswith(b"\xef\xbb\xbf---\r\n") and b"title: C\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")

# verify: machine path; human: refused from an agent; elicitation path; changed body refused.
asyncio.run(k.verify("note.md", by="claude-code/claude-opus-5-5"))
d = k.meta((kb / "note.md").read_text())[0]
assert d["verified"][0]["by"] == "claude-code/claude-opus-5-5" and TS.fullmatch(d["verified"][0]["at"])
assert k.trust_tier(d) == "machine-confirmed"
assert "only a human" in raises(k.verify, "note.md", by="human:drew")
raises(k.verify, "note.md", by="drew")


class Ctx:
    def __init__(self, action="accept", reviewer="tester", edit=None):
        self.action, self.reviewer, self.edit = action, reviewer, edit

    async def elicit(self, message, schema):
        assert "note.md" in message
        if self.edit:
            self.edit()
        return SimpleNamespace(action=self.action, data=SimpleNamespace(confirm=True, reviewer=self.reviewer))


assert asyncio.run(k.verify("note.md", ctx=Ctx("decline")))["edited"] == []
assert asyncio.run(k.verify("note.md", ctx=Ctx()))["tier"] == "human-reviewed"
d = k.meta((kb / "note.md").read_text())[0]
assert [e["by"] for e in d["verified"]] == ["claude-code/claude-opus-5-5", "human:tester"]
edit = lambda: (kb / "note.md").write_text((kb / "note.md").read_text() + "\nmore\n")
assert "changed" in raises(k.verify, "note.md", ctx=Ctx(edit=edit))
assert cli("verify", "file=note.md", "by=human:drew")[0] == 0  # a human at the terminal

# cite / recheck: a recorded MCP call is the source and the re-check recipe.
(kb / ".mcp.json").write_text(json.dumps({"mcpServers": {"jira": {"command": "x", "env": {"TOKEN": "secret"}}}}))
raises(k.cite, "note.md", server="nope", tool="get_issue")
c = k.cite("note.md", server="jira", tool="get_issue", args={"issue_key": "INFRA-1"}, observed="Open",
           title="INFRA-1 status", by="claude-code/claude-opus-5-5", stale_days=30)
assert c["footnote"] == "[^infra-1]"
(kb / "note.md").write_text((kb / "note.md").read_text().replace("Body.", "The ticket is open.[^infra-1]"))
d = k.meta((kb / "note.md").read_text())[0]
assert d["sources"][0]["resource"] == "mcp://jira/get_issue?issue_key=INFRA-1" and TS.fullmatch(d["stale_after"])
assert k.lint()["ok"], k.lint()
plan = k.recheck_plan()
assert plan["calls"][0]["call"] == {"server": "jira", "tool": "get_issue", "args": {"issue_key": "INFRA-1"}}
assert k.recheck_plan(older_than_days=1)["calls"] == []
r = k.recheck_apply([{"file": "note.md", "id": "infra-1", "observed": "Open"}])
assert r[0]["result"] == "unchanged"
r = k.recheck_apply([{"file": "note.md", "id": "infra-1", "observed": "Closed"}])
assert r[0]["result"] == "changed" and "The ticket is open" in r[0]["review"][0]
assert "secret" not in json.dumps(k.lint(limit=0))
k.cite("note.md", resource="https://example.com/page", title="Page")
assert k.lint()["ok"]

# Read tools.
st = k.status()
assert st["by_tier"]["human-reviewed"] == 1 and st["by_status"]["stable"] >= 1 and st["okf_version"] == "0.2"
assert st["conformant"]
assert [x["id"] for x in k.list_(tier="human-reviewed")["concepts"]] == ["note"]
(kb / "other.md").write_text("---\ntype: Note\n---\nSee [the note](/note.md).\n")
k.index(apply=True)
assert k.links("note.md")["in"] == ["other.md"] and k.links("other.md")["out"][0]["exists"]
assert k.search("ticket")["total"] == 1
assert k.get("note.md", limit=1)["text"] == "---\n"
assert [f["file"] for f in k.get(files=["note.md", "other.md"])["files"]] == ["note.md", "other.md"]

# create, move, log, per-directory indexes.
k.create("guides/howto", "Playbook", description="How to.", tags=["ops"], status="draft", body="Step one.",
         by="claude-code/claude-opus-5-5")
t = (kb / "guides/howto.md").read_text()
d = k.meta(t)[0]
assert d["type"] == "Playbook" and d["generated"]["by"] == "claude-code/claude-opus-5-5" and "# howto\n\nStep one." in t
raises(k.create, "guides/howto", "Playbook")
raises(k.create, "x", " ")
raises(k.create, "index", "Note")
(kb / "guides/ref.md").write_text("---\ntype: Note\ndescription: r.\n---\n"
                                  "See [how](howto.md#howto), [note](../note.md) and [abs](/note.md).\n")
assert "playbooks/howto.md" in k.move("guides/howto.md", "playbooks/howto.md")["would_edit"]
k.move("guides/howto.md", "playbooks/howto.md", apply=True)
assert (kb / "playbooks/howto.md").exists() and not (kb / "guides/howto.md").exists()
assert "](../playbooks/howto.md#howto)" in (kb / "guides/ref.md").read_text()
k.move("guides/ref", "a/b/ref", apply=True)
t = (kb / "a/b/ref.md").read_text()
assert "](../../playbooks/howto.md#howto)" in t and "](../../note.md)" in t and "](/note.md)" in t
k.log("Reviewed the guides.")
assert "* **Update**: Reviewed the guides." in (kb / "log.md").read_text()
raises(k.log, "two\nlines")
k.index(dirs=True, apply=True)
assert "(ref.md)" in (kb / "a/b/index.md").read_text() and "[b](b/)" in (kb / "a/index.md").read_text()
assert k.lint()["ok"] and "index_stale" not in kinds() and "dead_anchor" not in kinds()

# migrate (v0.1): Citations become sources; timestamp needs git for `by`.
(kb / "old").mkdir()
(kb / "old/index.md").write_text("# Old\n")
(kb / "old/m.md").write_text("---\ntype: Metric\ntimestamp: '2026-05-28T22:53:05+00:00'\n---\n# M\n\nText.\n\n"
                             "# Citations\n- https://wiki.acme/fpa-handbook\n- [Policy](https://wiki.acme/policy)\n")
out = k.migrate(apply=True, bundle="old")
assert out["needs_by"] == ["m.md"]
d = k.meta((kb / "old/m.md").read_text())[0]
assert [e["id"] for e in d["sources"]] == ["fpa-handbook", "policy"] and d["sources"][1]["title"] == "Policy"
assert "# Citations" not in (kb / "old/m.md").read_text() and "timestamp" in d
assert k.meta((kb / "old/index.md").read_text())[0]["okf_version"] == "0.2"
assert k.lint(bundle="old", scope="okf")["ok"] and k.migrate(bundle="old")["would_edit"] == []
assert {b["bundle"] for b in k.bundles()["bundles"]} == {".", "old"}
shutil.rmtree(kb / "old")

# The spec as an MCP resource.
assert "okf://spec" in {str(x.uri) for x in asyncio.run(k.mcp.list_resources())}
assert k.spec().startswith("# Open Knowledge Format")

# verify promote: only a human review moves draft to stable.
k.create("promo", "Note", description="P.", status="draft")
assert "only a human" in raises(k.verify, "promo.md", by="claude/x", promote=True)
assert cli("verify", "file=promo.md", "by=human:drew", "promote=true")[0] == 0
assert k.meta((kb / "promo.md").read_text())[0]["status"] == "stable"

# fix normalizes tag case to the most common spelling.
(kb / "tags").mkdir()
for n, tg in (("a", "Sales"), ("b", "Sales"), ("c", "sales")):
    (kb / f"tags/{n}.md").write_text(f"---\ntype: x\ndescription: d.\ntags: [{tg}]\n---\n")
assert "tag_case" in kinds(bundle="tags")
k.fix(apply=True, bundle="tags")
assert "tag_case" not in kinds(bundle="tags") and k.meta((kb / "tags/c.md").read_text())[0]["tags"] == ["Sales"]
shutil.rmtree(kb / "tags")

# Bundles in a knowledgebase: a nested bundle is its own; lint follows where the user is.
k.init(apply=True, bundle="child")
(kb / "child/sub").mkdir()
(kb / "child/sub/c.md").write_text("---\ntype: x\ndescription: c.\n---\nno link out\n")
k.index(apply=True, bundle="child")
(kb / "other.md").write_text((kb / "other.md").read_text() + "\nAlso [c](child/sub/c.md).\n")
assert "okf_index" not in kinds(bundle=".", all=False) and "cross_bundle" in kinds(bundle=".", all=False)
assert not any(f["file"].startswith("child/") for f in k.lint(bundle=".", all=False, limit=0)["findings"])
cwd = os.getcwd()
os.chdir(kb / "child/sub")
L = k.lint(limit=0)
assert set(L["bundles"]) == {"."} and {f["file"] for f in L["findings"]} == {"sub/c.md"}, L
os.chdir(kb)
L = k.lint(limit=0)
assert set(L["bundles"]) == {".", "child"} and any(f["file"] == "child/sub/c.md" for f in L["findings"])
assert L["ok"], L
L = k.lint(file="child/sub/c.md", limit=0)
assert {f["file"] for f in L["findings"]} == {"child/sub/c.md"}
assert {f["file"] for f in k.lint(files=["child"], limit=0)["findings"]} == {"child/sub/c.md"}
code, out = cli("lint", "child/sub/c.md", "format=text")
assert code == 0 and out.startswith("child/sub/c.md: warning: orphan")
raises(k.lint, file="nope.md")
os.chdir(cwd)
(kb / "other.md").write_text((kb / "other.md").read_text().replace("\nAlso [c](child/sub/c.md).\n", ""))
shutil.rmtree(kb / "child")

# split: a directory becomes its own bundle; / links inside are rewritten for the new root.
(kb / "area").mkdir()
(kb / "area/y.md").write_text("---\ntype: x\ndescription: y.\n---\n")
(kb / "area/x.md").write_text("---\ntype: x\ndescription: x.\n---\n[n](/note.md) [y](/area/y.md)\n")
out = k.split_off("area", apply=True)
t = (kb / "area/x.md").read_text()
assert "[n](../note.md)" in t and "[y](/y.md)" in t and out["crossing"]["count"] == 1
assert k.declares(kb / "area/index.md") and (kb / "area/log.md").exists()
assert k.lint(bundle="area")["ok"] and "(./area/x.md)" not in (kb / "index.md").read_text()
shutil.rmtree(kb / "area")
k.index(apply=True)

# CLI: exit codes and CI formats.
assert cli("lint")[0] == 0
(kb / "bad").mkdir()
(kb / "bad/x.md").write_text("no frontmatter\n")
code, out = cli("lint", "bundle=bad", "format=github")
assert code == 1 and out.startswith("::error file=")
code, out = cli("lint", "bundle=bad", "format=sarif")
assert code == 1 and json.loads(out)["runs"][0]["results"]
assert cli("lint", "nonsense=1")[0] == 2
assert cli("fix", "bundle=bad")[0] == 0
assert cli("help")[0] == 0
shutil.rmtree(kb / "bad")

# MCP surface: annotations, and the context parameter is not a tool argument.
tools = {t.name: t for t in asyncio.run(k.mcp.list_tools())}
assert tools["lint"].annotations.readOnlyHint and not tools["fix"].annotations.readOnlyHint
assert "ctx" not in tools["verify"].inputSchema["properties"]

# Git: history, provenance, ingest (copy, then in place).
src = kb / "src"
(src / "docs").mkdir(parents=True)


def g(*a):
    subprocess.run(["git", "-c", "commit.gpgsign=false", *a], cwd=src, check=True, capture_output=True)


g("init", "-q")
g("config", "user.name", "Ann")
g("config", "user.email", "ann@example.com")
(src / "docs/guide.md").write_text("# Guide\n\nHow to do it. [home](../index.md) ![i](../img.png)\n")
(src / "README.md").write_text("# Readme\n\nSee [g](/docs/guide.md).\n")
(src / "index.md").write_text("---\ntitle: Home\n---\n# Home\n")
(src / "img.png").write_bytes(b"\x89PNG")
g("add", ".")
g("commit", "-qm", "init")
(src / "docs/guide.md").write_text("---\ntags: [x]\n---\n# Guide\n\nHow to do it. [home](../index.md) ![i](../img.png)\n")  # frontmatter only
g("-c", "user.name=Bob", "commit", "-qam", "tags")
(src / "README.md").write_text("# Readme\n\nSee [g](/docs/guide.md). Updated.\n")
g("commit", "-qam", "edit\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
(src / "bot.md").write_text("# Bot\n\nBumped.\n")
g("add", "bot.md")
g("-c", "user.name=dependabot[bot]", "-c", "user.email=49699333+dependabot[bot]@users.noreply.github.com",
  "commit", "-qm", "bot")
g("remote", "add", "origin", "https://user:tok@github.com/o/r.git")

h = k.history(src, [src / "docs/guide.md", src / "README.md", src / "bot.md"])
assert h[src / "docs/guide.md"]["by"] == "human:ann@example.com"  # Bob's frontmatter edit does not count
assert h[src / "README.md"]["by"] == "claude/claude-opus-5.5"
assert h[src / "bot.md"]["by"] == "process:dependabot"
assert k.provenance(bundle="src")["would_edit"] == ["docs/guide.md"]

plan = k.ingest("src", bundle="imported", rules={"docs/*": "Guide"})
assert plan["ingest"] == 4 and plan["skipped"] == {"not markdown": 1}, plan
assert {i["to"] for i in plan["items"]} == {"docs/guide.md", "README.md", "src-index.md", "bot.md"}
assert plan["absolute_links"]["count"] == 1 and plan["provenance"] == {"full": 4}
assert plan["links_after_ingest"]["count"] == 2, plan["links_after_ingest"]
k.ingest("src", bundle="imported", rules={"docs/*": "Guide"}, apply=True)
d = k.meta((kb / "imported/docs/guide.md").read_text())[0]
assert d["type"] == "Guide" and d["status"] == "draft" and d["tags"] == ["x"]
assert d["generated"] == {"by": "human:ann@example.com", "at": d["generated"]["at"], "basis": "git-history"}
assert d["sources"][0]["resource"].startswith("https://github.com/o/r/blob/") and "tok" not in json.dumps(d)
assert k.lint(bundle="imported", scope="okf")["ok"]
assert k.ingest("src", bundle="imported")["ingest"] == 0  # re-run is a no-op
assert "source_changed" not in kinds(bundle="imported")
m = k.ingest("imported", bundle="merged", keep_okf=True, apply=True)  # merge an OKF bundle as is
assert m["ingest"] == 4 and (kb / "merged/docs/guide.md").read_text() == (kb / "imported/docs/guide.md").read_text()
assert k.ingest("imported", bundle="merged", keep_okf=True)["ingest"] == 0

(src / "dirty.md").write_text("x\n")
assert "clean git tree" in raises(k.ingest, "src", bundle="src", apply=True)
(src / "dirty.md").unlink()
assert k.ingest("src", bundle="src", apply=True)["links_after_ingest"]["count"] == 1
assert not (src / "index.md").exists() and (src / "src-index.md").exists()
assert k.lint(bundle="src", scope="okf")["ok"] and k.ingest("src", bundle="src")["ingest"] == 0

# lint since: only files changed since a ref (committed, unstaged or untracked) count.
g("add", "-A")
g("commit", "-qm", "okf")
(src / "new.md").write_text("no frontmatter\n")
L = k.lint(bundle="src", since="HEAD", limit=0)
assert {f["file"] for f in L["findings"]} == {"new.md"} and not L["ok"]
assert k.lint(bundle="src", since="HEAD~1", limit=0)["total"] > L["total"]
assert "unknown ref" in raises(k.lint, bundle="src", since="nope")
assert "git work tree" in raises(k.lint, since="HEAD")
(src / "new.md").unlink()

subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{src}", str(kb / "shallow")], check=True,
               capture_output=True)
assert "shallow" in raises(k.provenance, bundle="shallow")

print("ok")
