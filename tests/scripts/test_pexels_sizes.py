#!/usr/bin/env python3
"""
Test Pexels API image sizes to understand available thumbnails
"""

import requests
import json

def test_pexels_api():
    print("🔍 Testing Pexels API Image Sizes")
    print("=" * 50)
    
    # Your Pexels API key
    api_key = "kwAuD8aJKoF60pgwS3UC4cJ9Iyc5iOHnjQ4ERqQHdsgwQQIKnzB2m7pK"
    
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {
        "query": "nature",
        "per_page": 1,  # Just get one image to examine
        "orientation": "landscape"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('photos'):
            photo = data['photos'][0]
            
            print(f"📸 Photo ID: {photo['id']}")
            print(f"📷 Photographer: {photo['photographer']}")
            print(f"📝 Alt text: {photo.get('alt', 'N/A')}")
            print(f"\n🖼️  Available image sizes:")
            
            src = photo['src']
            for size_name, url in src.items():
                print(f"   {size_name:12}: {url}")
            
            print(f"\n📏 Recommended approach:")
            print(f"   - Selection page: Use '{list(src.keys())[0]}' ({src[list(src.keys())[0]]})")
            print(f"   - Full quality:   Use 'large' for final video")
            
            # Test download size difference
            print(f"\n📊 Size comparison:")
            sizes_to_test = ['tiny', 'small', 'medium', 'large']
            
            for size in sizes_to_test:
                if size in src:
                    try:
                        head_response = requests.head(src[size])
                        content_length = head_response.headers.get('content-length')
                        if content_length:
                            size_kb = int(content_length) / 1024
                            print(f"   {size:8}: ~{size_kb:.1f} KB")
                    except:
                        print(f"   {size:8}: Unable to get size")
                        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_pexels_api()
