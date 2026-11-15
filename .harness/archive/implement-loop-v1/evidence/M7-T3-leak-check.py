#!/usr/bin/env python3
"""Read-only leak check: counts occurrences of alert secrets per location. Prints labels and counts only."""
import json, os, subprocess, sys
from urllib.parse import quote

CONFIG = os.path.expanduser("~/.config/harness-e2e/alert.json")
SECRET_KEYS = ["ntfy_topic", "to"]  # topic and recipient; server base URL is not a secret
FIXTURE = "/Users/ryankenny/Tools/harness-m7-fixture"
THIS = "/Users/ryankenny/Tools/AgenticCodingHarness"


def fail(reason):
    print("LEAK_CHECK_FAIL: " + reason)
    sys.exit(1)


def load():
    try:
        with open(CONFIG) as f:
            cfg = json.load(f)
    except Exception:
        fail("alert config missing or unreadable")
    if not isinstance(cfg, dict) or not isinstance(cfg.get("ntfy_topic"), str) or not cfg["ntfy_topic"]:
        fail("no topic key found")
    secrets = {}
    for k in SECRET_KEYS:
        v = cfg.get(k)
        if isinstance(v, str) and v:
            secrets[k] = v
    return secrets


def needles(secrets):
    out = set()
    for v in secrets.values():
        out.add(v.encode())
        out.add(quote(v, safe="").encode())
    return sorted(out)


def count_in(data, ns):
    return sum(data.count(n) for n in ns)


def count_files(paths, ns):
    total = 0
    for p in paths:
        try:
            with open(p, "rb") as f:
                total += count_in(f.read(), ns)
        except OSError:
            pass
    return total


def tree_files(root):
    for dp, dns, fns in os.walk(root):
        if ".git" in dns:
            dns.remove(".git")
        for fn in fns:
            p = os.path.join(dp, fn)
            if not os.path.islink(p):
                yield p


def git_count(repo, ns):
    total = 0
    for args in (["log", "-p", "--all", "--binary"], ["log", "--all", "--format=%B"]):
        r = subprocess.run(["git", "-C", repo] + args, capture_output=True)
        if r.returncode != 0:
            fail("git history unreadable in " + repo)
        total += count_in(r.stdout, ns)
    return total


def main():
    secrets = load()
    ns = needles(secrets)
    print("secrets checked: %d (%s)" % (len(secrets), ", ".join(sorted(secrets))))
    loop = os.path.join(FIXTURE, ".harness", "loop")
    results = []
    for name in ("loop.log", "commands.log", "outcome.json"):
        results.append(("fixture " + name, count_files([os.path.join(loop, name)], ns)))
    results.append(("fixture working tree", count_files(tree_files(FIXTURE), ns)))
    results.append(("fixture git history", git_count(FIXTURE, ns)))
    results.append(("this repo working tree", count_files(tree_files(THIS), ns)))
    results.append(("this repo git history", git_count(THIS, ns)))
    for label, c in results:
        print("%s: %d" % (label, c))
    if any(len(v) < 8 for v in secrets.values()):
        fail("a secret is shorter than 8 characters")
    if any(c for _, c in results):
        fail("matches found")
    print("LEAK_CHECK_OK")


main()
