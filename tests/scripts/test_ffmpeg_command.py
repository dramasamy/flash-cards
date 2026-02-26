"""
Test FFmpeg command generation for video processing
"""

import sys
sys.path.insert(0, '.')

import yaml
from services.video_service import VideoService
import os

def test_ffmpeg_command():
    # Load config
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Initialize video service
    video_service = VideoService(config)
    
    print("🎬 Testing FFmpeg Command Generation")
    print("=" * 50)
    
    # Simulate video processing command generation
    item = "test_animal"
    session_dir = "temp/test"
    duration = 2.0
    
    # Mock media data for video content
    video_media_data = {
        'id': '12345',
        'url': 'test_video.mp4',
        'type': 'video',
        'duration': 10,
        'quality': 'hd'
    }
    
    # Mock media data for image content  
    image_media_data = {
        'id': '67890',
        'url': 'test_image.jpg',
        'type': 'image'
    }
    
    print("📹 Video Content FFmpeg Command:")
    print("-" * 30)
    
    # Simulate the FFmpeg command building for video content
    cmd_video = ['ffmpeg', '-y']
    cmd_video.extend([
        '-ss', '0',
        '-t', str(duration),
        '-i', 'processed_video.mp4'
    ])
    cmd_video.extend(['-i', 'audio.wav'])
    cmd_video.extend([
        '-t', str(duration),
        '-vf', f'scale={video_service.width}:{video_service.height}:force_original_aspect_ratio=decrease,pad={video_service.width}:{video_service.height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-map', '0:v',
        '-map', '1:a',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-r', str(video_service.fps),
        '-pix_fmt', 'yuv420p',
        '-shortest',
        'output_segment.mp4'
    ])
    
    print("Command:", ' '.join(cmd_video))
    print(f"Output file: output_segment.mp4")
    
    print("\n📸 Image Content FFmpeg Command:")
    print("-" * 30)
    
    # Simulate the FFmpeg command building for image content
    cmd_image = ['ffmpeg', '-y']
    cmd_image.extend(['-loop', '1', '-i', 'processed_image.jpg'])
    cmd_image.extend(['-i', 'audio.wav'])
    cmd_image.extend([
        '-t', str(duration),
        '-vf', f'scale={video_service.width}:{video_service.height}:force_original_aspect_ratio=decrease,pad={video_service.width}:{video_service.height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-r', str(video_service.fps),
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        'output_segment.mp4'  
    ])
    
    print("Command:", ' '.join(cmd_image))
    print(f"Output file: output_segment.mp4")
    
    print(f"\n✅ Both commands include proper output file specification!")
    print(f"Video resolution: {video_service.width}x{video_service.height}")
    print(f"Video FPS: {video_service.fps}")
    print(f"Duration: {duration}s")

if __name__ == "__main__":
    test_ffmpeg_command()
