"""
Check available YouTube channels for the authenticated user
"""

import pickle
import os
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def check_channels():
    try:
        # Load existing credentials
        token_file = 'youtube_token.pickle'
        if not os.path.exists(token_file):
            print("❌ No YouTube token found. Please run the app first to authenticate.")
            return
        
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh if needed
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Get all channels the user has access to
        print("🔍 Checking available channels...")
        
        # Get channels the user owns/manages
        request = youtube.channels().list(
            part='snippet,contentDetails,statistics,brandingSettings',
            mine=True,
            maxResults=50
        )
        response = request.execute()
        
        print(f"\n📺 Found {len(response.get('items', []))} channel(s):")
        print("=" * 80)
        
        for i, channel in enumerate(response.get('items', [])):
            snippet = channel['snippet']
            stats = channel.get('statistics', {})
            
            print(f"\n{i+1}. Channel: {snippet['title']}")
            print(f"   ID: {channel['id']}")
            print(f"   Description: {snippet.get('description', 'No description')[:100]}...")
            print(f"   Subscribers: {stats.get('subscriberCount', 'Hidden')}")
            print(f"   Videos: {stats.get('videoCount', '0')}")
            print(f"   Views: {stats.get('viewCount', '0')}")
            print(f"   Created: {snippet.get('publishedAt', 'Unknown')}")
            
            # Check if this is a brand account
            branding = channel.get('brandingSettings', {})
            if branding:
                print(f"   Brand Account: {branding.get('channel', {}).get('title', 'N/A')}")
        
        # Also check if user manages any other channels
        print("\n" + "=" * 80)
        print("🔍 Checking managed channels...")
        
        try:
            request = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                managedByMe=True,
                maxResults=50
            )
            managed_response = request.execute()
            
            managed_channels = managed_response.get('items', [])
            if managed_channels:
                print(f"📺 Found {len(managed_channels)} managed channel(s):")
                for i, channel in enumerate(managed_channels):
                    snippet = channel['snippet']
                    print(f"\n{i+1}. Managed Channel: {snippet['title']}")
                    print(f"   ID: {channel['id']}")
            else:
                print("No additional managed channels found.")
                
        except Exception as e:
            print(f"Note: Could not check managed channels: {e}")
        
    except Exception as e:
        print(f"❌ Error checking channels: {e}")

if __name__ == "__main__":
    check_channels()
