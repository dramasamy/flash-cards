#!/usr/bin/env python3
"""
Quick test script to demonstrate subtitle clarity improvements
"""

import os
import subprocess
from services.video_service import VideoService
import yaml

def create_test_subtitle():
    """Create a test SRT file with sample content"""
    srt_content = """1
00:00:00,000 --> 00:00:04,000
APPLE

2
00:00:04,000 --> 00:00:08,000
BANANA

3
00:00:08,000 --> 00:00:12,000
CHERRY

4
00:00:12,000 --> 00:00:16,000
DRAGON FRUIT
"""
    
    with open('test_subtitles.srt', 'w') as f:
        f.write(srt_content)
    print("Created test_subtitles.srt")

def create_test_video():
    """Create a simple test video"""
    # Create a 16-second test video with solid color
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'color=c=blue:size=1920x1080:duration=16',
        '-r', '30',
        'test_base_video.mp4'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("Created test_base_video.mp4")
        return True
    else:
        print(f"Error creating test video: {result.stderr}")
        return False

def test_subtitle_styles():
    """Test different subtitle styles for clarity comparison"""
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    video_service = VideoService(config)
    
    # Test 1: Old style (small, basic)
    print("\n=== Testing OLD subtitle style ===")
    cmd_old = [
        'ffmpeg', '-y',
        '-i', 'test_base_video.mp4',
        '-vf', 'subtitles=test_subtitles.srt:force_style=\'FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF&,Outline=2,Shadow=1\'',
        'test_output_old_style.mp4'
    ]
    
    result = subprocess.run(cmd_old, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Created test_output_old_style.mp4 (small, basic subtitles)")
    else:
        print(f"❌ Error: {result.stderr}")
    
    # Test 2: New enhanced style
    print("\n=== Testing NEW enhanced subtitle style ===")
    
    # Get enhanced style configuration
    subtitle_config = config.get('output', {})
    font_name = subtitle_config.get('subtitle_font', 'Arial Bold')
    font_size = subtitle_config.get('subtitle_size', 48)
    font_color = subtitle_config.get('subtitle_color', 'white')
    outline_color = subtitle_config.get('subtitle_outline_color', 'black')
    outline_width = subtitle_config.get('subtitle_outline_width', 3)
    
    # Build enhanced subtitle style
    primary_color = video_service._color_to_hex(font_color)
    outline_color_hex = video_service._color_to_hex(outline_color)
    
    style_parts = [
        f'FontName={font_name}',
        f'FontSize={font_size}',
        f'PrimaryColour=&H{primary_color}&',
        f'OutlineColour=&H{outline_color_hex}&',
        f'Outline={outline_width}',
        'Bold=1',
        'Alignment=2',  # Bottom center
        'MarginV=50',   # Bottom margin
        'Shadow=2',
        'BackColour=&H80000000&',  # Semi-transparent background
        'BorderStyle=4'  # Background box
    ]
    
    subtitle_style = ','.join(style_parts)
    
    cmd_new = [
        'ffmpeg', '-y',
        '-i', 'test_base_video.mp4',
        '-vf', f'subtitles=test_subtitles.srt:force_style=\'{subtitle_style}\'',
        'test_output_new_style.mp4'
    ]
    
    print(f"Enhanced style: {subtitle_style}")
    
    result = subprocess.run(cmd_new, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Created test_output_new_style.mp4 (large, bold, with outline and background)")
    else:
        print(f"❌ Error: {result.stderr}")
    
    print("\n=== Subtitle Clarity Test Complete ===")
    print("Compare these two videos:")
    print("• test_output_old_style.mp4 - Old style (size 24, basic)")
    print("• test_output_new_style.mp4 - New style (size 48, bold, outlined, background)")
    print("\nThe new style should be much clearer and easier to read!")

if __name__ == "__main__":
    print("Subtitle Clarity Test")
    print("====================")
    
    # Create test files
    create_test_subtitle()
    
    if create_test_video():
        test_subtitle_styles()
    
    # Cleanup test files
    cleanup_files = ['test_subtitles.srt', 'test_base_video.mp4']
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")
