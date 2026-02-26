#!/usr/bin/env python3
"""
Test script to debug the progress page issue
"""

import sys
import os
import json
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

def debug_progress_issue():
    print("🔍 Debugging Progress Page Issue")
    print("=" * 50)
    
    # Find the most recent session
    temp_dir = '/Users/dramasam/Documents/github/pexel/flash/temp'
    
    if not os.path.exists(temp_dir):
        print("❌ Temp directory not found")
        return
    
    session_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
    
    if not session_dirs:
        print("❌ No session directories found")
        return
    
    # Get the most recent session
    latest_session = max(session_dirs, key=lambda x: os.path.getmtime(os.path.join(temp_dir, x)))
    session_file = os.path.join(temp_dir, latest_session, 'session.json')
    
    print(f"📁 Testing session: {latest_session}")
    
    if not os.path.exists(session_file):
        print(f"❌ Session file not found: {session_file}")
        return
    
    try:
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        print(f"✅ Session data loaded successfully")
        print(f"📋 Status: {session_data.get('status', 'UNKNOWN')}")
        
        # Test the problematic fields
        items = session_data.get('items', None)
        selected_images = session_data.get('selected_images', None)
        
        print(f"\n🔍 Field Analysis:")
        print(f"   items: {type(items)} - {items}")
        print(f"   selected_images: {type(selected_images)} - {list(selected_images.keys()) if isinstance(selected_images, dict) else selected_images}")
        
        # Test length operations
        print(f"\n📏 Length Tests:")
        try:
            items_len = len(items) if items else 0
            print(f"   len(items): {items_len} ✅")
        except Exception as e:
            print(f"   len(items): ERROR - {e} ❌")
        
        try:
            selected_len = len(selected_images) if selected_images else 0
            print(f"   len(selected_images): {selected_len} ✅")
        except Exception as e:
            print(f"   len(selected_images): ERROR - {e} ❌")
        
        # Test template-like access
        print(f"\n🖼️  Template-like Tests:")
        try:
            # Simulate Jinja2 filter
            result = len(items) if items else 0
            print(f"   items|length simulation: {result} ✅")
        except Exception as e:
            print(f"   items|length simulation: ERROR - {e} ❌")
        
        try:
            result = len(selected_images) if selected_images else 0
            print(f"   selected_images|length simulation: {result} ✅")
        except Exception as e:
            print(f"   selected_images|length simulation: ERROR - {e} ❌")
        
        print(f"\n💡 Suggestions:")
        print(f"   1. Try accessing /debug/{latest_session} in browser")
        print(f"   2. Check Flask logs for more detailed error messages")
        print(f"   3. If session data looks good, the issue might be in template rendering")
        
    except Exception as e:
        print(f"❌ Error loading session data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_progress_issue()
