#!/usr/bin/env python3
"""
Test FFmpeg video creation using existing cached data
This allows us to test video generation without running the full application
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from services.video_service import VideoService
from services.image_service import ImageService


def load_config():
    """Load configuration"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)


def create_test_session_data():
    """Create test session data using cached images"""
    # Load some cached image data
    cache_dir = 'cache'
    image_files = [f for f in os.listdir(cache_dir) if f.startswith('images_')]
    
    if not image_files:
        print("No cached image data found!")
        return None
    
    # Instead of trying to guess from image alt text, use the AI service fallback data
    # This simulates what the real app would get from AI
    from services.ai_service import AIService
    
    # Create AI service to get realistic item names
    config = load_config()
    ai_service = AIService(config)
    
    # Use fallback items (which are the same as what AI would generate)
    realistic_items = ai_service._get_fallback_items('animals', 5)  # Get 5 animals
    
    # Load cached images and map them to realistic item names
    cached_images = {}
    
    for i, item_name in enumerate(realistic_items):
        if i < len(image_files):
            cache_path = os.path.join(cache_dir, image_files[i])
            with open(cache_path, 'r') as f:
                images = json.load(f)
            cached_images[item_name] = images
        else:
            # If we run out of cached images, create mock data
            cached_images[item_name] = [{
                "id": f"mock_{item_name}",
                "url": f"https://example.com/{item_name}.jpg",
                "thumbnail": f"https://example.com/{item_name}_thumb.jpg",
                "photographer": "Mock Photographer",
                "source": "pexels",
                "alt": f"A beautiful {item_name}"
            }]
    
    # Create mock audio files (we'll create dummy ones)
    audio_files = {}
    for item in realistic_items:
        audio_files[item] = f"mock_audio_{item}.wav"
    
    # Create session data structure
    session_data = {
        'prompt': 'Test Animals',
        'items': realistic_items,  # Use realistic item names
        'session_id': 'test-ffmpeg-session',
        'created_at': datetime.now().isoformat(),
        'status': 'ready_for_video',
        'images': cached_images,
        'selected_images': {
            item: cached_images[item][0] if cached_images.get(item) else None 
            for item in realistic_items
        },
        'audio_files': audio_files
    }
    
    return session_data


def create_real_audio_files(session_data, session_dir):
    """Create real audio files using Azure TTS for testing"""
    print("Creating real audio files using Azure TTS...")
    
    from services.tts_service import TTSService
    
    try:
        config = load_config()
        tts_service = TTSService(config)
        
        audio_files = {}
        
        for item in session_data['items']:
            print(f"Generating audio for: {item}")
            
            # Generate audio using Azure TTS
            audio_file = tts_service.generate_audio(item, session_dir)
            
            if audio_file and os.path.exists(audio_file):
                audio_files[item] = audio_file
                print(f"✅ Audio created: {os.path.basename(audio_file)}")
            else:
                print(f"⚠️  Failed to create audio for {item}")
                # Create fallback silent audio
                audio_files[item] = create_fallback_silent_audio(item, session_dir)
        
        # Update session data with actual audio files
        session_data['audio_files'] = audio_files
        print(f"Created {len(audio_files)} audio files")
        
    except Exception as e:
        print(f"Error with Azure TTS: {e}")
        print("Falling back to silent audio files...")
        create_fallback_silent_audio_files(session_data, session_dir)


def create_fallback_silent_audio(item, session_dir):
    """Create a single silent audio file as fallback"""
    silent_audio_path = os.path.join(session_dir, f"silent_{item}.wav")
    
    import subprocess
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-t', '2',  # 2 seconds
        '-c:a', 'pcm_s16le',
        silent_audio_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return silent_audio_path
    except Exception as e:
        print(f"Error creating fallback audio: {e}")
    
    return None


def create_fallback_silent_audio_files(session_data, session_dir):
    """Create dummy audio files for testing (fallback)"""
    print("Creating fallback silent audio files...")
    
    # Create a very short silent audio file using FFmpeg
    silent_audio_path = os.path.join(session_dir, 'silent.wav')
    
    import subprocess
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-t', '2',  # 2 seconds
        '-c:a', 'pcm_s16le',
        silent_audio_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Created silent audio file: {silent_audio_path}")
            
            # Copy this file for each item
            for item in session_data['items']:
                audio_file = os.path.join(session_dir, f"silent_{item}.wav") 
                shutil.copy2(silent_audio_path, audio_file)
                session_data['audio_files'][item] = audio_file
        else:
            print(f"Failed to create silent audio: {result.stderr}")
            # Fallback: create empty audio files dict
            session_data['audio_files'] = {}
    except Exception as e:
        print(f"Error creating dummy audio: {e}")
        session_data['audio_files'] = {}


