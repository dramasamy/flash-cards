"""
YouTube Upload Service
Handles uploading videos to YouTube using the YouTube Data API v3
"""

import os
import pickle
import json
from typing import Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import httplib2
import random
import time

class YouTubeService:
    def __init__(self, config: Dict):
        self.config = config
        self.youtube_config = config.get('youtube', {})
        self.enabled = self.youtube_config.get('enabled', True)
        self.client_secrets_file = self.youtube_config.get('client_secrets_file', 'youtube_client_secrets.json')
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube.readonly'
        ]
        self.youtube = None
        
        if self.enabled:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with YouTube API using OAuth2"""
        try:
            creds = None
            token_file = 'youtube_token.pickle'
            
            # Load existing credentials
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.client_secrets_file):
                        print(f"❌ YouTube client secrets file not found: {self.client_secrets_file}")
                        print("   Please download it from Google Cloud Console and place it in the project root")
                        self.enabled = False
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.youtube = build('youtube', 'v3', credentials=creds)
            print("✅ YouTube API authenticated successfully")
            
        except Exception as e:
            print(f"❌ YouTube authentication failed: {e}")
            self.enabled = False
    
    def upload_video(self, video_path: str, session_data: Dict, channel_id: Optional[str] = None) -> Optional[Dict]:
        """
        Upload video to YouTube
        
        Args:
            video_path: Path to the video file
            session_data: Session data containing prompt and other info
            channel_id: Optional channel ID to upload to (for brand accounts)
            
        Returns:
            Dictionary with video details if successful, None if failed
        """
        if not self.enabled or not self.youtube:
            error_msg = "❌ YouTube upload disabled or not authenticated"
            print(error_msg)
            return {'error': error_msg}
        
        if not os.path.exists(video_path):
            error_msg = f"❌ Video file not found: {video_path}"
            print(error_msg)
            return {'error': error_msg}
        
        try:
            print(f"🚀 Starting YouTube upload process...")
            print(f"   Video path: {video_path}")
            print(f"   Channel ID: {channel_id if channel_id else 'Default channel'}")
            print(f"   File size: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
            # Prepare video metadata
            prompt = session_data.get('prompt', 'Flash Cards')
            
            title_template = self.youtube_config.get('default_title_template', 
                                                   "Flash Cards: {prompt} - Educational Video")
            title = title_template.format(prompt=prompt)
            
            description_template = self.youtube_config.get('default_description', 
                                                         "Educational flash cards video about {prompt}")
            description = description_template.format(prompt=prompt)
            
            tags = self.youtube_config.get('default_tags', [])
            if prompt.lower() not in [tag.lower() for tag in tags]:
                tags.append(prompt.lower())
            
            privacy = self.youtube_config.get('upload_privacy', 'unlisted')
            category_id = self.youtube_config.get('category_id', '27')  # Education
            
            # Create the request body
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy,
                    'selfDeclaredMadeForKids': True  # Educational content is often for kids
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload in a single chunk
                resumable=True,
                mimetype='video/mp4'
            )
            
            print(f"🚀 Starting YouTube upload for: {title}")
            print(f"   Privacy: {privacy}")
            print(f"   File: {os.path.basename(video_path)}")
            
            # Execute the upload
            insert_params = {
                'part': ','.join(body.keys()),
                'body': body,
                'media_body': media
            }
            
            # Note: For regular YouTube accounts, videos are uploaded to the authenticated channel
            # Brand channel support would require different authentication flow
            if channel_id:
                print(f"   Note: Uploading to channel {channel_id} (if authenticated for that channel)")
            
            insert_request = self.youtube.videos().insert(**insert_params)
            
            response = self._resumable_upload(insert_request)
            
            if response:
                video_id = response['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                result = {
                    'video_id': video_id,
                    'url': video_url,
                    'title': title,
                    'privacy': privacy,
                    'upload_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                print(f"✅ Video uploaded successfully!")
                print(f"   Video ID: {video_id}")
                print(f"   URL: {video_url}")
                print(f"   Title: {title}")
                
                return result
            else:
                error_msg = "❌ Upload failed - no response received"
                print(error_msg)
                return {'error': error_msg}
                
        except HttpError as e:
            error_msg = f"❌ YouTube API error: {e}"
            print(error_msg)
            if e.resp.status == 403:
                error_msg += " (This might be due to quota limits or permissions)"
                print("   This might be due to quota limits or permissions")
            elif e.resp.status == 400:
                error_msg += " (Bad request - check video format and metadata)"
                print("   Bad request - check video format and metadata")
            elif e.resp.status == 401:
                error_msg += " (Authentication failed - please re-authenticate)"
                print("   Authentication failed - please re-authenticate")
            return {'error': error_msg}
            
        except Exception as e:
            error_msg = f"❌ Unexpected error during upload: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return {'error': error_msg}
    
    def _resumable_upload(self, insert_request):
        """Handle resumable upload with retry logic"""
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                print(f"   Uploading... (attempt {retry + 1})")
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        return response
                    else:
                        raise HttpError(response.get('error', 'Unknown error'))
                        
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # Retriable HTTP errors
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                    retry += 1
                    if retry > 3:
                        print(f"❌ Max retries exceeded: {error}")
                        break
                    
                    wait_time = random.uniform(1, 2**retry)
                    print(f"   Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise e
                    
            except Exception as e:
                error = f"An error occurred: {e}"
                break
        
        if error:
            print(f"❌ Upload failed: {error}")
        
        return None
    
    def get_available_channels(self) -> list:
        """Get all available channels for the authenticated user"""
        if not self.enabled or not self.youtube:
            return []
        
        channels = []
        try:
            # Get channels the user owns
            request = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True,
                maxResults=50
            )
            response = request.execute()
            
            for channel in response.get('items', []):
                channels.append({
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'subscriber_count': channel['statistics'].get('subscriberCount', 'Hidden'),
                    'video_count': channel['statistics']['videoCount'],
                    'view_count': channel['statistics']['viewCount'],
                    'type': 'owned'
                })
            
            # Also try to get managed channels
            try:
                request = self.youtube.channels().list(
                    part='snippet,statistics',
                    managedByMe=True,
                    maxResults=50
                )
                managed_response = request.execute()
                
                for channel in managed_response.get('items', []):
                    # Avoid duplicates
                    if not any(c['id'] == channel['id'] for c in channels):
                        channels.append({
                            'id': channel['id'],
                            'title': channel['snippet']['title'],
                            'subscriber_count': channel['statistics'].get('subscriberCount', 'Hidden'),
                            'video_count': channel['statistics']['videoCount'],
                            'view_count': channel['statistics']['viewCount'],
                            'type': 'managed'
                        })
            except Exception:
                pass  # managedByMe might not be available for all accounts
                
        except Exception as e:
            print(f"❌ Error getting channels: {e}")
        
        return channels
    
    def get_channel_info(self, channel_id: Optional[str] = None) -> Optional[Dict]:
        """Get information about a specific channel or the default channel"""
        if not self.enabled or not self.youtube:
            return None
        
        try:
            if channel_id:
                request = self.youtube.channels().list(
                    part='snippet,statistics',
                    id=channel_id
                )
            else:
                request = self.youtube.channels().list(
                    part='snippet,statistics',
                    mine=True
                )
            
            response = request.execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'subscriber_count': channel['statistics'].get('subscriberCount', 'Hidden'),
                    'video_count': channel['statistics']['videoCount'],
                    'view_count': channel['statistics']['viewCount']
                }
        except Exception as e:
            print(f"❌ Error getting channel info: {e}")
        
        return None
    
    def is_enabled(self) -> bool:
        """Check if YouTube upload is enabled and authenticated"""
        return self.enabled and self.youtube is not None
