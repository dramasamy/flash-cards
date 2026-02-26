#!/usr/bin/env python3
"""
Debug script to check YouTube upload availability
"""

import sys
import os
import json
sys.path.append('/Users/dramasam/Documents/github/pexel/flash')

import yaml
from services.youtube_service import YouTubeService

def debug_youtube_setup():
    print("🔍 Debugging YouTube Upload Setup")
    print("=" * 50)
    
    # Load config
    with open('/Users/dramasam/Documents/github/pexel/flash/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"📋 YouTube Configuration:")
    youtube_config = config.get('youtube', {})
    print(f"   - Enabled: {youtube_config.get('enabled', False)}")
    print(f"   - Auto upload: {youtube_config.get('auto_upload', False)}")
    print(f"   - Client secrets file: {youtube_config.get('client_secrets_file', 'N/A')}")
    print(f"   - Upload privacy: {youtube_config.get('upload_privacy', 'N/A')}")
    
    # Check if client secrets file exists
    secrets_file = youtube_config.get('client_secrets_file', 'youtube_client_secrets.json')
    secrets_path = os.path.join('/Users/dramasam/Documents/github/pexel/flash', secrets_file)
    
    if os.path.exists(secrets_path):
        print(f"   ✅ Client secrets file exists: {secrets_path}")
        try:
            with open(secrets_path, 'r') as f:
                secrets = json.load(f)
                if 'web' in secrets or 'installed' in secrets:
                    print(f"   ✅ Client secrets file format is valid")
                else:
                    print(f"   ❌ Client secrets file format is invalid")
        except Exception as e:
            print(f"   ❌ Error reading client secrets: {e}")
    else:
        print(f"   ❌ Client secrets file not found: {secrets_path}")
    
    # Try to initialize YouTube service
    print(f"\n🔧 Testing YouTube Service Initialization:")
    try:
        youtube_service = YouTubeService(config)
        print(f"   ✅ YouTube service initialized successfully")
    except Exception as e:
        print(f"   ❌ Error initializing YouTube service: {e}")
    
    # Check recent session files to see their status
    print(f"\n📁 Checking Recent Session Files:")
    temp_dir = '/Users/dramasam/Documents/github/pexel/flash/temp'
    
    if os.path.exists(temp_dir):
        sessions = []
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                session_file = os.path.join(item_path, 'session.json')
                if os.path.exists(session_file):
                    try:
                        with open(session_file, 'r') as f:
                            session_data = json.load(f)
                            sessions.append({
                                'id': item,
                                'status': session_data.get('status', 'unknown'),
                                'prompt': session_data.get('prompt', 'N/A'),
                                'created_at': session_data.get('created_at', 'N/A'),
                                'has_video': 'video_path' in session_data,
                                'has_youtube': 'youtube_info' in session_data
                            })
                    except:
                        continue
        
        if sessions:
            sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            print(f"   Found {len(sessions)} recent sessions:")
            
            for i, session in enumerate(sessions[:5], 1):  # Show last 5
                status_icon = "✅" if session['status'] == 'video_created' else "⏳" if session['status'] in ['downloaded', 'video_created'] else "❓"
                youtube_icon = "📺" if session['has_youtube'] else "⭕"
                print(f"   {i}. {status_icon} {session['id'][:8]}... - Status: {session['status']} - {session['prompt']} {youtube_icon}")
                
                if session['status'] == 'video_created':
                    print(f"      💡 This session should show YouTube upload button!")
        else:
            print(f"   ❌ No session files found")
    else:
        print(f"   ❌ Temp directory not found: {temp_dir}")
    
    print(f"\n💡 Troubleshooting Tips:")
    print(f"   1. Make sure you complete the video creation process")
    print(f"   2. The YouTube upload button appears when status = 'video_created'")
    print(f"   3. Check that YouTube is enabled in config.yaml")
    print(f"   4. Ensure youtube_client_secrets.json is properly configured")

if __name__ == "__main__":
    try:
        debug_youtube_setup()
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