def test_audio_generation():
    """Test Azure TTS audio generation specifically"""
    print("=== Azure TTS Audio Generation Test ===")
    
    config = load_config()
    
    # Check if Azure TTS is configured
    azure_config = config.get('azure_tts', {})
    if not azure_config.get('subscription_key') or not azure_config.get('region'):
        print("❌ Azure TTS not configured in config.yaml")
        return False
    
    print(f"Azure TTS Config:")
    print(f"  Region: {azure_config.get('region')}")
    print(f"  Voice: {azure_config.get('voice_name')}")
    print(f"  Language: {azure_config.get('language')}")
    
    from services.tts_service import TTSService
    from services.ai_service import AIService
    
    try:
        tts_service = TTSService(config)
        ai_service = AIService(config)
        
        # Get a few test items
        test_items = ai_service._get_fallback_items('animals', 3)
        print(f"Testing audio generation for: {test_items}")
        
        temp_dir = tempfile.mkdtemp(prefix='audio_test_')
        
        generated_files = []
        for item in test_items:
            print(f"Generating audio for: {item}")
            
            audio_file = tts_service.generate_audio(item, temp_dir)
            
            if audio_file and os.path.exists(audio_file):
                print(f"✅ Audio generated: {os.path.basename(audio_file)}")
                generated_files.append(audio_file)
                
                # Get audio duration
                try:
                    duration = tts_service.get_audio_duration(audio_file)
                    print(f"   Duration: {duration:.2f} seconds")
                except:
                    print("   Duration: unknown")
            else:
                print(f"❌ Failed to generate audio for: {item}")
        
        success = len(generated_files) == len(test_items)
        if success:
            print(f"✅ All {len(test_items)} audio files generated successfully")
        else:
            print(f"⚠️  Only {len(generated_files)}/{len(test_items)} audio files generated")
        
        return success
        
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_subtitle_creation():
    """Test subtitle creation specifically"""
    print("=== Subtitle Creation Test ===")
    
    config = load_config()
    video_service = VideoService(config)
    
    # Use realistic AI-generated item names (same as real app would use)
    from services.ai_service import AIService
    ai_service = AIService(config)
    items = ai_service._get_fallback_items('animals', 3)  # Get 3 realistic animal names
    
    audio_files = {
        item: f'mock_audio_{item}.wav' for item in items
    }
    
    temp_dir = tempfile.mkdtemp(prefix='subtitle_test_')
    session_dir = os.path.join(temp_dir, 'test_session')
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        print("Creating test subtitle file...")
        subtitle_path = video_service._create_subtitles(items, audio_files, session_dir)
        
        if subtitle_path and os.path.exists(subtitle_path):
            print(f"✅ Subtitle file created: {subtitle_path}")
            
            # Read and display subtitle content
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("Subtitle content:")
            print("-" * 40)
            print(content)
            print("-" * 40)
            return True
        else:
            print("❌ Subtitle creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Subtitle error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_creation():
    """Test video creation with cached data and subtitles"""
    print("=== FFmpeg Video Creation Test (with Subtitles) ===")
    print("Using cached data to test video generation...")
    
    # Load config
    config = load_config()
    
    # Create session data from cached images
    session_data = create_test_session_data()
    if not session_data:
        print("Could not create test session data")
        return False
    
    print(f"Test session created with {len(session_data['items'])} items:")
    for item in session_data['items']:
        print(f"  - {item}")
    
    # Create temporary session directory
    temp_dir = tempfile.mkdtemp(prefix='ffmpeg_test_')
    session_dir = os.path.join(temp_dir, 'test_session')
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        # Create real audio files using Azure TTS
        create_real_audio_files(session_data, session_dir)
        
        # Initialize video service
        print("\nInitializing VideoService...")
        video_service = VideoService(config)
        
        print(f"Video config:")
        print(f"  Resolution: {video_service.resolution}")
        print(f"  FPS: {video_service.fps}")
        print(f"  Duration per image: {video_service.image_display_duration}s")
        
        # Show subtitle config
        subtitle_config = config.get('output', {})
        print(f"Subtitle config:")
        print(f"  Font: {subtitle_config.get('subtitle_font', 'Arial')}")
        print(f"  Size: {subtitle_config.get('subtitle_size', 24)}")
        print(f"  Color: {subtitle_config.get('subtitle_color', 'white')}")
        
        # Test video creation
        print(f"\nCreating test video with subtitles...")
        print(f"Session directory: {session_dir}")
        
        video_path = video_service.create_flashcard_video(session_data, session_dir)
        
        if video_path and os.path.exists(video_path):
            print(f"\n✅ SUCCESS: Video with subtitles created successfully!")
            print(f"Video path: {video_path}")
            
            # Check if subtitle file was created
            subtitle_path = os.path.join(session_dir, 'subtitles.srt')
            if os.path.exists(subtitle_path):
                print(f"✅ Subtitle file found: {subtitle_path}")
                
                # Show first few lines of subtitle
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:10]  # First 10 lines
                print("Subtitle preview:")
                for line in lines:
                    print(f"  {line.strip()}")
            else:
                print("⚠️  No subtitle file found")
            
            # Get video info
            import subprocess
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video_path]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    format_info = info.get('format', {})
                    video_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'video']
                    audio_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
                    
                    print(f"Video duration: {format_info.get('duration', 'unknown')} seconds")
                    print(f"Video streams: {len(video_streams)}")
                    print(f"Audio streams: {len(audio_streams)}")
                    
                    if video_streams:
                        vs = video_streams[0]
                        print(f"Video resolution: {vs.get('width')}x{vs.get('height')}")
                        print(f"Video codec: {vs.get('codec_name')}")
                    
                    if audio_streams:
                        aus = audio_streams[0]
                        print(f"Audio codec: {aus.get('codec_name')}")
                        print(f"Audio sample rate: {aus.get('sample_rate')}")
                        
                    # Check if video has subtitles embedded
                    subtitle_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'subtitle']
                    if subtitle_streams:
                        print(f"✅ Embedded subtitle streams: {len(subtitle_streams)}")
                    else:
                        print("ℹ️  Subtitles burned into video (not embedded as separate stream)")
                        
            except Exception as e:
                print(f"Could not get video info: {e}")
            
            return True
        else:
            print(f"\n❌ FAILED: Video was not created")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup (but keep video file for inspection)
        print(f"\nCleanup: Temporary files in {temp_dir}")
        print("(Keeping files for inspection - you can delete manually)")


