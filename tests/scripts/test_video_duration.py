"""
Test video duration limiting functionality
"""

import sys
sys.path.insert(0, '.')

import yaml
from services.video_service import VideoService

def test_video_duration_config():
    # Load config
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Initialize video service
    video_service = VideoService(config)
    
    print("🎬 Video Duration Configuration Test")
    print("=" * 50)
    print(f"Image display duration: {video_service.image_display_duration}s")
    print(f"Video clip duration: {video_service.video_clip_duration}s")
    print(f"Video clip min duration: {video_service.video_clip_min_duration}s")
    print(f"Video clip max duration: {video_service.video_clip_max_duration}s")
    
    # Test duration calculation logic
    print("\n🧪 Testing Duration Logic:")
    print("=" * 30)
    
    # Simulate different audio durations
    test_cases = [
        ("Very short audio", 1.5),
        ("Short audio", 2.5), 
        ("Normal audio", 3.2),
        ("Long audio", 6.0),
        ("Very long audio", 10.0)
    ]
    
    for description, audio_duration in test_cases:
        # Simulate the duration calculation logic from the video service
        enforced_duration = max(video_service.video_clip_min_duration, 
                              min(video_service.video_clip_max_duration, audio_duration))
        
        print(f"{description:15} | Audio: {audio_duration:4.1f}s → Video: {enforced_duration:4.1f}s")
    
    print("\n✅ Configuration loaded successfully!")
    print(f"Videos will be trimmed to {video_service.video_clip_min_duration}-{video_service.video_clip_max_duration} seconds")
    print(f"Default video clip duration: {video_service.video_clip_duration}s (when no audio)")

if __name__ == "__main__":
    test_video_duration_config()
