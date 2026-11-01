#!/usr/bin/env python3
"""Compare published first-party homepage download links with latest GitHub Release assets.

Read-only verification: checks exact static href targets, not platform-dependent
JavaScript-generated links or whether binaries install and launch.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys
from urllib.parse import unquote, urlsplit

from scripts.audit_product_docs import github_get

DIRECT = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/releases/latest/download/([^/?#]+)$")


class HrefParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "href" and value:
                self.links.append(value)


def direct_downloads(html):
    parser = HrefParser()
    parser.feed(html)
    found = set()
    for link in parser.links:
        match = DIRECT.fullmatch(link)
        if match:
            found.add((match.group(1), match.group(2), unquote(match.group(3))))
    return found


@lru_cache(maxsize=32)
def published_assets(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    payload = json.loads(github_get(url))
    return payload.get("tag_name"), {asset["name"] for asset in payload["assets"]}


def inspect_site(owner, spec):
    repo = spec["repo"]
    checked = 0
    problems = []
    tagged = {}
    for page in spec["pages"]:
        path = f'{spec["root"]}/{page}'
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
        try:
            html = github_get(url).decode("utf-8")
        except Exception as exc:
            problems.append(f"{path}: cannot read homepage: {exc}")
            continue
        for link_owner, link_repo, asset in sorted(direct_downloads(html)):
            checked += 1
            if (link_owner, link_repo) != (owner, repo):
                problems.append(f"{path}: unexpected external release destination {link_owner}/{link_repo}/{asset}")
                continue
            try:
                tag, names = published_assets(owner, repo)
                tagged[repo] = tag
                if asset not in names:
                    problems.append(f"{path}: missing {asset!r} in latest stable release {tag} (available: {len(names)})")
            except Exception as exc:
                problems.append(f"{path}: unable to verify latest stable release asset {asset!r}: {exc}")
    return repo, checked, tagged, sorted(set(problems))


def main():
    manifest = json.loads(Path("docs/product-sites.json").read_text(encoding="utf-8"))
    owner = manifest["owner"]
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = [pool.submit(inspect_site, owner, spec) for spec in manifest["sites"]]
        for future in as_completed(jobs):
            rows.append(future.result())

    bad = 0
    scanned = 0
    for repo, count, tags, issues in sorted(rows):
        scanned += count
        if issues:
            bad += len(issues)
            print(f"FAIL {owner}/{repo}: {count} exact homepage download links")
            for issue in issues:
                print("  - " + issue)
        else:
            print(f"PASS {owner}/{repo}: {count} exact homepage download links")
    print(f"Checked {len(rows)} products, {scanned} exact release links, {bad} missing or unverified.")
    print("Not covered: JS-generated links, preview releases, remote web hosting, binary quality, installation.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
