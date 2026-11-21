"""Regression protection for the archive and local reference checker."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('documentation', ROOT / 'tools/check_documentation.py')
DOCS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOCS)


class DocumentationTests(unittest.TestCase):
    def test_repository_links_and_originals(self):
        counts = DOCS.check()
        self.assertEqual(counts['archivedDocuments'], 25)
        self.assertGreater(counts['localReferences'], 100)

    def test_unicode_duplicate_and_fenced_headings(self):
        text = '# Revisión: `INTEGER`\n## Revisión: `INTEGER`\n```md\n# Hidden\n```'
        self.assertEqual(DOCS.markdown_anchors(text), {'revisión-integer', 'revisión-integer-1'})


if __name__ == '__main__':
    unittest.main()