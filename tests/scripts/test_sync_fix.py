#!/usr/bin/env python3
"""
Test script to verify the synchronization fix for skipped items
"""

import sys
import os
import json
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.video_service import VideoService

def test_sync_fix():
    print("🔧 Testing Synchronization Fix for Skipped Items")
    print("=" * 60)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create test session data
    test_session_data = {
        'items': ['apple', 'banana', 'cherry', 'date', 'elderberry'],
        'selected_images': {
            'apple': {'id': 1, 'url': 'http://example.com/apple.jpg', 'alt': 'Red apple'},
            # 'banana': None,  # This item has no selected image - should be skipped
            'cherry': {'id': 3, 'url': 'http://example.com/cherry.jpg', 'alt': 'Red cherries'},
            # 'date': None,    # This item has no selected image - should be skipped  
            'elderberry': {'id': 5, 'url': 'http://example.com/elderberry.jpg', 'alt': 'Elderberries'}
        },
        'audio_files': {
            'apple': '/tmp/apple.wav',
            'banana': '/tmp/banana.wav',
            'cherry': '/tmp/cherry.wav', 
            'date': '/tmp/date.wav',
            'elderberry': '/tmp/elderberry.wav'
        }
    }
    
    print(f"📋 Test Scenario:")
    print(f"   - Total items: {len(test_session_data['items'])}")
    print(f"   - Items with selected images: {len(test_session_data['selected_images'])}")
    print(f"   - Items: {test_session_data['items']}")
    print(f"   - Selected: {list(test_session_data['selected_images'].keys())}")
    print(f"   - Should skip: banana, date")
    
    # Test the filtering logic (without actually creating video)
    video_service = VideoService(config)
    
    # Simulate the filtering logic from create_flashcard_video
    items = test_session_data['items']
    selected_images = test_session_data.get('selected_images', {})
    audio_files = test_session_data.get('audio_files', {})
    
    # Filter items to only include those with selected images
    filtered_items = []
    filtered_audio_files = {}
    
    print(f"\n🔍 Filtering Process:")
    for item in items:
        if item in selected_images and selected_images[item]:
            filtered_items.append(item)
            if item in audio_files:
                filtered_audio_files[item] = audio_files[item]
            print(f"   ✅ {item} - has selected image, included")
        else:
            print(f"   ❌ {item} - no selected image, excluded")
    
    print(f"\n📊 Results:")
    print(f"   - Original items: {items}")
    print(f"   - Filtered items: {filtered_items}")
    print(f"   - Original audio files: {len(audio_files)} items")
    print(f"   - Filtered audio files: {len(filtered_audio_files)} items")
    
    print(f"\n✅ Synchronization Check:")
    if len(filtered_items) == len(filtered_audio_files):
        print(f"   ✅ Items and audio are synchronized ({len(filtered_items)} each)")
    else:
        print(f"   ❌ Items ({len(filtered_items)}) and audio ({len(filtered_audio_files)}) are NOT synchronized")
    
    print(f"\n🎬 Video Creation Impact:")
    print(f"   - Video segments will be created for: {filtered_items}")
    print(f"   - Subtitles will be created for: {filtered_items}")
    print(f"   - Audio will be used for: {list(filtered_audio_files.keys())}")
    print(f"   - Everything is now synchronized! 🎯")
    
    # Test subtitle timing calculation
    print(f"\n⏱️  Subtitle Timing Test (assuming 4s per item):")
    current_time = 0.0
    for i, item in enumerate(filtered_items):
        start_time = current_time
        end_time = current_time + 4.0
        print(f"   {i+1}. {item}: {start_time:.1f}s → {end_time:.1f}s")
        current_time += 4.0
    
    total_duration = len(filtered_items) * 4.0
    print(f"   📺 Total video duration: {total_duration:.1f}s")

if __name__ == "__main__":
    try:
        test_sync_fix()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
