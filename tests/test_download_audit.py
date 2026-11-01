import unittest
from scripts.audit_product_downloads import direct_downloads


class ReleaseLinkParsingTests(unittest.TestCase):
    def test_static_links_are_deduplicated(self):
        html = ('<a href="https://github.com/turlamai/taskly/releases/latest/download/taskly-linux-x64.AppImage">Download</a>'
                '<a href="https://github.com/turlamai/taskly/releases/latest/download/taskly-linux-x64.AppImage">Again</a>')
        self.assertEqual(direct_downloads(html), {("turlamai", "taskly", "taskly-linux-x64.AppImage")})

    def test_release_overview_and_dynamic_urls_are_not_mistaken_for_assets(self):
        html = ('<a href="https://github.com/turlamai/taskly/releases">All</a>'
                '<a href="https://github.com/turlamai/taskly/releases/latest">Latest</a>'
                '<script>let base = "https://github.com/turlamai/taskly/releases/latest/download/";</script>')
        self.assertEqual(direct_downloads(html), set())

    def test_encoded_name_and_query_are_ignored_without_false_success(self):
        html = '<a href="https://github.com/turlamai/thing/releases/latest/download/my%20app.zip">zip</a>'
        self.assertEqual(direct_downloads(html), {("turlamai", "thing", "my app.zip")})


if __name__ == "__main__":
    unittest.main()
