#!/usr/bin/env python3
"""Source-only audit for first-party product site links.

Checks checked-in assets, relative HTML links, fragment targets, and obsolete
owner URLs. Does NOT claim that Pages was deployed, remote links work, or a
released application matches the manual. Uses the GitHub API read-only.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from html.parser import HTMLParser
import json
import os
import posixpath
import re
import sys
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen


LEGACY_OWNER = re.compile(r"https?://(?:www\.)?github\.com/turinglambdaai/")
TIMEOUT = 20


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        properties = dict(attrs)
        identifier = properties.get("id")
        if identifier:
            self.ids.add(identifier)
        if tag == "a" and properties.get("name"):
            self.ids.add(properties["name"])
        for kind in ("href", "src"):
            value = properties.get(kind)
            if value:
                self.references.append((kind, value))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def parse_page(body: str) -> Page:
    page = Page()
    page.feed(body)
    return page


def audit_page(path: str, body: str, files: set[str], load_html) -> tuple[int, list[str]]:
    """Return number of local references tested and actionable source errors."""
    current = parse_page(body)
    examined = 0
    problems: list[str] = []
    if LEGACY_OWNER.search(body):
        problems.append(f"{path}: legacy github.com/turinglambdaai URL")
    for kind, url in current.references:
        if any(marker in url for marker in ("{{", "${", "<%")):
            continue  # templated URL, requires a runtime-specific review
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or url.startswith(("/", "//")):
            continue  # remote / deployment-root links are out of scope
        destination = unquote(parts.path)
        if not destination and not parts.fragment:
            continue
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), destination)) if destination else path
        examined += 1
        if resolved.startswith("../") or resolved == "..":
            problems.append(f"{path}: reference escapes repository: {url}")
            continue
        if destination.endswith("/"):
            resolved = posixpath.join(resolved, "index.html")
        if resolved not in files:
            problems.append(f"{path}: missing file {resolved} (from {kind}={url!r})")
            continue
        if kind == "href" and parts.fragment and resolved.lower().endswith((".html", ".htm")):
            try:
                target = current if resolved == path else parse_page(load_html(resolved))
            except Exception as exc:
                problems.append(f"{path}: cannot read fragment target {resolved}: {exc}")
                continue
            if unquote(parts.fragment) not in target.ids:
                problems.append(f"{path}: missing anchor #{parts.fragment} in {resolved}")
    return examined, problems


def github_get(url: str) -> bytes:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "turlamai-docs-audit"}
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=TIMEOUT) as response:
        return response.read()


def inspect_site(owner: str, spec: dict) -> tuple[str, int, list[str]]:
    repository = spec["repo"]
    root = spec["root"]
    name = f"{owner}/{repository}"
    tree_url = f"https://api.github.com/repos/{owner}/{repository}/git/trees/main?recursive=1"
    try:
        tree = json.loads(github_get(tree_url))
        if tree.get("truncated"):
            return name, 0, ["Git tree response truncated: cannot verify all paths"]
        if "tree" not in tree:
            return name, 0, ["Git tree unavailable (check repository visibility / branch)"]
        files = {item["path"] for item in tree["tree"] if item.get("type") == "blob"}

        @lru_cache(maxsize=64)
        def read_html(path: str) -> str:
            url = f"https://raw.githubusercontent.com/{owner}/{repository}/main/{quote(path, safe='/')}"
            return github_get(url).decode("utf-8")

        tested = 0
        issues = []
        for relative in spec["pages"]:
            path = posixpath.normpath(posixpath.join(root, relative))
            if path not in files:
                issues.append(f"{path}: declared page is missing")
                continue
            try:
                count, errors = audit_page(path, read_html(path), files, read_html)
            except Exception as exc:
                issues.append(f"{path}: unable to inspect source: {exc}")
                continue
            tested += count
            issues.extend(errors)
        return name, tested, sorted(set(issues))
    except Exception as exc:
        return name, 0, [f"repository source unavailable: {exc}"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="docs/product-sites.json")
    parser.add_argument("--jobs", type=int, default=6)
    options = parser.parse_args()

    with open(options.manifest, encoding="utf-8") as source:
        settings = json.load(source)
    sites = settings["sites"]
    if len({spec["repo"] for spec in sites}) != len(sites):
        parser.error("duplicate repository in manifest")

    results = []
    with ThreadPoolExecutor(max_workers=max(1, min(options.jobs, 8))) as executor:
        futures = [executor.submit(inspect_site, settings["owner"], site) for site in sites]
        for future in as_completed(futures):
            results.append(future.result())

    total = 0
    failures = 0
    for name, checked, errors in sorted(results):
        total += checked
        if errors:
            failures += len(errors)
            print(f"FAIL {name} ({checked} local references)")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {name} ({checked} local references)")
    print(f"Checked {len(results)} sites, {total} relative references, {failures} source errors.")
    print("Not covered: deployed site reachability, remote links, release assets, visual/UI behavior.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
