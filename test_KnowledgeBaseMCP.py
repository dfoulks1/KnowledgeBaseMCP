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
    k.CLI, k.ATTEST = False, ""
    return code, buf.getvalue()


# init: a new bundle is conformant and clean; a second init refuses.
assert k.init()["would_edit"] == {".": ["index.md", "log.md"]}
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
check("# Log\n\n## 2026-02-01\n\n* a\n\n## 2026-02-01\n\n* b\n", "okf_log", "log.md")  # after a union merge
assert k.tidied("# Log\n\n## 2026-01-01\n\n* <!-- 1 --> old\n\n## 2026-02-01\n\n* <!-- 5 --> x\n\n"
                "## 2026-02-01\n\n* <!-- 9 --> y\n* <!-- 5 --> x\n") == (
    "# Log\n\n## 2026-02-01\n\n* <!-- 9 --> y\n* <!-- 5 --> x\n\n## 2026-01-01\n\n* <!-- 1 --> old\n")
check("---\nokf_version: '9.9'\n---\n", "okf_version", "index.md")
check("---\ntype: x\n---\n", "odd_filename", "a b.md")
check("---\ntype: x\n---\n", "no_description")
check("---\ntype: x\n---\n", "orphan")
check("---\ntype: Attested Computation\n---\n", "bad_computation")
check("---\ntype: x\n---\n# Real\n\n[a](#nope)\n", "dead_anchor")
check("---\ntype: x\ntags: [Sales, sales]\n---\n", "tag_case")
check("---\ntype: x\ncomputation: nope/x.sql\n---\n", "dead_path")
check("---\ntype: x\ngenerated: {by: human:a, at: '2026-01-01T00:00:00Z'}\n"
      "sources: [{id: s, resource: r, last_modified: '2026-02-01T00:00:00Z'}]\n---\n", "source_changed")
check("---\ntype: x\nsources: [{resource: r, last_modified: yesterday}]\n---\n", "bad_source")  # §5.1 signals
check("---\ntype: x\nsources: [{resource: r, usage_count: many}]\n---\n", "bad_source")
check("---\ntype: x\nusage_window: {from: 2026-06-01}\nsources: [{resource: r}]\n---\n", "bad_source")
check("---\ntype: x\ntags: sales\n---\n", "bad_tags")
check("---\ntype: x\n---\nkey: AKIAIOSFODNN7EXAMPLE\n", "secret")  # AWS's documented example key
check("---\ntype: x\n---\n-----BEGIN OPENSSH PRIVATE KEY-----\n", "secret")
check("---\ntype: x\n---\npostgres://app:hunter2@db/prod\n", "secret")
assert k.secrets("tok ghp_" + "a" * 36 + "\nfine\n") == [(1, "GitHub token")]
assert not k.secrets("see https://example.com/a and ghp_short and sk-tiny\n")
(kb / "bad/leak.md").write_text("---\ntype: x\n---\nkey: AKIAIOSFODNN7EXAMPLE\n")
L = k.lint(bundle="bad", limit=0)
assert not L["ok"] and "AKIAIOSFODNN7EXAMPLE" not in json.dumps(L)  # named by kind and line, never the value
(kb / "bad/leak.md").unlink()
sec = Path(tempfile.mkdtemp())  # ingest leaves a file with a credential behind, and says why
(sec / "ok.md").write_text("# Fine\n")
(sec / "leak.md").write_text("# Leak\n\ntoken: glpat-" + "x" * 20 + "\n")
plan = k.ingest(str(sec), bundle="bad")
assert plan["ingest"] == 1 and plan["secrets"]["skipped"] == 1
assert any(f["file"] == "leak.md" and "GitLab token on line 3" in f["reason"] for f in plan["skipped_files"])
for c in ("parameters: [{name: year}]", "executor: {receipt: [job_id]}", "computation: x.sql\n---\n# Computation\n"):
    check(f"---\ntype: Attested Computation\nruntime: bigquery\n{c}" + ("" if "---" in c else "\n---\n# Computation\n"),
          "bad_computation")
