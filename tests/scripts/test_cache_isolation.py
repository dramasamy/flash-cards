#!/usr/bin/env python3  
"""
Quick test to verify the caching bug fix
This will help debug image caching issues
"""

import sys
import os
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.image_service import ImageService

def test_cache_isolation():
    print("🧪 Testing Cache Isolation Fix")
    print("=" * 50)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    image_service = ImageService(config)
    
    print("\n1️⃣  Testing 'car' search...")
    car_images = image_service.search_images('car', count=3)
    print(f"   Found {len(car_images)} car images")
    if car_images:
        print(f"   Sample: {car_images[0]['alt'][:60]}...")
    
    print("\n2️⃣  Testing 'apple' search...")
    apple_images = image_service.search_images('apple', count=3)
    print(f"   Found {len(apple_images)} apple images")
    if apple_images:
        print(f"   Sample: {apple_images[0]['alt'][:60]}...")
    
    print("\n3️⃣  Testing 'brain' search...")
    brain_images = image_service.search_images('brain', count=3)
    print(f"   Found {len(brain_images)} brain images")
    if brain_images:
        print(f"   Sample: {brain_images[0]['alt'][:60]}...")
    
    # Verify they are different
    car_ids = set(img['id'] for img in car_images)
    apple_ids = set(img['id'] for img in apple_images)
    brain_ids = set(img['id'] for img in brain_images)
    
    print(f"\n🔍 Cache Isolation Test:")
    print(f"   Car image IDs:   {sorted(car_ids)}")
    print(f"   Apple image IDs: {sorted(apple_ids)}")
    print(f"   Brain image IDs: {sorted(brain_ids)}")
    
    if car_ids & apple_ids:
        print("   ❌ ERROR: Car and Apple images overlap!")
    elif car_ids & brain_ids:
        print("   ❌ ERROR: Car and Brain images overlap!")
    elif apple_ids & brain_ids:
        print("   ❌ ERROR: Apple and Brain images overlap!")
    else:
        print("   ✅ SUCCESS: All searches returned different images!")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   - Each search term should return relevant images")
    print(f"   - No image IDs should overlap between different searches")
    print(f"   - If you're still seeing wrong images in the UI, use 'Clear Cache & Start Fresh'")

if __name__ == "__main__":
    try:
        test_cache_isolation()
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
