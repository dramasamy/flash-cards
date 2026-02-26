#!/usr/bin/env python3
"""
Test Azure OpenAI configuration
"""

import sys
import os
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.ai_service import AIService

def test_azure_openai():
    print("🧪 Testing Azure OpenAI Configuration")
    print("=" * 50)
    
    try:
        # Load config
        with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        print(f"🔧 Azure OpenAI Key: {'*' * 10 + config['api_keys']['azure_openai_key'][-10:]}")
        print(f"🔧 Azure OpenAI Endpoint: {config['api_keys']['azure_openai_endpoint']}")
        print(f"🔧 Azure OpenAI Deployment: {config['api_keys']['azure_openai_deployment']}")
        
        # Initialize AI service
        ai_service = AIService(config)
        print("✅ AI Service initialized successfully")
        
        # Test with a simple prompt
        print("\n🔍 Testing with 'Season' prompt...")
        items = ai_service.get_items_list("Season", max_items=5)
        
        print(f"✅ Generated {len(items)} items: {items}")
        
        # Check if items are seasonal
        seasonal_words = ['spring', 'summer', 'autumn', 'winter', 'fall', 'snow', 'rain', 'sun', 'leaves', 'flowers']
        items_text = ' '.join(items).lower()
        
        if any(word in items_text for word in seasonal_words):
            print("✅ Items appear to be seasonal!")
        else:
            print("⚠️  Items might not be seasonal, but AI is working")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_azure_openai()