check("---\ntype: x\ntimestamp: '2026-01-01T00:00:00Z'\n"  # §13.1: timestamp stands in for generated.at
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
assert set(k.fix()["would_edit"]["."]) == {"index.md", "sub/index.md"}
out = k.fix(apply=True)
assert out["remaining"]["ok"], out
assert k.fix()["would_edit"] == {}
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
os.environ["KB_USER"] = "drew"
assert cli("verify", "file=note.md", "--attest")[0] == 0  # a human at the terminal
assert k.meta((kb / "note.md").read_text())[0]["verified"][-1]["by"] == "human:drew"
assert cli("verify", "file=note.md", "by=human:drew")[0] == 2 and cli("lint", "--attest")[0] == 2
assert "only a human" in raises(k.recheck_apply, file="note.md", id="x", by="human:drew")

# cite / recheck: a recorded MCP call is the source and the re-check recipe.
(kb / ".mcp.json").write_text(json.dumps({"mcpServers": {"jira": {"command": "x", "env": {"TOKEN": "secret"}}}}))
raises(k.cite, "note.md", server="nope", tool="get_issue")
c = k.cite("note.md", server="jira", tool="get_issue", args={"issue_key": "INFRA-1"},
           title="INFRA-1 status", stale_days=30)
assert c["footnote"] == "[^infra-1]"
(kb / "note.md").write_text((kb / "note.md").read_text().replace("Body.", "The ticket is open.[^infra-1]"))
d = k.meta((kb / "note.md").read_text())[0]
assert d["sources"][0]["resource"] == "mcp://jira/get_issue?issue_key=INFRA-1" and TS.fullmatch(d["stale_after"])
assert k.lint()["ok"], k.lint()
plan = k.recheck_plan()
assert plan["calls"][0]["call"] == {"server": "jira", "tool": "get_issue", "args": {"issue_key": "INFRA-1"}}
assert k.recheck_plan(older_than_days=1)["calls"] == []
assert "The ticket is open" in plan["calls"][0]["cites"][0]
assert k.recheck_apply([{"file": "note.md", "id": "infra-1"}])[0]["checked"] == ["infra-1"]
n = len(k.entries(k.meta((kb / "note.md").read_text())[0]["verified"]))
assert k.recheck_apply(file="note.md", by="process:nightly")[0]["checked"] == ["infra-1"]  # no id: every source
assert k.entries(k.meta((kb / "note.md").read_text())[0]["verified"])[-1]["by"] == "process:nightly"
assert len(k.entries(k.meta((kb / "note.md").read_text())[0]["verified"])) == n + 1
assert k.recheck_apply(file="note.md", id="nope")[0]["result"] == "no such source"
assert cli("recheck_apply", "file=note.md", "--attest")[0] == 0  # a person: "I checked this concept's sources"
assert k.entries(k.meta((kb / "note.md").read_text())[0]["verified"])[-1]["by"] == "human:drew"
assert cli("cite", "file=note.md", "resource=https://x", "--attest")[0] == 2  # citing is not confirming
assert "secret" not in json.dumps(k.lint(limit=0))
k.cite("note.md", resource="https://example.com/page", title="Page")
assert k.lint()["ok"]

# Symlinks are never followed.
(kb / "alias.md").symlink_to(kb / "note.md")
assert "alias.md" not in json.dumps(k.lint(limit=0)) and "alias" not in json.dumps(k.list_())
(kb / "alias.md").unlink()

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
(kb / "guides/ref.md").write_text("---\ntype: Note\ndescription: r.\nexecutor: {resource: note.md}\n"
                                  "sources:\n  - id: h\n    resource: howto.md\n---\n"
                                  "See [how](howto.md#howto), [note](../note.md) and [abs](/note.md).\n")
assert "playbooks/howto.md" in k.move("guides/howto.md", "playbooks/howto.md")["would_edit"]["."]
k.move("guides/howto.md", "playbooks/howto.md", apply=True)
assert (kb / "playbooks/howto.md").exists() and not (kb / "guides/howto.md").exists()
assert "](../playbooks/howto.md#howto)" in (kb / "guides/ref.md").read_text()
assert k.meta((kb / "guides/ref.md").read_text())[0]["sources"][0]["resource"] == "../playbooks/howto.md"
k.move("guides/ref", "a/b/ref", apply=True)
t = (kb / "a/b/ref.md").read_text()
assert "](../../playbooks/howto.md#howto)" in t and "](../../note.md)" in t and "](/note.md)" in t
d = k.meta(t)[0]
assert d["sources"][0]["resource"] == "../../playbooks/howto.md" and d["executor"]["resource"] == "note.md"  # root-relative stays
k.record("Reviewed the guides.")
assert re.search(r"^\* <!-- \d+ --> \*\*Update\*\*: Reviewed the guides\.$", (kb / "log.md").read_text(), re.MULTILINE)
raises(k.log, "two\nlines")
k.index(dirs=True, apply=True)
assert "(ref.md)" in (kb / "a/b/index.md").read_text() and "[b](b/)" in (kb / "a/index.md").read_text()
assert k.lint()["ok"] and "index_stale" not in kinds() and "dead_anchor" not in kinds()

# upgrade (v0.1): Citations become sources; timestamp needs git for `by`.
(kb / "old").mkdir()
(kb / "old/index.md").write_text("# Old\n")
(kb / "old/m.md").write_text("---\ntype: Metric\ntimestamp: '2026-05-28T22:53:05+00:00'\n---\n# M\n\nText.\n\n"
                             "# Citations\n- https://wiki.acme/fpa-handbook\n- [Policy](https://wiki.acme/policy)\n")
out = k.upgrade(apply=True, bundle="old")
assert out["needs_by"] == ["m.md"]
d = k.meta((kb / "old/m.md").read_text())[0]
assert [e["id"] for e in d["sources"]] == ["fpa-handbook", "policy"] and d["sources"][1]["title"] == "Policy"
assert "# Citations" not in (kb / "old/m.md").read_text() and "timestamp" in d
assert k.meta((kb / "old/index.md").read_text())[0]["okf_version"] == "0.2"
assert k.lint(bundle="old", scope="okf")["ok"] and k.upgrade(bundle="old")["would_edit"] == {}
assert {b["bundle"] for b in k.bundles()["bundles"]} == {".", "old"}
shutil.rmtree(kb / "old")

# The spec as an MCP resource.
assert "okf://spec" in {str(x.uri) for x in asyncio.run(k.mcp.list_resources())}
assert k.spec().startswith("# Open Knowledge Format")

# verify promote: only a human review moves draft to stable.
k.create("promo", "Note", description="P.", status="draft")
assert "only a human" in raises(k.verify, "promo.md", by="claude/x", promote=True)
assert cli("verify", "file=promo.md", "--attest", "promote=true")[0] == 0
assert k.meta((kb / "promo.md").read_text())[0]["status"] == "stable"

# fix normalizes tag case to the most common spelling.
(kb / "tags").mkdir()
for n, tg in (("a", "Sales"), ("b", "Sales"), ("c", "sales")):
    (kb / f"tags/{n}.md").write_text(f"---\ntype: x\ndescription: d.\ntags: [{tg}]\n---\n")
assert "tag_case" in kinds(bundle="tags")
k.fix(apply=True, bundle="tags")
assert "tag_case" not in kinds(bundle="tags") and k.meta((kb / "tags/c.md").read_text())[0]["tags"] == ["Sales"]
shutil.rmtree(kb / "tags")

# Spec use cases: §6.1 broken links tolerated, §5.1 lineage edges and signals, §8 lists and synthesized
# indexes, §9 logs at any level, §5.4 deprecation logged by convention.
u, saved = kb.parent / "uses", k.KB_ROOT
u.mkdir()
k.KB_ROOT = kb.parent
k.init(apply=True, bundle="uses")
k.create("t/src.md", "Reference", description="s.", bundle="uses", resource="https://example.com/x")
k.create("t/m.md", "Metric", description="m.", body="[later](/t/unwritten.md)", bundle="uses")
(u / "t/m.md").write_text((u / "t/m.md").read_text().replace("type: Metric", "type: Metric\nsources: [{id: s, resource: /t/src.md}]"))
L = k.lint(bundle="uses", limit=0)
assert L["ok"] and "dead_link" in L["counts"] and ("t/src.md", "orphan") not in {(f["file"], f["kind"]) for f in L["findings"]}
assert k.links("t/src.md", bundle="uses")["in"] == ["t/m.md"]
assert {"field": "sources[0].resource", "path": "/t/src.md", "target": {"bundle": "uses", "file": "t/src.md"},
        "exists": True} in k.links("t/m.md", bundle="uses")["out"]
assert "* [src](./t/src.md) - s." in (u / "index.md").read_text()
g = k.get("t/index.md", bundle="uses")
assert g["synthesized"] and "* [m](m.md) - m." in g["text"] and not (u / "t/index.md").exists()
(u / "t/log.md").write_text("# Log\n")
k.cite("t/m.md", resource="https://example.com/doc", author="team:docs", usage_count=0,
       last_modified="2026-05-30T00:00:00Z", bundle="uses")
e = k.meta((u / "t/m.md").read_text())[0]["sources"][-1]
assert e["author"] == "team:docs" and e["usage_count"] == 0 and "Cited" in (u / "t/log.md").read_text()
k.set_({"status": "deprecated"}, file="t/src.md", bundle="uses", apply=True)
assert "**Deprecation**: Deprecated [t/src.md](/t/src.md)." in (u / "t/log.md").read_text()
k.record("Hand note on [m](/t/m.md).", dir="t", bundle="uses")
L = k.log("t/m.md", bundle="uses")
assert [e["entry"] for e in L["entries"]][:1] == ["**Update**: Hand note on [m](/t/m.md)."] and L["entries"][0]["log"] == "t/log.md"
assert not any("src.md" in e["entry"] and "m.md" not in e["entry"] for e in L["entries"])
assert len(k.log(bundle="uses")["entries"]) > len(L["entries"])
assert "Hand note" in (u / "t/log.md").read_text() and "Hand note" not in (u / "log.md").read_text()
assert "usage_window" in raises(k.set_, {"usage_window": {"from": "x"}}, file="t/m.md", bundle="uses")
asyncio.run(k.verify("t/m.md", by="process:nightly", bundle="uses"))
k.create("t/d.md", "Note", description="d.", status="draft", by="claude-code/x", bundle="uses")
k.set_({"stale_after": k.now(10)}, file="t/m.md", bundle="uses", apply=True)
st = k.status(bundle="uses")
assert st["review"]["oldest"] == [{"file": "t/m.md", "days": 0}] and st["drafts"] == {"count": 1, "oldest": [{"file": "t/d.md", "days": 0}]}
assert [d["file"] for d in st["due"]] == ["t/m.md"] and not k.status(due_days=5, bundle="uses")["due"]
shutil.rmtree(u)
k.KB_ROOT = saved

# A knowledgebase of sibling bundles: tools follow where the user is; bundles do not nest.
saved, cwd, ws = k.KB_ROOT, os.getcwd(), (kb.parent / "ws").resolve()
ws.mkdir()
k.KB_ROOT = ws
k.init(apply=True, bundle="a")
k.init(apply=True, bundle="b")
assert (ws / ".gitattributes").read_text() == "log.md merge=union\n"
(ws / "a/sub").mkdir()
(ws / "a/sub/c.md").write_text("---\ntype: x\ndescription: c.\nsources: [{id: n, resource: /n.md}]\n---\n[n](/n.md)\n")
(ws / "a/n.md").write_text("---\ntype: x\ndescription: n.\n---\n[c](sub/c.md) [b](../b/m.md)\n")
(ws / "b/m.md").write_text("---\ntype: x\ndescription: m.\n---\n[n](../a/n.md) [m](m.md)\n")
k.index(apply=True, bundle="a")
k.index(apply=True, bundle="b")
os.chdir(ws / "a/sub")
L = k.lint(limit=0)
assert set(L["bundles"]) == {"a"} and {(f["bundle"], f["file"], f["kind"]) for f in L["findings"]} == {("a", "n.md", "cross_bundle")}, L
code, out = cli("get", "file=c.md")  # CLI paths are relative to where you are
assert code == 0 and (json.loads(out)["bundle"], json.loads(out)["file"]) == ("a", "sub/c.md")
os.chdir(ws)
L = k.lint(limit=0)
assert set(L["bundles"]) == {".", "a", "b"} and L["ok"], L
assert {("a", "n.md"), ("b", "m.md")} <= {(c["bundle"], c["file"]) for c in k.list_()["concepts"]} and any(h["bundle"] == "b" for h in k.search("description")["hits"])
assert set(k.status()["bundles"]) == {"a", "b"} and "bundles" not in k.status(bundle="a")
st = k.status(bundle="a")
assert st["sources"] == {"with": 1, "without": 1} and st["words"]["longest"][0]["words"] >= 1 and st["due"] == []
assert {(f["bundle"], f["file"]) for f in k.lint(file="a/n.md", limit=0)["findings"]} == {("a", "n.md")}
assert {(f["bundle"], f["file"]) for f in k.lint(files=["b"], limit=0)["findings"]} == {("b", "m.md")}
code, out = cli("lint", "a/n.md", "format=text")
assert code == 0 and out.startswith("a/n.md: warning: cross_bundle")
raises(k.lint, file="nope.md")
k.set_({"status": "draft"}, file="a/n.md", apply=True)  # routes to bundle a: its log, not a root one
assert "Set status" in (ws / "a/log.md").read_text() and not (ws / "log.md").exists()
assert k.links("a/n.md")["in"] == ["sub/c.md"] and k.links("n.md", bundle="a")["bundle"] == "a"
k.baseline(apply=True)  # fingerprints are knowledgebase-relative, so they hold from any directory
os.chdir(ws / "a")
assert k.lint(baseline=".okf-baseline.json")["total"] == 0 and k.lint(baseline=".okf-baseline.json")["baselined"]
os.chdir(ws)
assert "migrate" in raises(k.move, "a/sub/c.md", "b/c.md")
k.migrate("a/sub/c.md", "b", apply=True)
assert (ws / "b/sub/c.md").exists() and not (ws / "a/sub/c.md").exists()
assert "[c](../b/sub/c.md)" in (ws / "a/n.md").read_text() and "[n](../../a/n.md)" in (ws / "b/sub/c.md").read_text()
assert k.meta((ws / "b/sub/c.md").read_text())[0]["sources"][0]["resource"] == "../../a/n.md"
assert "Migrated" in (ws / "a/log.md").read_text() and "Migrated" in (ws / "b/log.md").read_text()
assert "nest" in raises(k.init, bundle="a/inner", apply=True)
(ws / "a/inner").mkdir()
(ws / "a/inner/index.md").write_text('---\nokf_version: "0.2"\n---\n# Inner\n')
assert "nested_bundle" in kinds(bundle="a")
shutil.rmtree(ws / "a/inner")
assert k.fix(apply=True)["remaining"]["ok"]  # every bundle here, re-linted the same way
(ws / "area").mkdir()
(ws / "area/y.md").write_text("---\ntype: x\ndescription: y.\n---\n")
(ws / "area/x.md").write_text("---\ntype: x\ndescription: x.\n---\n[n](/a/n.md) [y](/area/y.md)\n")
out = k.split_off("area", apply=True)
t = (ws / "area/x.md").read_text()
assert "[n](../a/n.md)" in t and "[y](/y.md)" in t and out["crossing"]["count"] == 1
assert k.declares(ws / "area/index.md") and k.lint(bundle="area")["ok"]
assert "nest" in raises(k.split_off, "b/sub")
# rename, archive, unarchive: whole directories move and every link follows.
(ws / "b/m.md").write_text("---\ntype: x\ndescription: m.\n---\n[n](../a/n.md) [m](/m.md)\n")
assert "-> d" in k.rename_bundle("d", bundle="b")["move"] and (ws / "b").exists()
k.rename_bundle("d", bundle="b", apply=True)
assert not (ws / "b").exists() and "[m](/m.md)" in (ws / "d/m.md").read_text()
assert "../d/m.md" in (ws / "a/n.md").read_text() and "Renamed the bundle" in (ws / "d/log.md").read_text()
k.archive("n.md", bundle="a", apply=True)  # one concept
assert (ws / "archive/a/n.md").exists() and k.declares(ws / "archive/index.md")
assert "../archive/a/n.md" in (ws / "d/m.md").read_text() and "archived_link" in kinds(bundle="d")
assert "archived" in raises(k.set_, {"status": "draft"}, file="a/n.md", bundle="archive")
k.unarchive("a/n.md", apply=True)
assert (ws / "a/n.md").exists() and "../a/n.md" in (ws / "d/m.md").read_text()
assert "explicitly" in raises(k.archive)
k.archive(bundle="d", apply=True)  # a whole bundle: its log comes along, it stops being a bundle
assert not (ws / "d").exists() and not k.declares(ws / "archive/d/index.md") and (ws / "archive/d/log.md").exists()
assert "../archive/d/m.md" in (ws / "a/n.md").read_text() and "nested_bundle" not in kinds(bundle="archive")
k.unarchive("d", apply=True)
assert k.declares(ws / "d/index.md") and "../d/m.md" in (ws / "a/n.md").read_text() and k.lint(bundle="d")["ok"]
k.rename_bundle("b", bundle="d", apply=True)
shutil.rmtree(ws / "archive")
w = k.web()  # at the knowledgebase root: bundles, edges counted
assert w["level"] == "bundles" and {"from": "a", "to": "b", "kind": "link", "count": 2} in w["edges"], w
assert k.web(bundle="a")["level"] == "concepts" and k.graph(w).startswith("graph LR\n")
code, out = cli("web", "format=mermaid")
assert code == 0 and "-->|link|" in out
assert k.knowledgebase(ws / "a/sub") == ws / "a"  # no index above yet: the bundle is the knowledgebase
assert "index_stale" not in kinds() and k.index(apply=True)["edited"] == {".": ["index.md"]}
assert (ws / "index.md").read_text().count("* [") == 3 and "* [b](b/)" in (ws / "index.md").read_text()
assert k.knowledgebase(ws / "a/sub") == ws and k.knowledgebase(ws) == ws
(ws / "c").mkdir()
k.init(apply=True, bundle="c")
assert "index_stale" in kinds() and k.fix(apply=True)["remaining"]["ok"] and "* [c](c/)" in (ws / "index.md").read_text()
os.chdir(cwd)
k.KB_ROOT = saved

# §6.2: a path field is a path only if it looks like one; git-ignored files are not scanned.
assert k.pathed("dashboards/exec-revenue", kb / "x.md", kb) is None
assert k.pathed("./nope", kb / "x.md", kb) == (None, "missing")
g = Path(tempfile.mkdtemp())
subprocess.run(["git", "init", "-q", str(g)], check=True)
(g / ".gitignore").write_text("node_modules/\n")
(g / "node_modules").mkdir()
(g / "node_modules/README.md").write_text("x\n")
(g / "a.md").write_text("x\n")
assert k.walk(g) == [g / "a.md"]

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
(kb / "bare.md").write_text("---\ntype: x\n---\n")
assert cli("set", "bare.md", "status=draft", "tags=[a, b]", "apply=true")[0] == 0  # frontmatter as key=value
assert k.meta((kb / "bare.md").read_text())[0] | {} == {"type": "x", "status": "draft", "tags": ["a", "b"]}
assert cli("move", "bare.md", "bare2.md", "apply=true")[0] == 0 and (kb / "bare2.md").exists()  # bare arguments
(kb / "bare2.md").unlink()
code, out = cli("help", "move")
assert code == 0 and "to: str  (required)" in out and cli("move", "--help")[1] == out
code, out = cli("bundles", "format=text")
assert code == 0 and out.startswith("bundles:")
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

hm = k.heatmap(bundle="src", limit=0)  # most changed first; README and guide changed twice
assert [(f["file"], f["changes"]) for f in hm["files"][:2]] == [("src/README.md", 2), ("src/docs/guide.md", 2)], hm
assert sum(f["changes"] for f in hm["files"]) == hm["bundles"][0]["changes"] == 5  # index.md left out
assert {(f["file"], f["authors"]) for f in hm["files"]} >= {("src/docs/guide.md", 2), ("src/README.md", 1)}
assert {a["author"] for a in hm["authors"]} == {"Ann", "Bob", "dependabot[bot]"} and hm["authors"][0] == {
    "author": "Ann", "changes": 3, "concepts": 2}
assert {(f["file"], f["author"]) for f in hm["single_author"]} == {("src/README.md", "Ann"), ("src/bot.md", "dependabot[bot]")}
h = k.history(src, [src / "docs/guide.md", src / "README.md", src / "bot.md"])
assert h[src / "docs/guide.md"]["by"] == "human:ann@example.com"  # Bob's frontmatter edit does not count
assert h[src / "README.md"]["by"] == "claude/claude-opus-5.5"
assert h[src / "bot.md"]["by"] == "process:dependabot"
assert k.provenance(bundle="src")["would_edit"] == {"src": ["docs/guide.md"]}

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
pl = k.ingest("shallow", bundle="fromshallow", keep_okf=True)  # no history: origin only, said so
assert "shallow" in pl and set(pl["provenance"]) == {"partial"}, pl
up = Path(tempfile.mkdtemp())  # a plain repo, shallow-cloned: origin documents the repository and the commit
for c in (["init", "-q"], ["-c", "user.name=A", "-c", "user.email=a@x", "-c", "commit.gpgsign=false", "commit", "-q",
                           "--allow-empty", "-m", "x"]):
    subprocess.run(["git", *c], cwd=up, check=True, capture_output=True)
(up / "plain.md").write_text("# Plain\n")
subprocess.run(["git", "add", "."], cwd=up, check=True)
subprocess.run(["git", "-c", "user.name=A", "-c", "user.email=a@x", "-c", "commit.gpgsign=false", "commit", "-qm", "y"],
               cwd=up, check=True)
subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{up}", str(kb / "shallow2")], check=True, capture_output=True)
k.ingest("shallow2", bundle="fromshallow2", apply=True)
o = k.meta((kb / "fromshallow2/plain.md").read_text())[0]["sources"][0]
assert o["resource"] == f"file://{up}" and re.fullmatch(r"plain\.md at [0-9a-f]{12} of file://.+", o["title"]), o
g("remote", "set-url", "origin", "https://user:tok@github.com/o/r.git")
assert k.remote(src) == "https://github.com/o/r.git"

# permalink: credentials and ports dropped; a local remote has no web URL.
g("remote", "set-url", "origin", "ssh://git@host.example:2222/o/r.git")
assert k.permalink(src, src.resolve())(src / "bot.md", "abc") == "https://host.example/o/r/blob/abc/bot.md"
g("remote", "set-url", "origin", "git@github.com:o/r.git")
assert k.permalink(src, src.resolve())(src / "bot.md", "abc") == "https://github.com/o/r/blob/abc/bot.md"
g("remote", "set-url", "origin", f"file://{src}")
assert k.permalink(src, src.resolve()) is None

print("ok")
