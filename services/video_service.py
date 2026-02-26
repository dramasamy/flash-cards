import os
import subprocess
from typing import Dict, List
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from services.youtube_service import YouTubeService


class VideoService:
    def __init__(self, config):
        self.config = config
        self.resolution = config['video'].get('resolution', '1920x1080')
        self.fps = config['video'].get('fps', 30)
        self.image_display_duration = config['video'].get('image_display_duration', 4)
        self.max_duration = config['video'].get('max_duration_seconds', 120)
        
        # Parse resolution
        self.width = int(config['video']['resolution'].split('x')[0])
        self.height = int(config['video']['resolution'].split('x')[1])
        self.fps = config['video'].get('fps', 30)
        self.image_display_duration = config['video'].get('image_display_duration', 4)
        self.video_clip_duration = config['video'].get('video_clip_duration', 3)
        self.video_clip_min_duration = config['video'].get('video_clip_min_duration', 2)
        self.video_clip_max_duration = config['video'].get('video_clip_max_duration', 5)
        
        # Initialize YouTube service
        self.youtube_service = YouTubeService(config)
    
    def create_flashcard_video(self, session_data: Dict, session_dir: str) -> str:
        """
        Create flashcard video from session data
        
        Args:
            session_data: Session data containing items, images, audio, etc.
            session_dir: Session directory path
            
        Returns:
            Path to created video file
        """
        try:
            items = session_data['items']
            selected_images = session_data.get('selected_images', {})
            audio_files = session_data.get('audio_files', {})
            
            # Filter items to only include those with selected images
            filtered_items = []
            filtered_audio_files = {}
            
            for item in items:
                if item in selected_images and selected_images[item]:
                    filtered_items.append(item)
                    if item in audio_files:
                        filtered_audio_files[item] = audio_files[item]
                else:
                    print(f"⏭️  Excluding '{item}' from video - no image selected")
            
            if not filtered_items:
                raise ValueError("No items with selected images found")
            
            print(f"📝 Creating video with {len(filtered_items)} items (out of {len(items)} total)")
            
            # Create video segments for each filtered item (text overlays are burned-in)
            video_segments = []
            total_duration = 0
            
            for item in filtered_items:
                if total_duration >= self.max_duration:
                    print(f"Reached maximum video duration ({self.max_duration}s)")
                    break
                
                # All filtered items have selected images, so no need to check again
                segment_path = self._create_item_segment(
                    item, 
                    selected_images.get(item),
                    filtered_audio_files.get(item),  # Use filtered audio files
                    session_dir
                )
                
                if segment_path:
                    video_segments.append(segment_path)
                    # Add to total duration (approximate)
                    media_data = selected_images.get(item)
                    is_video_content = media_data and media_data.get('type') == 'video'
                    total_duration += self.video_clip_duration if is_video_content else self.image_display_duration
            
            if not video_segments:
                raise ValueError("No video segments created")
            
            # Concatenate all segments (text overlays already burned-in, no separate subtitles needed)
            final_video_path = self._concatenate_segments(video_segments, session_data, session_dir)
            
            print(f"Flashcard video created: {final_video_path}")
            
            # Only auto-upload to YouTube if explicitly enabled
            youtube_config = self.config.get('youtube', {})
            if youtube_config.get('auto_upload', False):
                youtube_info = self._upload_to_youtube(final_video_path, session_data)
                if youtube_info:
                    session_data['youtube_info'] = youtube_info
                    print(f"✅ Video uploaded to YouTube: {youtube_info['url']}")
            
            return final_video_path
            
        except Exception as e:
            print(f"Error creating flashcard video: {e}")
            raise
    
    def _create_item_segment(self, item: str, media_data: Dict, audio_file: str, session_dir: str) -> str:
        """Create video segment for a single flashcard item"""
        try:
            # Check if we're dealing with video or image content
            is_video_content = media_data and media_data.get('type') == 'video'
            
            if is_video_content:
                # Download and prepare video
                from services.image_service import ImageService
                image_service = ImageService(self.config)
                video_path = image_service.download_image(media_data, session_dir)  # download_image handles both images and videos
                processed_media_path = video_path
            elif media_data:
                # Download and prepare image
                from services.image_service import ImageService
                image_service = ImageService(self.config)
                image_path = image_service.download_image(media_data, session_dir)
                if not image_path or not os.path.exists(image_path):
                    print(f"Image not available for {item}, creating text image")
                    image_path = self._create_text_image(item, session_dir)
                # Prepare image for video
                processed_media_path = self._process_image_for_video(image_path, item, session_dir)
            else:
                # Create text-only image if no media selected
                image_path = self._create_text_image(item, session_dir)
                processed_media_path = self._process_image_for_video(image_path, item, session_dir)
            
            # Determine segment duration
            if audio_file and os.path.exists(audio_file):
                from services.tts_service import TTSService
                tts_service = TTSService(self.config)
                audio_duration = tts_service.get_audio_duration(audio_file)
                
                if is_video_content:
                    # For videos, use audio duration but enforce min/max limits
                    duration = max(self.video_clip_min_duration, 
                                 min(self.video_clip_max_duration, audio_duration))
                    print(f"   Video duration: {duration}s (audio: {audio_duration}s, enforced limits: {self.video_clip_min_duration}-{self.video_clip_max_duration}s)")
                else:
                    # For images, use audio duration as-is
                    duration = audio_duration
            else:
                # No audio - use default durations
                duration = self.video_clip_duration if is_video_content else self.image_display_duration
            
            # Create video segment
            segment_filename = f"segment_{item.replace(' ', '_')}.mp4"
            segment_path = os.path.join(session_dir, segment_filename)
            
            # Build FFmpeg command properly
            cmd = ['ffmpeg', '-y']
            
            if is_video_content:
                # Input 1: Video (with start time and duration control)
                cmd.extend([
                    '-ss', '0',  # Start from beginning (could be randomized later)
                    '-t', str(duration),  # Limit input duration
                    '-i', processed_media_path
                ])
                
                # Input 2: Audio (if available)
                if audio_file and os.path.exists(audio_file):
                    cmd.extend(['-i', audio_file])
                    
                    # Video processing options for video input with audio replacement
                    cmd.extend([
                        '-t', str(duration),  # Ensure output duration matches
                        '-vf', f'scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
                        '-map', '0:v',  # Use video from input 0
                        '-map', '1:a',  # Use audio from input 1
                        '-c:v', 'libx264',
                        '-c:a', 'aac',
                        '-r', str(self.fps),
                        '-pix_fmt', 'yuv420p',
                        '-shortest',  # Stop when shortest stream ends
                        segment_path
                    ])
                else:
                    # Video processing options for video input without audio replacement
                    cmd.extend([
                        '-t', str(duration),
                        '-vf', f'scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
                        '-c:v', 'libx264',
                        '-c:a', 'aac',
                        '-r', str(self.fps),
                        '-pix_fmt', 'yuv420p',
                        segment_path
                    ])
            else:
                # Input 1: Image (looped)
                cmd.extend(['-loop', '1', '-i', processed_media_path])
                
                # Input 2: Audio (if available)
                if audio_file and os.path.exists(audio_file):
                    cmd.extend(['-i', audio_file])
                else:
                    # Add silent audio track
                    cmd.extend(['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100'])
                
                # Video processing options for image input
                cmd.extend([
                    '-t', str(duration),
                    '-vf', f'scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
                    '-r', str(self.fps),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',
                    segment_path
                ])
            
            # Execute FFmpeg command
            print(f"🎬 Running FFmpeg command for {item}:")
            print(f"   Command: {' '.join(cmd[:10])}... (truncated)")
            print(f"   Output: {segment_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ FFmpeg error for {item}:")
                print(f"   Command: {' '.join(cmd)}")
                print(f"   Error: {result.stderr}")
                print(f"   Return code: {result.returncode}")
                return None
            else:
                print(f"✅ Successfully created segment for {item}: {segment_path}")
            
            print(f"Created segment for {item}: {segment_filename}")
            return segment_path
            
        except Exception as e:
            print(f"Error creating segment for {item}: {e}")
            return None
    
    def _process_image_for_video(self, image_path: str, item: str, session_dir: str) -> str:
        """Process image for video: resize, add text overlay, etc."""
        try:
            # Open and process image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image to fit video dimensions while maintaining aspect ratio
            img.thumbnail((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Create new image with video dimensions and center the original
            new_img = Image.new('RGB', (self.width, self.height), color='black')
            
            # Calculate position to center the image
            x = (self.width - img.width) // 2
            y = (self.height - img.height) // 2
            
            new_img.paste(img, (x, y))
            
            # Add text overlay
            new_img = self._add_text_overlay(new_img, item)
            
            # Save processed image
            processed_filename = f"processed_{os.path.basename(image_path)}"
            processed_path = os.path.join(session_dir, processed_filename)
            new_img.save(processed_path, 'JPEG', quality=95)
            
            return processed_path
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return image_path  # Return original if processing fails
    
    def _add_text_overlay(self, img: Image.Image, text: str) -> Image.Image:
        """Add text overlay to image with enhanced styling"""
        try:
            # Create a drawing context
            draw = ImageDraw.Draw(img)
            
            # Get styling configuration
            subtitle_config = self.config.get('output', {})
            font_size = subtitle_config.get('subtitle_size', 48)
            font_color = subtitle_config.get('subtitle_color', 'white')
            outline_color = subtitle_config.get('subtitle_outline_color', 'black')
            outline_width = subtitle_config.get('subtitle_outline_width', 3)
            
            # Try to load a font
            try:
                # Use a bold font for better visibility
                font = ImageFont.truetype("/System/Library/Fonts/Arial Black.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
            
            # Convert text to uppercase for better visibility
            text = text.upper()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position text at bottom center with margin
            x = (self.width - text_width) // 2
            y = self.height - text_height - 60  # 60px from bottom for better positioning
            
            # Draw text with multiple outline layers for better visibility
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
            
            # Draw main text
            draw.text((x, y), text, font=font, fill=font_color)
            
            # Optional: Add a semi-transparent background box for even better readability
            if subtitle_config.get('subtitle_background', True):
                # Create background rectangle
                padding = 10
                bg_x1 = x - padding
                bg_y1 = y - padding
                bg_x2 = x + text_width + padding
                bg_y2 = y + text_height + padding
                
                # Draw semi-transparent black background
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle([bg_x1, bg_y1, bg_x2, bg_y2], fill=(0, 0, 0, 128))
                
                # Composite with original image
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                
                # Redraw text on top of background
                draw = ImageDraw.Draw(img)
                # Redraw outline
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
                # Redraw main text
                draw.text((x, y), text, font=font, fill=font_color)
            
            return img
            
        except Exception as e:
            print(f"Error adding text overlay: {e}")
            return img
    
    def _create_text_image(self, text: str, session_dir: str) -> str:
        """Create image with just text (fallback when no image available)"""
        try:
            # Create new image
            img = Image.new('RGB', (self.width, self.height), color='#2C3E50')  # Dark blue background
            draw = ImageDraw.Draw(img)
            
            # Try to load a large font
            try:
                font_size = max(72, self.height // 15)
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2
            
            # Draw text with shadow
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill='black')
            draw.text((x, y), text, font=font, fill='white')
            
            # Save text image
            text_image_filename = f"text_{text.replace(' ', '_')}.jpg"
            text_image_path = os.path.join(session_dir, text_image_filename)
            img.save(text_image_path, 'JPEG', quality=95)
            
            return text_image_path
            
        except Exception as e:
            print(f"Error creating text image: {e}")
            return None
    
    def _concatenate_segments(self, video_segments: List[str], session_data: Dict, session_dir: str) -> str:
        """Concatenate all video segments into final video"""
        try:
            # Create file list for FFmpeg concat
            concat_file_path = os.path.join(session_dir, 'concat_list.txt')
            
            with open(concat_file_path, 'w') as f:
                for segment in video_segments:
                    f.write(f"file '{os.path.abspath(segment)}'\n")
            
            # Generate output filename
            prompt = session_data.get('prompt', 'flashcards')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"flashcards_{prompt.replace(' ', '_')}_{timestamp}.mp4"
            output_path = os.path.join('output', output_filename)
            
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            
            # FFmpeg concat command
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file_path,
                '-c', 'copy',
                output_path
            ]
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFmpeg concat error: {result.stderr}")
                raise Exception(f"Failed to concatenate video segments: {result.stderr}")
            
            print(f"Final video created: {output_filename}")
            return output_path
            
        except Exception as e:
            print(f"Error concatenating segments: {e}")
            raise
    
    def _create_subtitles(self, items: List[str], audio_files: Dict, session_dir: str) -> str:
        """Create SRT subtitle file for the video"""
        try:
            subtitle_path = os.path.join(session_dir, 'subtitles.srt')
            
            current_time = 0.0
            subtitle_entries = []
            
            for i, item in enumerate(items):
                # Get audio duration or use default
                if audio_files.get(item) and os.path.exists(audio_files[item]):
                    try:
                        duration = self._get_audio_duration(audio_files[item])
                    except:
                        duration = self.image_display_duration
                else:
                    duration = self.image_display_duration
                
                # Create subtitle entry
                start_time = self._seconds_to_srt_time(current_time)
                end_time = self._seconds_to_srt_time(current_time + duration)
                
                subtitle_entries.append(f"{i + 1}")
                subtitle_entries.append(f"{start_time} --> {end_time}")
                subtitle_entries.append(item.upper())  # Display item name in caps
                subtitle_entries.append("")  # Empty line between entries
                
                current_time += duration
            
            # Write subtitle file
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(subtitle_entries))
            
            print(f"Created subtitles file: {subtitle_path}")
            return subtitle_path
            
        except Exception as e:
            print(f"Error creating subtitles: {e}")
            return None
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _get_audio_duration(self, audio_file: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'compact=print_section=0:nokey=1:escape=csv',
                '-show_entries', 'format=duration', audio_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
        return self.image_display_duration
    
    def _add_subtitles_to_video(self, video_path: str, subtitle_path: str, session_data: Dict, session_dir: str) -> str:
        """Add subtitles to the video"""
        try:
            if not subtitle_path or not os.path.exists(subtitle_path):
                print("No subtitle file found, returning video without subtitles")
                return video_path
            
            # Generate final output filename
            prompt = session_data.get('prompt', 'flashcards')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"flashcards_{prompt.replace(' ', '_')}_{timestamp}_with_subs.mp4"
            output_path = os.path.join('output', output_filename)
            
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            
            # Get subtitle configuration from config
            subtitle_config = self.config.get('output', {})
            font_name = subtitle_config.get('subtitle_font', 'Arial Bold')
            font_size = subtitle_config.get('subtitle_size', 48)
            font_color = subtitle_config.get('subtitle_color', 'white')
            outline_color = subtitle_config.get('subtitle_outline_color', 'black')
            outline_width = subtitle_config.get('subtitle_outline_width', 3)
            shadow = subtitle_config.get('subtitle_shadow', True)
            background = subtitle_config.get('subtitle_background', True)
            
            # Build enhanced subtitle style
            primary_color = self._color_to_hex(font_color)
            outline_color_hex = self._color_to_hex(outline_color)
            
            # Enhanced subtitle styling for maximum clarity
            style_parts = [
                f'FontName={font_name}',
                f'FontSize={font_size}',
                f'PrimaryColour=&H{primary_color}&',
                f'OutlineColour=&H{outline_color_hex}&',
                f'Outline={outline_width}',
                'Bold=1',
                'Alignment=2',  # Bottom center
                'MarginV=50'    # Bottom margin
            ]
            
            if shadow:
                style_parts.extend(['Shadow=2', 'BackColour=&H80000000&'])
            
            if background:
                style_parts.append('BorderStyle=4')  # Background box
            
            subtitle_style = ','.join(style_parts)
            
            # FFmpeg command to add subtitles with enhanced styling
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', f'subtitles={subtitle_path}:force_style=\'{subtitle_style}\'',
                '-c:a', 'copy',  # Copy audio without re-encoding
                output_path
            ]
            
            print(f"Adding subtitles to video...")
            print(f"Subtitle config: Font={font_name}, Size={font_size}, Color={font_color}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"FFmpeg subtitle error: {result.stderr}")
                print("Falling back to video without subtitles")
                return video_path
            
            print(f"Added subtitles successfully: {output_filename}")
            return output_path
            
        except Exception as e:
            print(f"Error adding subtitles: {e}")
            return video_path
    
    def _color_to_hex(self, color_name: str) -> str:
        """Convert color name to hex for FFmpeg"""
        colors = {
            'white': 'FFFFFF',
            'black': '000000',
            'red': 'FF0000',
            'green': '00FF00',
            'blue': '0000FF',
            'yellow': 'FFFF00',
            'cyan': '00FFFF',
            'magenta': 'FF00FF',
            'orange': 'FFA500',
            'purple': '800080',
            'pink': 'FFC0CB',
            'brown': 'A52A2A',
            'gray': '808080',
            'grey': '808080',
            'black_transparent': '80000000'  # Semi-transparent black
        }
        return colors.get(color_name.lower(), 'FFFFFF')
    
    def add_intro_outro(self, video_path: str, session_data: Dict) -> str:
        """Add intro and outro to the video (optional enhancement)"""
        # This is a placeholder for future enhancement
        # You could add title screens, credits, etc.
        return video_path
    
    def _upload_to_youtube(self, video_path: str, session_data: Dict) -> Dict:
        """Upload video to YouTube"""
        try:
            if not self.youtube_service.is_enabled():
                print("ℹ️  YouTube upload is disabled or not configured")
                return None
            
            print("🚀 Uploading video to YouTube...")
            youtube_info = self.youtube_service.upload_video(video_path, session_data)
            
            return youtube_info
            
        except Exception as e:
            print(f"❌ YouTube upload failed: {e}")
            return None
