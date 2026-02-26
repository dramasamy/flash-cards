#!/usr/bin/env python3
"""
Performance test script for image loading
"""

import sys
import os
import time
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.image_service import ImageService

def test_performance():
    print("🚀 Testing Image Loading Performance")
    print("=" * 60)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"🔧 Configuration:")
    print(f"   - Images per item: {config['images']['download_count']}")
    print(f"   - Image size: {config['images']['image_size']}")
    print(f"   - Thumbnail size: {config['images'].get('thumbnail_size', 'medium')}")
    print(f"   - Provider: {config['images']['preferred_provider']}")
    
    image_service = ImageService(config)
    
    # Test with different numbers of items
    test_queries = ['season', 'nature', 'animal', 'fruit', 'color']
    
    print(f"\n⏱️  Testing Performance with {len(test_queries)} items...")
    
    # Test individual queries
    individual_times = []
    for query in test_queries:
        start = time.time()
        images = image_service.search_images(query, count=config['images']['download_count'])
        duration = time.time() - start
        individual_times.append(duration)
        
        status = "✅" if images else "❌"
        print(f"   {status} '{query}': {len(images)} images in {duration:.2f}s")
    
    total_individual = sum(individual_times)
    print(f"\n📊 Performance Summary:")
    print(f"   - Total time (sequential): {total_individual:.2f}s")
    print(f"   - Average per item: {total_individual/len(test_queries):.2f}s")
    print(f"   - Images per second: {len(test_queries) * config['images']['download_count'] / total_individual:.1f}")
    
    # Test parallel fetching (simulating app.py behavior)
    print(f"\n🔄 Testing Parallel Fetching...")
    from concurrent.futures import ThreadPoolExecutor
    
    def fetch_item_images(query):
        return query, image_service.search_images(query, count=config['images']['download_count'])
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(fetch_item_images, test_queries))
    parallel_time = time.time() - start
    
    print(f"   ⚡ Parallel fetch time: {parallel_time:.2f}s")
    print(f"   🚀 Speedup: {total_individual/parallel_time:.1f}x faster")
    
    # Recommendations
    print(f"\n💡 Performance Recommendations:")
    if total_individual > 10:
        print("   ⚠️  Image loading is slow - consider reducing image count or size")
    else:
        print("   ✅ Image loading performance is good")
    
    if config['images']['download_count'] > 3:
        print("   💡 Consider reducing download_count to 3 for faster loading")
    
    if config['images']['image_size'] == 'large':
        print("   💡 Consider using 'medium' image size for better performance")
        
    if not config['images'].get('thumbnail_size'):
        print("   💡 Consider adding thumbnail_size: 'small' for faster selection page")

if __name__ == "__main__":
    try:
        test_performance()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
