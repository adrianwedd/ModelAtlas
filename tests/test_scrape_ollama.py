import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
import os
import sys
from io import StringIO

# Add the tools directory to the path so we can import scrape_ollama
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import scrape_ollama

class TestScrapeOllama(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for model JSON files and debug dumps
        self.test_ollama_models_dir = "test_models_ollama"
        self.test_debug_dir = "test_ollama_debug_dumps"
        os.makedirs(self.test_ollama_models_dir, exist_ok=True)
        os.makedirs(self.test_debug_dir, exist_ok=True)

        # Patch the directories in scrape_ollama.py
        scrape_ollama.OLLAMA_MODELS_DIR = self.test_ollama_models_dir
        scrape_ollama.DEBUG_DIR = self.test_debug_dir
        scrape_ollama.LOG_FILE = "test_ollama_scraper.log"

        # Use settings for consistency
        scrape_ollama.settings.OLLAMA_MODELS_DIR = Path(self.test_ollama_models_dir)
        scrape_ollama.settings.DEBUG_DIR = Path(self.test_debug_dir)
        scrape_ollama.settings.LOG_FILE = Path("test_ollama_scraper.log")

        # Clear log file before each test
        if os.path.exists(scrape_ollama.LOG_FILE):
            os.remove(scrape_ollama.LOG_FILE)

    def tearDown(self):
        # Clean up temporary directories and files
        for root, dirs, files in os.walk(self.test_ollama_models_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_ollama_models_dir)

        for root, dirs, files in os.walk(self.test_debug_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_debug_dir)

        if os.path.exists(scrape_ollama.LOG_FILE):
            os.remove(scrape_ollama.LOG_FILE)

    @patch('scrape_ollama.requests.get')
    @patch('scrape_ollama.BeautifulSoup')
    @patch('scrape_ollama.scrape_tags_page')
    @patch('scrape_ollama.scrape_details')
    @patch('scrape_ollama.get_hash') # Patch get_hash
    @patch('scrape_ollama.sync_playwright')
    def test_scrape_new_model(self, mock_sync_playwright, mock_get_hash, mock_scrape_details, mock_scrape_tags_page, mock_beautifulsoup, mock_requests_get):
        model_name = "test-model"
        # Mock Playwright setup (minimal as scrape_details/tags are mocked)
        mock_playwright = MagicMock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
        mock_browser = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_temp_page = MagicMock()
        mock_browser.new_page.return_value = mock_temp_page

        # Mock initial library page content
        mock_page.content.return_value = f"""
            <ul>
                <li><a href="/library/{model_name}">{model_name}</a></li>
            </ul>
        """
        mock_initial_library_soup = MagicMock()
        mock_initial_library_soup.select.return_value = [
            MagicMock(find=lambda x: {'href': f'/library/{model_name}'})
        ]
        mock_beautifulsoup.side_effect = [mock_initial_library_soup, MagicMock()] # For initial library, then temp_page

        # Mock get_hash to return a consistent hash
        mock_get_hash.return_value = "mocked_hash_new"

        # Mock scrape_details and scrape_tags_page to return sample data
        sample_details = {
            "name": model_name,
            "description": "Test description.",
            "pull_count": 12345,
            "last_updated": "Jul 17, 2025",
            "readme_html": "<div>Test README HTML</div>",
            "readme_text": "Test README text.",
            "architecture": "amd64",
            "family": "test-family",
            "page_hash": "mocked_hash_new" # This will be overwritten by the actual hash from get_hash
        }
        mock_scrape_details.return_value = sample_details
        mock_scrape_tags_page.return_value = [
            {
                "tag": "latest",
                "last_updated": "2 weeks ago",
                "size": "1.2GB",
                "digest": "mocked_digest",
                "manifest": {},
                "config": {}
            }
        ]

        # Mock requests.get for manifest and config blobs (if still called by scrape_tags_page)
        mock_requests_get.return_value.json.return_value = {}
        mock_requests_get.return_value.raise_for_status.return_value = None

        # Capture stdout/stderr
        captured_output = StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output

        try:
            scrape_ollama.scrape_ollama_models_from_web(headless=True, debug_model=model_name)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            print("Captured Output:\n", captured_output.getvalue())

        # Assertions
        model_file_path = os.path.join(self.test_ollama_models_dir, f"{model_name}.json")
        self.assertTrue(os.path.exists(model_file_path))
        with open(model_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["name"], model_name)
            self.assertEqual(data["description"], "Test description.")
            self.assertEqual(data["page_hash"], "mocked_hash_new")
            self.assertIn("quality_score", data)
        with open(scrape_ollama.LOG_FILE) as f:
            self.assertIn("Performing full scrape", f.read())

    @patch('scrape_ollama.requests.get')
    @patch('scrape_ollama.BeautifulSoup')
    @patch('scrape_ollama.scrape_tags_page')
    @patch('scrape_ollama.scrape_details')
    @patch('scrape_ollama.get_hash') # Patch get_hash
    @patch('scrape_ollama.sync_playwright')
    def test_scrape_existing_model_no_change(self, mock_sync_playwright, mock_get_hash, mock_scrape_details, mock_scrape_tags_page, mock_beautifulsoup, mock_requests_get):
        model_name = "test-model-unchanged"
        model_file_path = os.path.join(self.test_ollama_models_dir, f"{model_name}.json")
        
        # Create a dummy existing model file with a known hash
        initial_hash = "mocked_hash_unchanged"
        existing_data = {"name": model_name, "description": "Initial description.", "page_hash": initial_hash, "tags": [], "quality_score": {"completeness": 0.5}}
        with open(model_file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        # Mock Playwright setup
        mock_playwright = MagicMock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
        mock_browser = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_temp_page = MagicMock()
        mock_browser.new_page.return_value = mock_temp_page

        # Mock initial library page content
        mock_page.content.return_value = f"""
            <ul>
                <li><a href="/library/{model_name}">{model_name}</a></li>
            </ul>
        """
        mock_initial_library_soup = MagicMock()
        mock_initial_library_soup.select.return_value = [
            MagicMock(find=lambda x: {'href': f'/library/{model_name}'})
        ]

        # Mock get_hash to return a consistent hash
        mock_get_hash.return_value = initial_hash

        # Control which BeautifulSoup instance is returned
        mock_beautifulsoup.side_effect = [
            mock_initial_library_soup, # First call for initial library page
            MagicMock() # For temp_page_soup.prettify() - will be ignored due to mocked get_hash
        ]

        # Capture stdout/stderr
        captured_output = StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output

        try:
            scrape_ollama.scrape_ollama_models_from_web(headless=True, debug_model=model_name)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            print("Captured Output:\n", captured_output.getvalue())

        # Assertions
        mock_scrape_details.assert_not_called() # Verify scrape_details was skipped
        mock_scrape_tags_page.assert_not_called() # Verify scrape_tags_page was skipped

        self.assertTrue(os.path.exists(model_file_path))
        with open(model_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["name"], model_name)
            self.assertEqual(data["description"], "Initial description.")
            self.assertEqual(data["page_hash"], initial_hash)
        with open(scrape_ollama.LOG_FILE) as f:
            log_content = f.read()
            self.assertIn(f"Page hash for {model_name} matches existing data. Skipping detailed scrape.", log_content)
            self.assertNotIn("Performing full scrape", log_content)

    @patch('scrape_ollama.requests.get')
    @patch('scrape_ollama.BeautifulSoup')
    @patch('scrape_ollama.scrape_tags_page')
    @patch('scrape_ollama.scrape_details')
    @patch('scrape_ollama.get_hash') # Patch get_hash
    @patch('scrape_ollama.sync_playwright')
    def test_scrape_existing_model_with_change(self, mock_sync_playwright, mock_get_hash, mock_scrape_details, mock_scrape_tags_page, mock_beautifulsoup, mock_requests_get):
        model_name = "test-model-changed"
        model_file_path = os.path.join(self.test_ollama_models_dir, f"{model_name}.json")
        
        # Create a dummy existing model file with a known hash
        old_hash = "mocked_hash_old"
        existing_data = {"name": model_name, "description": "Old description.", "page_hash": old_hash, "tags": [], "quality_score": {"completeness": 0.5}}
        with open(model_file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)

        # Mock Playwright setup
        mock_playwright = MagicMock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright
        mock_browser = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_page = MagicMock()
        mock_browser.new_page.return_value = mock_page
        mock_temp_page = MagicMock()
        mock_browser.new_page.return_value = mock_temp_page

        # Mock initial library page content
        mock_page.content.return_value = f"""
            <ul>
                <li><a href="/library/{model_name}">{model_name}</a></li>
            </ul>
        """
        mock_initial_library_soup = MagicMock()
        mock_initial_library_soup.select.return_value = [
            MagicMock(find=lambda x: {'href': f'/library/{model_name}'})
        ]

        # Mock get_hash to return a new hash
        new_hash = "mocked_hash_new_changed"
        mock_get_hash.return_value = new_hash

        # Control which BeautifulSoup instance is returned
        mock_beautifulsoup.side_effect = [
            mock_initial_library_soup, # First call for initial library page
            MagicMock() # For temp_page_soup.prettify() - will be ignored due to mocked get_hash
        ]

        # Mock scrape_details and scrape_tags_page to return updated sample data
        updated_details = {
            "name": model_name,
            "description": "New description.",
            "pull_count": 54321,
            "last_updated": "Jul 18, 2025",
            "readme_html": "<div>New README HTML</div>",
            "readme_text": "New README text.",
            "architecture": "arm64",
            "family": "new-family",
            "page_hash": new_hash # This will be overwritten by the actual hash from get_hash
        }
        mock_scrape_details.return_value = updated_details
        mock_scrape_tags_page.return_value = [
            {
                "tag": "new-latest",
                "last_updated": "1 week ago",
                "size": "2.5GB",
                "digest": "new_mocked_digest",
                "manifest": {},
                "config": {}
            }
        ]

        # Mock requests.get for manifest and config blobs
        mock_requests_get.return_value.json.return_value = {}
        mock_requests_get.return_value.raise_for_status.return_value = None

        # Capture stdout/stderr
        captured_output = StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output

        try:
            scrape_ollama.scrape_ollama_models_from_web(headless=True, debug_model=model_name)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            print("Captured Output:\n", captured_output.getvalue())

        # Assertions
        mock_scrape_details.assert_called_once() # Verify scrape_details was called
        mock_scrape_tags_page.assert_called_once() # Verify scrape_tags_page was called

        self.assertTrue(os.path.exists(model_file_path))
        with open(model_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["name"], model_name)
            self.assertEqual(data["description"], "New description.")
            self.assertEqual(data["page_hash"], new_hash)
            self.assertIn("quality_score", data)
        with open(scrape_ollama.LOG_FILE) as f:
            log_content = f.read()
            self.assertIn("Performing full scrape", log_content)
            self.assertNotIn("Skipping detailed scrape", log_content)

if __name__ == '__main__':
    unittest.main()
