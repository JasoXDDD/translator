import unittest

from vtt_translator import find_keywords_in_vtt, format_keyword_context


class KeywordContextTests(unittest.TestCase):
    def test_finds_matching_keywords_case_insensitively(self):
        keywords = [
            {"keyword": "DeepSeek", "info": "LLM provider"},
            {"keyword": "missing", "info": "Should not match"},
        ]

        matches = find_keywords_in_vtt("WEBVTT\n\n00:00.000 --> 00:01.000\ndeepseek works", keywords)

        self.assertEqual(matches, [{"keyword": "DeepSeek", "info": "LLM provider"}])

    def test_formats_empty_context(self):
        self.assertEqual(format_keyword_context([]), "No stored keywords were found in this VTT file.")


if __name__ == "__main__":
    unittest.main()
