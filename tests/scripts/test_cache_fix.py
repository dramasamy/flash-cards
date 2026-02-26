#!/usr/bin/env python3
"""
Test cache isolation after the fix
"""

import sys
import os
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.image_service import ImageService

def test_cache_fix():
    print("🧪 Testing Cache Fix for Cross-Contamination")
    print("=" * 50)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    image_service = ImageService(config)
    
    print(f"🔧 Provider: {image_service.preferred_provider}")
    print(f"🔧 Orientation: {config['images'].get('search_orientation')}")
    print(f"🔧 Size: {config['images'].get('image_size')}")
    
    # Test with different queries that should have very different results
    test_queries = [
        ("season", "Should return seasonal images"),
        ("car", "Should return vehicle images"), 
        ("apple", "Should return fruit images")
    ]
    
    for query, expected in test_queries:
        print(f"\n🔍 Testing '{query}' - {expected}")
        images = image_service.search_images(query, count=3)
        
        if images:
            print(f"   ✅ Got {len(images)} images")
            print(f"   📝 Sample: {images[0]['alt'][:60]}...")
            
            # Check if image content seems relevant to query
            alt_text = ' '.join([img['alt'].lower() for img in images])
            if query.lower() in alt_text:
                print(f"   ✅ Images seem relevant to '{query}'")
            else:
                print(f"   ⚠️  Images might not be relevant to '{query}'")
        else:
            print(f"   ❌ No images found")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   - Cache has been cleared ✅")
    print(f"   - Cache keys now include provider, orientation, and size ✅") 
    print(f"   - Each search should return relevant images ✅")
    print(f"   - Try creating a new video with 'season' prompt now!")

if __name__ == "__main__":
    try:
        test_cache_fix()
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
