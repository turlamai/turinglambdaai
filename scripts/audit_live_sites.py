#!/usr/bin/env python3
"""Probe official product CNAME hostnames from a GitHub Actions runner.

Reports HTTP status, HTML title and exact source-byte agreement. This is
reachability/deployment evidence, not a real-browser or application test.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import hashlib
import json
import re
import sys

from scripts.audit_product_docs import github_get


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def parse_title(text):
    parser = TitleParser()
    parser.feed(text)
    return " ".join(parser.title.split())


def compare_source_and_live(source, live):
    """Check shared HTML identity and byte agreement without browser claims."""
    source_title = parse_title(source)
    live_title = parse_title(live)
    exact = source.replace("\r\n", "\n") == live.replace("\r\n", "\n")
    return source_title, live_title, exact


def probe_site(owner, spec):
    repo = spec["repo"]
    path = f'{spec["root"]}/index.html'
    prefix = f"https://raw.githubusercontent.com/{owner}/{repo}/main/"
    try:
        cname = github_get(prefix + f'{spec["root"]}/CNAME').decode("utf-8").strip()
        if not re.fullmatch(r"[a-z0-9.-]+\.jrtx\.site", cname):
            return repo, None, f"invalid or unexpected CNAME: {cname!r}"
        source = github_get(prefix + path).decode("utf-8")
        request = Request("https://" + cname + "/", headers={"User-Agent": "turlamai-product-qa/1.0", "Accept": "text/html"})
        with urlopen(request, timeout=15) as response:
            status = response.status
            mime = response.headers.get_content_type()
            address = response.geturl()
            body = response.read(2_000_000).decode("utf-8", errors="replace")
        source_title, live_title, exact = compare_source_and_live(source, body)
        info = {"domain": cname, "status": status, "source_title": source_title,
                "live_title": live_title, "exact_source_bytes": exact}
        if status != 200 or mime != "text/html":
            return repo, info, f"unexpected HTTP status or content type: {status} {mime}"
        if not source_title or source_title != live_title:
            return repo, info, "live site title differs from checked-in main HTML title"
        if not address.startswith("https://" + cname + "/"):
            return repo, info, f"unexpected redirect destination: {address}"
        return repo, info, None
    except (HTTPError, URLError, TimeoutError, ValueError, UnicodeError) as error:
        return repo, None, f"deployed site could not be checked: {error}"
    except Exception as error:
        return repo, None, f"source or host check failed: {error}"


def main():
    sites = json.loads(Path("docs/product-sites.json").read_text(encoding="utf-8"))
    checked = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(probe_site, sites["owner"], spec) for spec in sites["sites"]]
        for future in as_completed(futures):
            checked.append(future.result())
    failures = 0
    drift = 0
    for repo, info, problem in sorted(checked):
        if problem:
            failures += 1
            print(f"FAIL {repo}: {problem} — {info}")
        else:
            drift += not info["exact_source_bytes"]
            print(f"PASS {repo}: {info['domain']} HTTP {info['status']} title matched; exact-source={info['exact_source_bytes']}")
    print(f"Checked {len(checked)} deployed sites: {failures} failures; {drift} non-identical HTML bodies for review.")
    print("Not tested: CSS visual layout, language switching, dynamic assets, OS-specific installs, updates.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
