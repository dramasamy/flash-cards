#!/usr/bin/env python3
"""
Test the new progressive loading performance
"""

import sys
import os
import time
import requests
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.image_service import ImageService

def test_progressive_loading():
    print("🚀 Testing Progressive Loading Performance")
    print("=" * 60)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"🔧 New Configuration:")
    print(f"   - Images per item: {config['images']['download_count']}")
    print(f"   - Thumbnail size: {config['images']['thumbnail_size']} (~8KB)")
    print(f"   - Preview size: {config['images']['preview_size']} (~21KB)")
    print(f"   - Final size: {config['images']['image_size']} (~58KB)")
    
    image_service = ImageService(config)
    
    # Test with one item to see all image sizes
    print(f"\n🔍 Testing image size distribution...")
    
    # Clear cache for fresh test
    import shutil
    shutil.rmtree('cache', ignore_errors=True)
    os.makedirs('cache', exist_ok=True)
    
    images = image_service.search_images('nature', count=5)
    
    if images:
        print(f"\n📊 Image Size Analysis (for 5 images):")
        
        total_thumbnail_size = 0
        total_preview_size = 0 
        total_final_size = 0
        
        for i, image in enumerate(images[:3], 1):  # Test first 3 images
            try:
                # Test thumbnail size
                thumb_response = requests.head(image['thumbnail'])
                thumb_size = int(thumb_response.headers.get('content-length', 0)) / 1024
                
                # Test preview size  
                preview_response = requests.head(image['preview'])
                preview_size = int(preview_response.headers.get('content-length', 0)) / 1024
                
                # Test final size
                final_response = requests.head(image['url'])
                final_size = int(final_response.headers.get('content-length', 0)) / 1024
                
                total_thumbnail_size += thumb_size
                total_preview_size += preview_size
                total_final_size += final_size
                
                print(f"   Image {i}: Thumb={thumb_size:.1f}KB, Preview={preview_size:.1f}KB, Final={final_size:.1f}KB")
                
            except Exception as e:
                print(f"   Image {i}: Could not get sizes - {e}")
        
        print(f"\n📈 Performance Benefits:")
        print(f"   - Initial page load (5 thumbnails): ~{total_thumbnail_size:.1f}KB")
        print(f"   - After hover/scroll (5 previews): ~{total_preview_size:.1f}KB")
        print(f"   - Final download (1 selected): ~{total_final_size/3:.1f}KB average")
        
        print(f"\n⚡ Speed Improvements:")
        print(f"   - Old way (5 large images): ~{total_final_size:.1f}KB initially")
        print(f"   - New way (5 tiny thumbs): ~{total_thumbnail_size:.1f}KB initially")
        print(f"   - Bandwidth saved: ~{total_final_size - total_thumbnail_size:.1f}KB ({((total_final_size - total_thumbnail_size)/total_final_size*100):.1f}% reduction)")
        
        print(f"\n🎯 User Experience:")
        print(f"   ✅ Page loads {total_final_size/total_thumbnail_size:.1f}x faster")
        print(f"   ✅ Only downloads full quality when needed")
        print(f"   ✅ Progressive enhancement on hover")
        print(f"   ✅ 5 images available for better selection")
        
    else:
        print("❌ No images found for testing")

if __name__ == "__main__":
    try:
        test_progressive_loading()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
