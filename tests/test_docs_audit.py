"""Offline tests for source-only HTML link validation."""

import unittest

from scripts.audit_product_docs import audit_page


class SourceLinkAuditTests(unittest.TestCase):
    def test_local_assets_query_strings_and_cross_page_anchors(self):
        files = {"docs/index.html", "docs/guide.html", "docs/styles.css", "docs/logo.svg"}
        pages = {"docs/guide.html": '<section id="setup">Install</section>'}
        home = (
            '<main id="intro"></main>'
            '<a href="#intro">Intro</a>'
            '<a href="guide.html#setup">Setup</a>'
            '<link href="styles.css?v=12" rel="stylesheet">'
            '<img src="logo.svg" alt="Logo">'
            '<a href="https://github.com/turlamai/taskly">source</a>'
        )
        count, issues = audit_page("docs/index.html", home, files, pages.__getitem__)
        self.assertEqual(count, 4)
        self.assertEqual(issues, [])

    def test_missing_fragment_and_missing_manual_are_reported(self):
        files = {"site/index.html", "site/styles.css", "site/guide.html"}
        pages = {"site/guide.html": "<h2 id='install'>Install</h2>"}
        body = '<a href="guide.html#missing">Manual</a><img src="missing.png">'
        _, issues = audit_page("site/index.html", body, files, pages.__getitem__)
        self.assertEqual(len(issues), 2)
        self.assertTrue(any("missing anchor #missing" in issue for issue in issues))
        self.assertTrue(any("missing file site/missing.png" in issue for issue in issues))

    def test_legacy_link_and_parent_traversal(self):
        files = {"site/index.html"}
        body = (
            '<a href="https://github.com/turinglambdaai/product">Old link</a>'
            '<a href="../../private.txt">Escapes</a>'
        )
        _, issues = audit_page("site/index.html", body, files, lambda _: "")
        self.assertEqual(len(issues), 2)
        self.assertTrue(any("legacy github.com/turinglambdaai" in issue for issue in issues))
        self.assertTrue(any("escapes repository" in issue for issue in issues))

    def test_external_links_and_templates_are_ignored(self):
        files = {"docs/index.html"}
        body = (
            '<a href="mailto:contact@example.com">Email</a>'
            '<a href="https://example.org/docs">External</a>'
            '<a href="{{ dynamic_path }}">Dynamic</a>'
            '<a href="/">Root</a>'
        )
        count, issues = audit_page("docs/index.html", body, files, lambda _: "")
        self.assertEqual(count, 0)
        self.assertEqual(issues, [])


    def test_regression_missing_flashpilot_guide(self):
        files = {"site/index.html"}
        _, issues = audit_page(
            "site/index.html", '<a href="guide.html">Manual</a>', files, lambda _: ""
        )
        self.assertTrue(any("missing file site/guide.html" in issue for issue in issues))

    def test_regression_taskly_download_anchor(self):
        files = {"docs/index.html", "docs/manual.html"}
        pages = {"docs/index.html": '<section id="release"></section>'}
        _, old_issues = audit_page(
            "docs/manual.html",
            '<a href="index.html#download">Download</a>',
            files,
            pages.__getitem__,
        )
        _, fixed_issues = audit_page(
            "docs/manual.html",
            '<a href="index.html#release">Downloads</a>',
            files,
            pages.__getitem__,
        )
        self.assertTrue(any("missing anchor #download" in issue for issue in old_issues))
        self.assertEqual(fixed_issues, [])

if __name__ == "__main__":
    unittest.main()
