#!/usr/bin/env python3
"""Source-only audit for first-party product site links.

Checks checked-in HTML/CSS assets, relative links, fragment targets, and obsolete
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
CSS_URL = re.compile(r"""url\(\s*(['\"]?)(.*?)\1\s*\)""", re.IGNORECASE)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.references: list[tuple[str, str]] = []
        self.styles: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        properties = dict(attrs)
        if tag == "style":
            self._in_style = True
        if properties.get("style"):
            self.styles.append(properties["style"])
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

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.styles.append(data)


def parse_page(body: str) -> Page:
    page = Page()
    page.feed(body)
    return page


def audit_css(path: str, body: str, files: set[str]) -> tuple[int, list[str]]:
    """Check local CSS url(...) assets relative to the containing CSS or HTML."""
    checked = 0
    issues: list[str] = []
    for match in CSS_URL.finditer(body):
        url = match.group(2).strip()
        if not url or any(marker in url for marker in ("{{", "\${", "<%")):
            continue
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or url.startswith(("/", "//", "#")):
            continue
        if not parts.path:
            continue
        target = posixpath.normpath(posixpath.join(posixpath.dirname(path), unquote(parts.path)))
        checked += 1
        if target.startswith("../") or target == "..":
            issues.append(f"{path}: CSS reference escapes repository: {url}")
        elif target not in files:
            issues.append(f"{path}: missing CSS asset {target} (from url({url!r}))")
    return checked, issues


def audit_page(path: str, body: str, files: set[str], load_html, load_css=None) -> tuple[int, list[str]]:
    """Return number of local references tested and actionable source errors."""
    current = parse_page(body)
    examined = 0
    problems: list[str] = []
    if LEGACY_OWNER.search(body):
        problems.append(f"{path}: legacy github.com/turinglambdaai URL")
    css_count, css_issues = audit_css(path, "\n".join(current.styles), files)
    examined += css_count
    problems.extend(css_issues)
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
        if kind == "href" and resolved.lower().endswith(".css") and load_css is not None:
            try:
                css_count, css_issues = audit_css(resolved, load_css(resolved), files)
                examined += css_count
                problems.extend(css_issues)
            except Exception as exc:
                problems.append(f"{path}: cannot read linked CSS {resolved}: {exc}")
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
                count, errors = audit_page(path, read_html(path), files, read_html, read_html)
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
    print("Not covered: deployed reachability, remote URLs, release assets, CSS imports without url(), visual/UI behavior.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
