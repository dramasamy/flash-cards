#!/usr/bin/env python3
"""
Test the improved fallback logic
"""

import sys
import os
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.ai_service import AIService

def test_fallback_logic():
    print("🧪 Testing Improved Fallback Logic")
    print("=" * 50)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    ai_service = AIService(config)
    
    # Test different prompts that should map to appropriate fallbacks
    test_cases = [
        ("Season", "Should return seasonal items"),
        ("Weather", "Should return weather items"),
        ("Nature", "Should return nature items"),
        ("Animals", "Should return animal items"),
        ("Body parts", "Should return body part items"),
        ("Random unknown topic", "Should return nature items as default")
    ]
    
    for prompt, expected in test_cases:
        print(f"\n🔍 Testing fallback for '{prompt}' - {expected}")
        
        # Call the fallback method directly to test logic
        items = ai_service._get_fallback_items(prompt, 10)
        
        print(f"   ✅ Got {len(items)} items: {items[:5]}{'...' if len(items) > 5 else ''}")
        
        # Check if items seem appropriate
        first_few = ' '.join(items[:3]).lower()
        if prompt.lower() == 'season':
            if any(word in first_few for word in ['spring', 'summer', 'autumn', 'winter', 'snow', 'flowers']):
                print(f"   ✅ Items seem appropriate for seasonal content")
            else:
                print(f"   ⚠️  Items might not be seasonal: {first_few}")

if __name__ == "__main__":
    test_fallback_logic()
