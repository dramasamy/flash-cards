"""
Test fixtures and mock data for unit testing
"""
import json
import os
from typing import Dict, List


class MockData:
    """Mock data for testing without external API calls"""
    
    @staticmethod
    def get_animals_items() -> List[str]:
        """Mock AI service response for animals"""
        return [
            'cat', 'dog', 'bird', 'fish', 'elephant', 
            'lion', 'tiger', 'bear', 'rabbit', 'horse',
            'cow', 'pig', 'sheep', 'chicken', 'duck'
        ]
    
    @staticmethod
    def get_body_parts_items() -> List[str]:
        """Mock AI service response for body parts"""
        return [
            'head', 'eyes', 'nose', 'mouth', 'ears', 
            'neck', 'shoulders', 'arms', 'hands', 'fingers',
            'chest', 'stomach', 'back', 'legs', 'knees', 'feet'
        ]
    
    @staticmethod
    def get_colors_items() -> List[str]:
        """Mock AI service response for colors"""
        return [
            'red', 'blue', 'green', 'yellow', 'orange',
            'purple', 'pink', 'brown', 'black', 'white', 'gray'
        ]
    
    @staticmethod
    def get_mock_images(item: str, count: int = 3) -> List[Dict]:
        """Mock image service response"""
        return [
            {
                "id": f"mock_{item}_{i}",
                "url": f"https://example.com/photos/{item}_{i}.jpg",
                "thumbnail": f"https://example.com/photos/{item}_{i}_thumb.jpg",
                "photographer": f"Mock Photographer {i}",
                "source": "pexels",
                "alt": f"Mock {item} image {i}"
            }
            for i in range(count)
        ]
    
    @staticmethod
    def get_mock_session_data() -> Dict:
        """Mock complete session data"""
        items = MockData.get_animals_items()[:5]  # First 5 animals
        return {
            'prompt': 'Animals',
            'items': items,
            'session_id': 'test-session-123',
            'created_at': '2025-10-25T21:00:00',
            'status': 'images_fetched',
            'images': {
                item: MockData.get_mock_images(item) for item in items
            },
            'selected_images': {
                item: MockData.get_mock_images(item)[0] for item in items
            },
            'audio_files': {
                item: f'test_audio_{item}.wav' for item in items
            }
        }


class CachedDataLoader:
    """Load actual cached data for testing"""
    
    def __init__(self, cache_dir: str = 'cache'):
        self.cache_dir = cache_dir
    
    def load_cached_images(self, filename: str = None) -> Dict:
        """Load cached image data"""
        if filename is None:
            # Get first available cache file
            cache_files = [f for f in os.listdir(self.cache_dir) if f.startswith('images_')]
            if not cache_files:
                return {}
            filename = cache_files[0]
        
        cache_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
        return {}
    
    def get_all_cached_images(self) -> Dict[str, List]:
        """Load all cached image data indexed by cache key"""
        cached_data = {}
        for filename in os.listdir(self.cache_dir):
            if filename.startswith('images_'):
                cache_key = filename.replace('images_', '').replace('.json', '')
                cached_data[cache_key] = self.load_cached_images(filename)
        return cached_data


# Test configuration that uses cached data
TEST_CONFIG = {
    'api_keys': {
        'openai': 'test-key',
        'pexels': 'test-key',
        'azure_openai_key': 'test-key',
        'azure_openai_endpoint': 'https://test.openai.azure.com/'
    },
    'azure_tts': {
        'subscription_key': 'test-key',
        'region': 'eastus',
        'voice_name': 'en-US-JennyNeural',
        'language': 'en-US'
    },
    'video': {
        'max_duration_seconds': 120,
        'max_items': 30,
        'image_display_duration': 4,
        'resolution': '1920x1080',
        'fps': 30
    },
    'images': {
        'download_count': 3,
        'preferred_provider': 'pexels',
        'image_size': 'large',
        'search_orientation': 'landscape'
    },
    'cache': {
        'enabled': True,
        'ttl_hours': 24,
        'max_size_mb': 500
    }
}
