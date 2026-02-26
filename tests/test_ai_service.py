"""
Unit tests for AI Service using cached/mock data
"""
import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService
from tests.fixtures import MockData, TEST_CONFIG


class TestAIService(unittest.TestCase):
    """Test AI Service with cached data"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create AI service with test config
        self.ai_service = AIService(TEST_CONFIG)
        
        # Patch the cache directory
        self.original_cache_join = os.path.join
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_cache_file(self, prompt: str, items: list, max_items: int = 30):
        """Create a mock cache file"""
        cache_key = f"{prompt}_{max_items}".replace(" ", "_").lower()
        cache_file = os.path.join(self.cache_dir, f'{cache_key}.json')
        
        cache_data = {
            'prompt': prompt,
            'items': items,
            'generated_at': '2025-10-25T21:00:00'
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        return cache_file
    
    @patch('os.path.join')
    def test_get_items_list_from_cache(self, mock_join):
        """Test loading items from cache"""
        # Setup mock to use our temp directory
        def side_effect(*args):
            if args[0] == 'cache':
                return os.path.join(self.cache_dir, args[1])
            return self.original_cache_join(*args)
        
        mock_join.side_effect = side_effect
        
        # Create cached data
        expected_items = MockData.get_animals_items()
        self.create_mock_cache_file('animals', expected_items)
        
        # Test
        result = self.ai_service.get_items_list('animals')
        
        self.assertEqual(result, expected_items)
    
    def test_fallback_items_animals(self):
        """Test fallback items for animals"""
        result = self.ai_service._get_fallback_items('animals', 15)
        
        expected_animals = MockData.get_animals_items()
        self.assertEqual(result, expected_animals)
    
    def test_fallback_items_body_parts(self):
        """Test fallback items for body parts"""
        result = self.ai_service._get_fallback_items('body parts', 16)
        
        expected_parts = MockData.get_body_parts_items()
        self.assertEqual(result, expected_parts)
    
    def test_fallback_items_colors(self):
        """Test fallback items for colors"""
        result = self.ai_service._get_fallback_items('colors', 11)
        
        expected_colors = MockData.get_colors_items()
        self.assertEqual(result, expected_colors)
    
    def test_fallback_items_unknown_prompt(self):
        """Test fallback for unknown prompt"""
        result = self.ai_service._get_fallback_items('unknown_category', 10)
        
        # Should default to body parts
        expected = MockData.get_body_parts_items()[:10]
        self.assertEqual(result, expected)
    
    def test_max_items_limit(self):
        """Test that max_items limit is respected"""
        items = MockData.get_animals_items()
        result = self.ai_service._get_fallback_items('animals', 5)
        
        self.assertEqual(len(result), 5)
        self.assertEqual(result, items[:5])
    
    @patch('openai.OpenAI')
    def test_ai_generation_with_mock_response(self, mock_openai):
        """Test AI generation with mocked OpenAI response"""
        # Setup mock OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(MockData.get_colors_items())
        mock_client.chat.completions.create.return_value = mock_response
        
        # Override client with mock
        self.ai_service.client = mock_client
        
        result = self.ai_service.get_items_list('colors', 11)
        
        expected = MockData.get_colors_items()
        self.assertEqual(result, expected)
    
    @patch('openai.OpenAI')
    def test_ai_generation_json_error_fallback(self, mock_openai):
        """Test fallback when AI returns invalid JSON"""
        # Setup mock OpenAI response with invalid JSON
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Override client with mock
        self.ai_service.client = mock_client
        
        result = self.ai_service.get_items_list('animals', 5)
        
        # Should fall back to default animals
        expected = MockData.get_animals_items()[:5]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
