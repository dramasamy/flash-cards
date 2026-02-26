import requests
import os
import json
import random
from typing import List, Dict
from urllib.parse import urlparse
import hashlib


class ImageService:
    def __init__(self, config):
        self.config = config
        self.pexels_api_key = config['api_keys'].get('pexels')
        self.unsplash_api_key = config['api_keys'].get('unsplash')
        self.pixabay_api_key = config['api_keys'].get('pixabay')
        self.preferred_provider = config['images'].get('preferred_provider', 'pexels')
        self.content_type = config['images'].get('content_type', 'image')  # 'image' or 'video'
    
    def search_content(self, query: str, count: int = 3) -> List[Dict]:
        """
        Search for images or videos using the configured provider
        
        Args:
            query: Search term
            count: Number of items to fetch
            
        Returns:
            List of content data dictionaries
        """
        if self.content_type == 'video':
            return self.search_videos(query, count)
        else:
            return self.search_images(query, count)
    
    def search_images(self, query: str, count: int = 3) -> List[Dict]:
        """
        Search for images using the configured provider
        
        Args:
            query: Search term
            count: Number of images to fetch
            
        Returns:
            List of image data dictionaries
        """
        try:
            # Check cache first - include provider and orientation for better uniqueness
            cache_key_string = f"{self.preferred_provider}_{query}_{count}_{self.config['images'].get('search_orientation', 'landscape')}_{self.config['images'].get('image_size', 'large')}"
            cache_key = hashlib.md5(cache_key_string.encode()).hexdigest()
            cache_file = os.path.join('cache', f'images_{cache_key}.json')
            
            print(f"🔍 Searching for '{query}' (count={count})")
            print(f"📦 Cache key: {cache_key}")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    print(f"✅ Loaded {len(cached_data)} images from cache for '{query}'")
                    # Debug: show first image ID to verify correctness
                    if cached_data:
                        print(f"   First image: ID {cached_data[0]['id']} - {cached_data[0]['alt'][:50]}...")
                    
                    # Add default images if enabled in config
                    if self.config['images'].get('include_defaults', False) and cached_data:
                        default_images = self.get_default_images(count=1)
                        if default_images:
                            cached_data.extend(default_images)
                            print(f"➕ Added {len(default_images)} default image(s) to cached results")
                    
                    return cached_data
            
            # Fetch new images
            if self.preferred_provider == 'pexels' and self.pexels_api_key:
                images = self._search_pexels(query, count)
            elif self.preferred_provider == 'unsplash' and self.unsplash_api_key:
                images = self._search_unsplash(query, count)
            elif self.preferred_provider == 'pixabay' and self.pixabay_api_key:
                images = self._search_pixabay(query, count)
            else:
                # Try fallback providers
                images = self._search_fallback(query, count)
            
            # Add default images if enabled in config
            if self.config['images'].get('include_defaults', False) and images:
                default_images = self.get_default_images(count=1)
                if default_images:
                    images.extend(default_images)
                    print(f"➕ Added {len(default_images)} default image(s) to results")
            
            # Cache the results (without default images to avoid local path issues)
            original_images = [img for img in images if not img.get('is_default', False)]
            if original_images:
                os.makedirs('cache', exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump(original_images, f, indent=2)
                print(f"💾 Cached {len(original_images)} images for '{query}'")
                # Debug: show first image ID to verify correctness
                if original_images:
                    print(f"   First image: ID {original_images[0]['id']} - {original_images[0]['alt'][:50]}...")
            
            return images
            
        except Exception as e:
            print(f"Error searching content: {e}")
            return []
    
    def get_default_images(self, count: int = 1) -> List[Dict]:
        """
        Get random default/placeholder images from the default_images folder
        
        Args:
            count: Number of default images to return
            
        Returns:
            List of default image data dictionaries
        """
        try:
            default_folder = self.config['images'].get('default_images_folder', 'default_images')
            
            if not os.path.exists(default_folder):
                print(f"Default images folder not found: {default_folder}")
                return []
            
            # Get all image files from default folder
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            default_files = []
            
            for file in os.listdir(default_folder):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    default_files.append(file)
            
            if not default_files:
                print(f"No default images found in {default_folder}")
                return []
            
            # Randomly select default images
            selected_files = random.sample(default_files, min(count, len(default_files)))
            
            default_images = []
            for i, filename in enumerate(selected_files):
                filepath = os.path.join(default_folder, filename)
                
                # Create web URLs for serving the default images via Flask route
                web_url = f'/default_images/{filename}'
                
                default_image = {
                    'id': f'default_{i}_{filename}',
                    'url': os.path.abspath(filepath),  # Keep local path for copying
                    'thumbnail': web_url,  # Web URL for browser display
                    'preview': web_url,  # Web URL for browser display
                    'sizes': {'large': web_url}, # Web URL for browser display
                    'photographer': 'Default',
                    'source': 'default',
                    'type': 'image',
                    'alt': f'Default placeholder image ({filename})',
                    'is_default': True  # Flag to identify default images
                }
                
                default_images.append(default_image)
            
            return default_images
            
        except Exception as e:
            print(f"Error getting default images: {e}")
            return []
    
    def search_videos(self, query: str, count: int = 3) -> List[Dict]:
        """
        Search for videos using the configured provider
        
        Args:
            query: Search term
            count: Number of videos to fetch
            
        Returns:
            List of video data dictionaries
        """
        try:
            # Check cache first
            cache_key_string = f"videos_{self.preferred_provider}_{query}_{count}_{self.config['images'].get('search_orientation', 'landscape')}"
            cache_key = hashlib.md5(cache_key_string.encode()).hexdigest()
            cache_file = os.path.join('cache', f'videos_{cache_key}.json')
            
            print(f"🎥 Searching for videos: '{query}' (count={count})")
            print(f"📦 Cache key: {cache_key}")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    print(f"✅ Loaded {len(cached_data)} videos from cache for '{query}'")
                    if cached_data:
                        print(f"   First video: ID {cached_data[0]['id']} - {cached_data[0]['alt'][:50]}...")
                    
                    # Add default images if enabled in config
                    if self.config['images'].get('include_defaults', False) and cached_data:
                        default_images = self.get_default_images(count=1)
                        if default_images:
                            cached_data.extend(default_images)
                            print(f"➕ Added {len(default_images)} default image(s) to cached video results")
                    
                    return cached_data
            
            # Fetch new videos
            if self.preferred_provider == 'pexels' and self.pexels_api_key:
                videos = self._search_pexels_videos(query, count)
            else:
                print(f"Video search not supported for provider: {self.preferred_provider}")
                return []
            
            # Add default images as fallback option if enabled
            if self.config['images'].get('include_defaults', False) and videos:
                default_images = self.get_default_images(count=1)
                if default_images:
                    videos.extend(default_images)
                    print(f"➕ Added {len(default_images)} default image(s) to video results")
            
            # Cache the results (without default images to avoid local path issues)
            original_videos = [video for video in videos if not video.get('is_default', False)]
            if original_videos:
                os.makedirs('cache', exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump(original_videos, f)
                print(f"💾 Cached {len(original_videos)} videos for '{query}'")
            
            print(f"✅ Found {len(videos)} items for '{query}'")
            return videos
            
        except Exception as e:
            print(f"Error searching videos: {e}")
            return []
    
    def _search_pexels_videos(self, query: str, count: int) -> List[Dict]:
        """Search videos using Pexels API"""
        if not self.pexels_api_key:
            print("Pexels API key not configured")
            return []
        
        url = "https://api.pexels.com/videos/search"
        headers = {
            "Authorization": self.pexels_api_key
        }
        params = {
            "query": query,
            "per_page": count,
            "orientation": self.config['images'].get('search_orientation', 'landscape'),
            "size": "medium"  # medium, large, small
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            for video in data.get('videos', []):
                # Get video files - prefer MP4 format
                video_files = video.get('video_files', [])
                mp4_files = [vf for vf in video_files if vf.get('file_type') == 'video/mp4']
                
                if not mp4_files:
                    continue
                
                # Sort by quality and file size (prefer HD but not too large for faster processing)
                sorted_files = sorted(mp4_files, key=lambda x: (
                    -1 if x.get('quality') == 'hd' else 
                    -2 if x.get('quality') == 'sd' else 
                    -3,
                    x.get('width', 0) * x.get('height', 0)  # Prefer smaller resolution for faster processing
                ))
                
                best_file = sorted_files[0]
                
                video_data = {
                    'id': video['id'],
                    'url': best_file['link'],  # Video file URL
                    'thumbnail': video['image'],  # Video preview image
                    'preview': video['image'],  # Same as thumbnail for videos
                    'width': video['width'],
                    'height': video['height'],
                    'duration': video['duration'],
                    'quality': best_file.get('quality', 'unknown'),
                    'file_type': best_file.get('file_type', 'video/mp4'),
                    'file_size': best_file.get('file_size', 0),
                    'resolution': f"{best_file.get('width', video['width'])}x{best_file.get('height', video['height'])}",
                    'photographer': video.get('user', {}).get('name', 'Unknown'),
                    'source': 'pexels',
                    'type': 'video',
                    'alt': f"Video about {query} ({video['duration']}s)"
                }
                
                videos.append(video_data)
            
            return videos
            
        except requests.RequestException as e:
            print(f"Pexels video API error: {e}")
            return []
        except Exception as e:
            print(f"Error processing Pexels video data: {e}")
            return []
    
    def _search_pexels(self, query: str, count: int) -> List[Dict]:
        """Search images using Pexels API"""
        if not self.pexels_api_key:
            print("Pexels API key not configured")
            return []
        
        url = "https://api.pexels.com/v1/search"
        headers = {
            "Authorization": self.pexels_api_key
        }
        params = {
            "query": query,
            "per_page": count,
            "orientation": self.config['images'].get('search_orientation', 'landscape'),
            "size": self.config['images'].get('image_size', 'large')
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for photo in data.get('photos', []):
                # Progressive loading: tiny for initial load, medium for preview, large for final
                thumbnail_size = self.config['images'].get('thumbnail_size', 'tiny')
                preview_size = self.config['images'].get('preview_size', 'medium')
                final_size = self.config['images'].get('image_size', 'large')
                
                image_data = {
                    'id': photo['id'],
                    'url': photo['src'][final_size],  # Full quality for video
                    'thumbnail': photo['src'][thumbnail_size],  # Tiny for fast loading (~8KB)
                    'preview': photo['src'][preview_size],  # Medium for selection preview (~21KB)
                    'sizes': photo['src'],  # All available sizes
                    'photographer': photo['photographer'],
                    'source': 'pexels',
                    'alt': photo.get('alt', query)
                }
                images.append(image_data)
            
            print(f"Found {len(images)} images on Pexels for '{query}'")
            return images
            
        except Exception as e:
            print(f"Error searching Pexels: {e}")
            return []
    
    def _search_unsplash(self, query: str, count: int) -> List[Dict]:
        """Search images using Unsplash API"""
        if not self.unsplash_api_key:
            print("Unsplash API key not configured")
            return []
        
        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {self.unsplash_api_key}"
        }
        params = {
            "query": query,
            "per_page": count,
            "orientation": self.config['images'].get('search_orientation', 'landscape')
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for photo in data.get('results', []):
                image_data = {
                    'id': photo['id'],
                    'url': photo['urls']['regular'],
                    'thumbnail': photo['urls']['small'],
                    'photographer': photo['user']['name'],
                    'source': 'unsplash',
                    'alt': photo.get('alt_description', query)
                }
                images.append(image_data)
            
            print(f"Found {len(images)} images on Unsplash for '{query}'")
            return images
            
        except Exception as e:
            print(f"Error searching Unsplash: {e}")
            return []
    
    def _search_pixabay(self, query: str, count: int) -> List[Dict]:
        """Search images using Pixabay API"""
        if not self.pixabay_api_key:
            print("Pixabay API key not configured")
            return []
        
        url = "https://pixabay.com/api/"
        params = {
            "key": self.pixabay_api_key,
            "q": query,
            "per_page": count,
            "image_type": "photo",
            "orientation": self.config['images'].get('search_orientation', 'horizontal'),
            "safesearch": "true"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for hit in data.get('hits', []):
                image_data = {
                    'id': hit['id'],
                    'url': hit['largeImageURL'],
                    'thumbnail': hit['webformatURL'],
                    'photographer': hit['user'],
                    'source': 'pixabay',
                    'alt': hit.get('tags', query)
                }
                images.append(image_data)
            
            print(f"Found {len(images)} images on Pixabay for '{query}'")
            return images
            
        except Exception as e:
            print(f"Error searching Pixabay: {e}")
            return []
    
    def _search_fallback(self, query: str, count: int) -> List[Dict]:
        """Try fallback providers when primary fails"""
        providers = ['pexels', 'unsplash', 'pixabay']
        
        for provider in providers:
            if provider == self.preferred_provider:
                continue
                
            try:
                if provider == 'pexels' and self.pexels_api_key:
                    images = self._search_pexels(query, count)
                elif provider == 'unsplash' and self.unsplash_api_key:
                    images = self._search_unsplash(query, count)
                elif provider == 'pixabay' and self.pixabay_api_key:
                    images = self._search_pixabay(query, count)
                else:
                    continue
                
                if images:
                    print(f"Using fallback provider: {provider}")
                    return images
                    
            except Exception as e:
                print(f"Fallback provider {provider} failed: {e}")
                continue
        
        return []
    
    def download_image(self, media_data: Dict, session_dir: str) -> str:
        """
        Download an image or video to local storage
        
        Args:
            media_data: Media data dictionary (image or video)
            session_dir: Directory to save the media
            
        Returns:
            Local file path of downloaded media
        """
        try:
            url = media_data['url']
            media_id = media_data['id']
            source = media_data['source']
            media_type = media_data.get('type', 'image')
            is_default = media_data.get('is_default', False)
            
            # Handle default/local images differently
            if is_default and source == 'default':
                # For default images, just copy the local file to session directory
                import shutil
                original_filename = os.path.basename(url)
                filename = f"default_{media_id}_{original_filename}"
                filepath = os.path.join(session_dir, filename)
                
                if not os.path.exists(filepath) and os.path.exists(url):
                    shutil.copy2(url, filepath)
                    print(f"Copied default image: {filename}")
                elif os.path.exists(filepath):
                    print(f"Default image already exists: {filename}")
                else:
                    print(f"Default image source not found: {url}")
                    return None
                    
                return filepath
            
            # Handle regular remote images/videos
            # Create filename with appropriate extension
            if media_type == 'video':
                file_type = media_data.get('file_type', 'video/mp4')
                extension = '.mp4' if 'mp4' in file_type else '.mov'
                filename = f"{source}_{media_id}{extension}"
            else:
                filename = f"{source}_{media_id}.jpg"
                
            filepath = os.path.join(session_dir, filename)
            
            # Download if not exists
            if not os.path.exists(filepath):
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"Downloaded {media_type}: {filename}")
            
            return filepath
            
        except Exception as e:
            print(f"Error downloading {media_data.get('type', 'image')}: {e}")
            return None
