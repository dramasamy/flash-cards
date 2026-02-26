#!/usr/bin/env python3
"""
Quick test to verify image count configuration is working
"""

import yaml
import sys
import os

# Add the parent directory to the path so we can import the services
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

from services.image_service import ImageService

def test_image_count():
    print("Testing Image Count Configuration")
    print("=" * 40)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check config value
    image_count = config['images'].get('download_count', 5)
    print(f"✅ Config download_count: {image_count}")
    
    # Initialize image service
    image_service = ImageService(config)
    
    # Test search for a sample item
    print(f"\n🔍 Testing image search for 'apple' with count={image_count}")
    images = image_service.search_images('apple', count=image_count)
    
    print(f"📊 Results:")
    print(f"   - Requested: {image_count} images")
    print(f"   - Received: {len(images)} images")
    
    if len(images) == image_count:
        print("   ✅ SUCCESS: Got exactly the requested number of images!")
    elif len(images) < image_count:
        print(f"   ⚠️  WARNING: Got fewer images than requested (might be limited by API results)")
    else:
        print(f"   ❌ ERROR: Got more images than requested")
    
    # Show image details
    if images:
        print(f"\n📸 Image Details:")
        for i, img in enumerate(images, 1):
            print(f"   {i}. ID: {img['id']} - by {img['photographer']} ({img['source']})")
    
    return len(images)

if __name__ == "__main__":
    try:
        result_count = test_image_count()
        print(f"\n🎯 SUMMARY: The fix should now show {result_count} images in the UI!")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