def test_single_segment():
    """Test creating just one video segment"""
    print("\n=== Single Segment Test ===")
    
    config = load_config()
    video_service = VideoService(config)
    
    # Create test session data with just one item
    session_data = create_test_session_data()
    if not session_data:
        return False
    
    # Use just first item
    first_item = session_data['items'][0]
    session_data['items'] = [first_item]
    session_data['selected_images'] = {first_item: session_data['selected_images'][first_item]}
    
    temp_dir = tempfile.mkdtemp(prefix='segment_test_')
    session_dir = os.path.join(temp_dir, 'test_session')
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        create_real_audio_files(session_data, session_dir)
        
        print(f"Testing single segment for: {first_item}")
        
        # Test single segment creation
        image_data = session_data['selected_images'][first_item]
        audio_file = session_data['audio_files'].get(first_item)
        
        segment_path = video_service._create_item_segment(
            first_item,
            image_data,
            audio_file,
            session_dir
        )
        
        if segment_path and os.path.exists(segment_path):
            print(f"✅ Single segment created: {segment_path}")
            return True
        else:
            print(f"❌ Single segment failed")
            return False
            
    except Exception as e:
        print(f"❌ Single segment error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("FFmpeg Test Script")
    print("Testing complete video creation pipeline with Azure TTS and subtitles...")
    
    # Test Azure TTS audio generation first
    print("1. Testing Azure TTS audio generation...")
    success_audio = test_audio_generation()
    
    if success_audio:
        print("\n" + "="*50)
        print("2. Testing subtitle creation...")
        success_subtitle = test_subtitle_creation()
        
        if success_subtitle:
            print("\n" + "="*50)
            print("3. Testing single segment...")
            success_segment = test_single_segment()
            
            if success_segment:
                print("\n" + "="*50)
                print("4. Testing full video with real audio and subtitles...")
                success_full = test_video_creation()
                
                if success_full:
                    print("\n🎉 All tests passed! Complete video creation pipeline is working.")
                    print("✅ Azure TTS audio generation")
                    print("✅ Subtitle creation") 
                    print("✅ Video segment creation")
                    print("✅ Full video with audio and subtitles")
                else:
                    print("\n⚠️  Individual components work but full video creation failed.")
            else:
                print("\n⚠️  Audio and subtitles work but video segment creation failed.")
        else:
            print("\n⚠️  Audio works but subtitle creation failed.")
    else:
        print("\n⚠️  Azure TTS audio generation failed - check configuration.")
        print("Continuing with fallback silent audio for remaining tests...")
        
        # Continue with other tests using fallback audio
        print("\n" + "="*50)
        print("2. Testing subtitle creation...")
        success_subtitle = test_subtitle_creation()
        
        if success_subtitle:
            print("\n" + "="*50)
            print("3. Testing video creation with fallback audio...")
            success_full = test_video_creation()
            
            if success_full:
                print("\n⚠️  Video creation works but using fallback audio (fix Azure TTS)")
            else:
                print("\n❌ Video creation failed even with fallback audio")
    
    print("\nTest complete.")
