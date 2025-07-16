import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harvester.base import (
    get_jwt,
    fetch_all_ids,
    infer_region,
    infer_region_from_note,
    extract_text,
    get_domain_from_url,
    process_url
)

class TestBase(unittest.TestCase):
    @patch('requests.post')
    def test_get_jwt(self, mock_post):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = "test_jwt_token"
        mock_post.return_value = mock_response

        result = get_jwt("test_api_key")
        self.assertEqual(result, "test_jwt_token")
        mock_post.assert_called_once()

        # Mock failed response
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        with self.assertRaises(Exception):
            get_jwt("invalid_api_key")

    @patch('requests.get')
    def test_fetch_all_ids(self, mock_get):
        # Mock successful response with bookmark
        mock_response1 = MagicMock()
        mock_response1.ok = True
        mock_response1.json.return_value = ["id1", "id2"]
        mock_response1.headers = {"x-ado-bookmark": "bookmark1"}

        mock_response2 = MagicMock()
        mock_response2.ok = True
        mock_response2.json.return_value = ["id3", "id4"]
        mock_response2.headers = {}

        mock_get.side_effect = [mock_response1, mock_response2]

        result = fetch_all_ids("test_jwt", "test_query")
        self.assertEqual(result, ["id1", "id2", "id3", "id4"])
        self.assertEqual(mock_get.call_count, 2)

    def test_infer_region_from_note(self):
        test_cases = [
            ("I live in Melbourne, Australia", "Australia"),
            ("来自北京的中国用户", "China"),
            ("Living in New York, USA", "United States"),
            ("No location mentioned", None)
        ]
        
        for note, expected in test_cases:
            with self.subTest(note=note):
                result = infer_region_from_note(note)
                self.assertEqual(result, expected)

    def test_infer_region(self):
        test_cases = [
            (("ja", "mastodon.social", ""), "Japan"),
            (("zh", "mastodon.social", ""), "China"),
            (("en", "aus.social", ""), "Australia"),
            (("en", "mastodon.social", "I'm from London"), "United Kingdom"),
            (("en", "unknown.domain", ""), "Global")
        ]
        
        for (language, domain, note), expected in test_cases:
            with self.subTest(language=language, domain=domain, note=note):
                result = infer_region(language, domain, note)
                self.assertEqual(result, expected)

    def test_extract_text(self):
        test_cases = [
            (
                '<p>Hello <a href="https://example.com">world</a></p>',
                'Hello world'
            ),
            (
                '<p>Line 1<br>Line 2</p>',
                'Line 1 Line 2'
            ),
            (
                '<a href="https://example.com">https://example.com</a>',
                'https://example.com'
            )
        ]
        
        for html, expected in test_cases:
            with self.subTest(html=html):
                result = extract_text(html)
                self.assertEqual(result, expected)

    def test_get_domain_from_url(self):
        test_cases = [
            ("https://mastodon.social/@user", "mastodon.social"),
            ("http://aus.social/users/123", "aus.social"),
            ("https://example.com/path", "example.com")
        ]
        
        for url, expected in test_cases:
            with self.subTest(url=url):
                result = get_domain_from_url(url)
                self.assertEqual(result, expected)

    def test_process_url(self):
        # Test with a real Mastodon post URL
        result = process_url('universeodon.com/@godpod/114495284548330848')
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn('post_id', result)
        self.assertIn('created_time', result)
        self.assertIn('content', result)
        self.assertIn('url', result)
        self.assertIn('language', result)
        self.assertIn('region', result)
        self.assertIn('author', result)
        self.assertIn('favourited_by', result)
        self.assertIn('reblogged_by', result)
        self.assertIn('replies', result)
        
        # Verify author information
        self.assertIsInstance(result['author'], dict)
        self.assertIn('acct', result['author'])
        self.assertIn('display_name', result['author'])
        self.assertIn('created_time', result['author'])
        self.assertIn('url', result['author'])
        self.assertIn('Domain', result['author'])
        self.assertIn('note', result['author'])
        
        # Verify lists
        self.assertIsInstance(result['favourited_by'], list)
        self.assertIsInstance(result['reblogged_by'], list)
        self.assertIsInstance(result['replies'], list)

if __name__ == '__main__':
    unittest.main() 