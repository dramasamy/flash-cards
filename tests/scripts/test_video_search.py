"""
Test Pexels video search functionality
"""

import sys
sys.path.insert(0, '.')

from services.image_service import ImageService
import yaml

def test_video_search():
    # Load config
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Initialize image service with video content type
    config['images']['content_type'] = 'video'
    image_service = ImageService(config)
    
    # Test video search
    query = "animals"
    count = 3
    
    print(f"🎥 Testing video search for '{query}'...")
    videos = image_service.search_videos(query, count)
    
    if videos:
        print(f"✅ Found {len(videos)} videos:")
        for i, video in enumerate(videos):
            print(f"\n{i+1}. Video ID: {video['id']}")
            print(f"   URL: {video['url']}")
            print(f"   Duration: {video['duration']}s")
            print(f"   Quality: {video['quality']}")
            print(f"   Size: {video['width']}x{video['height']}")
            print(f"   Photographer: {video['photographer']}")
            print(f"   Type: {video['type']}")
    else:
        print("❌ No videos found")
    
    # Test the unified search_content method
    print(f"\n🔍 Testing unified search_content method...")
    content = image_service.search_content(query, count)
    
    if content:
        print(f"✅ Found {len(content)} items via search_content:")
        for i, item in enumerate(content):
            item_type = item.get('type', 'image')
            print(f"{i+1}. {item_type.title()} ID: {item['id']} - {item.get('alt', 'No description')[:50]}...")
    else:
        print("❌ No content found via search_content")

if __name__ == "__main__":
    test_video_search()
