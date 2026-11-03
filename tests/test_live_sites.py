import unittest
from scripts.audit_live_sites import compare_source_and_live, parse_title


class LiveProbeTests(unittest.TestCase):
    def test_title_with_entities(self):
        self.assertEqual(parse_title("<html><title>Booklight &amp; Notes</title></html>"), "Booklight & Notes")

    def test_identical_normalized_source(self):
        source, live, same = compare_source_and_live(
            "<!doctype html>\r\n<title>App</title>",
            "<!doctype html>\n<title>App</title>"
        )
        self.assertEqual(source, live)
        self.assertTrue(same)

    def test_wrong_site_title_is_detected(self):
        source, live, same = compare_source_and_live(
            "<title>MoveBit</title>", "<title>Hosting error</title>"
        )
        self.assertNotEqual(source, live)
        self.assertFalse(same)


if __name__ == "__main__":
    unittest.main()
