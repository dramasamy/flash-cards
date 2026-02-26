"""
Test YouTube upload with better error reporting
"""

import os
import sys
sys.path.insert(0, '.')

from services.youtube_service import YouTubeService
import yaml

def test_youtube_upload():
    # Load config
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Initialize YouTube service
    youtube_service = YouTubeService(config)
    
    if not youtube_service.is_enabled():
        print("❌ YouTube service not enabled")
        return
    
    # Test getting channels
    print("🔍 Testing channel listing...")
    channels = youtube_service.get_available_channels()
    
    if channels:
        print(f"✅ Found {len(channels)} channel(s):")
        for i, channel in enumerate(channels):
            print(f"  {i+1}. {channel['title']} (ID: {channel['id']})")
            print(f"     Type: {channel['type']}, Subscribers: {channel['subscriber_count']}")
    else:
        print("❌ No channels found")
    
    # Test upload with a small test video file (if it exists)
    test_video_files = [
        'output.mp4',
        '../output.mp4',
        'test.mp4'
    ]
    
    test_video = None
    for video_file in test_video_files:
        if os.path.exists(video_file):
            test_video = video_file
            break
    
    if test_video:
        print(f"\n🧪 Testing upload with {test_video}...")
        session_data = {
            'prompt': 'Test Upload',
            'session_id': 'test_session_123'
        }
        
        result = youtube_service.upload_video(test_video, session_data)
        
        if result and 'error' not in result:
            print("✅ Upload test successful!")
            print(f"   Video ID: {result.get('video_id')}")
            print(f"   URL: {result.get('url')}")
        else:
            error = result.get('error') if result else 'Unknown error'
            print(f"❌ Upload test failed: {error}")
    else:
        print("\n⚠️  No test video file found - skipping upload test")
        print("   Looked for: " + ", ".join(test_video_files))

if __name__ == "__main__":
    test_youtube_upload()
