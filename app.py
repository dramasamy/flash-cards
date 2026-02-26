from flask import Flask, render_template, request, jsonify, session, send_file
import yaml
import os
import uuid
from datetime import datetime
import json

from services.ai_service import AIService
from services.image_service import ImageService
from services.tts_service import TTSService
from services.video_service import VideoService
from services.youtube_service import YouTubeService

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Load configuration
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Initialize services
ai_service = AIService(config)
image_service = ImageService(config)
tts_service = TTSService(config)
video_service = VideoService(config)
youtube_service = YouTubeService(config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_flashcards', methods=['POST'])
def create_flashcards():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        max_items = data.get('max_items', config['video']['max_items'])
        content_type = data.get('content_type', 'image')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Clear any existing session data to prevent cross-contamination
        if 'current_session' in session:
            old_session = session['current_session']
            print(f"🧹 Clearing old session: {old_session}")
            del session['current_session']
        
        # Generate session ID for this project
        session_id = str(uuid.uuid4())
        session['current_session'] = session_id
        print(f"🆕 Starting new session: {session_id} for prompt: '{prompt}'")
        
        # Create session directory
        session_dir = os.path.join('temp', session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Get list of items from AI
        items = ai_service.get_items_list(prompt, max_items)
        
        # Validate items
        if not items or not isinstance(items, list):
            return jsonify({'error': 'Failed to generate items from AI'}), 500
            
        # Store items in session
        session_data = {
            'prompt': prompt,
            'items': items,
            'session_id': session_id,
            'content_type': content_type,
            'created_at': datetime.now().isoformat(),
            'status': 'items_generated'
        }
        
        with open(os.path.join(session_dir, 'session.json'), 'w') as f:
            json.dump(session_data, f)
        
        return jsonify({
            'session_id': session_id,
            'items': items,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fetch_images/<session_id>')
def fetch_images(session_id):
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        items = session_data['items']
        content_type = session_data.get('content_type', 'image')
        images_data = {}
        
        # Get image count from configuration
        image_count = config['images'].get('download_count', 5)
        
        # Update image service content type for this session
        original_content_type = image_service.content_type
        image_service.content_type = content_type
        
        # Fetch images for each item (with improved performance)
        from concurrent.futures import ThreadPoolExecutor
        import time
        
        start_time = time.time()
        
        def fetch_item_images(item):
            return item, image_service.search_content(item, count=image_count)
        
        # Use parallel processing for faster image fetching
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(fetch_item_images, items))
        
        for item, images in results:
            images_data[item] = images
        
        fetch_time = time.time() - start_time
        content_label = "videos" if content_type == "video" else "images"
        print(f"⚡ Fetched {content_label} for {len(items)} items in {fetch_time:.2f}s")
        
        # Restore original content type
        image_service.content_type = original_content_type
        
        # Update session data
        session_data['images'] = images_data
        session_data['status'] = 'images_fetched'
        
        with open(os.path.join(session_dir, 'session.json'), 'w') as f:
            json.dump(session_data, f)
        
        return jsonify({
            'session_id': session_id,
            'images': images_data,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/select_images')
def select_images():
    session_id = request.args.get('session_id')
    if not session_id:
        return "Session ID required", 400
    
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        session_file = os.path.join(session_dir, 'session.json')
        
        if not os.path.exists(session_file):
            return f"Session file not found: {session_file}", 404
            
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Validate session data structure
        if 'items' not in session_data:
            return "Session data is incomplete - no items found", 400
            
        items = session_data['items']
        if not isinstance(items, list):
            return f"Session data is invalid - items is not a list: {type(items)}", 400
        
        # Additional validation to ensure items are strings
        for i, item in enumerate(items):
            if not isinstance(item, str):
                return f"Session data is invalid - item {i} is not a string: {type(item)}", 400
        
        # Ensure images data exists and is properly structured
        if 'images' in session_data:
            images = session_data['images']
            if not isinstance(images, dict):
                return f"Session data is invalid - images is not a dict: {type(images)}", 400
        
        print(f"Loading select_images template with {len(items)} items")
        print(f"Session data keys: {list(session_data.keys())}")
        print(f"Items type: {type(session_data['items'])}")
        print(f"Items content: {session_data['items']}")
        
        # Create a safe copy of session_data for template
        safe_session_data = {
            'prompt': session_data.get('prompt', ''),
            'item_list': list(session_data.get('items', [])),  # Rename to avoid conflicts
            'items': list(session_data.get('items', [])),  # Keep original for backward compatibility
            'session_id': session_data.get('session_id', session_id),
            'created_at': session_data.get('created_at', ''),
            'status': session_data.get('status', ''),
            'images': session_data.get('images', {})
        }
        
        print(f"Safe session data items type: {type(safe_session_data['items'])}")
        
        return render_template('select_images.html', 
                             session_data=safe_session_data,
                             session_id=session_id)
    except Exception as e:
        print(f"Error in select_images route: {str(e)}")
        return f"Error loading session: {str(e)}", 500

@app.route('/save_selections', methods=['POST'])
def save_selections():
    try:
        data = request.json
        session_id = data.get('session_id')
        selections = data.get('selections', {})
        
        # Load session data
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        # Save selected images
        session_data['selected_images'] = selections
        session_data['status'] = 'images_selected'
        
        with open(os.path.join(session_dir, 'session.json'), 'w') as f:
            json.dump(session_data, f)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_audio/<session_id>')
def generate_audio(session_id):
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        items = session_data['items']
        selected_images = session_data.get('selected_images', {})
        audio_files = {}
        
        # Only generate audio for items with selected images
        items_to_process = []
        if selected_images:
            # Filter to only items with selected images
            for item in items:
                if item in selected_images and selected_images[item]:
                    items_to_process.append(item)
            print(f"🎵 Generating audio for {len(items_to_process)} items with selected images (out of {len(items)} total)")
        else:
            # If no selections yet, generate for all items (fallback)
            items_to_process = items
            print(f"🎵 Generating audio for all {len(items)} items (no image selections found)")
        
        # Generate audio for filtered items
        for item in items_to_process:
            audio_file = tts_service.generate_audio(item, session_dir)
            audio_files[item] = audio_file
        
        # Update session data
        session_data['audio_files'] = audio_files
        session_data['status'] = 'audio_generated'
        
        with open(os.path.join(session_dir, 'session.json'), 'w') as f:
            json.dump(session_data, f)
        
        return jsonify({
            'session_id': session_id,
            'audio_files': audio_files,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_video/<session_id>')
def create_video(session_id):
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        # Create video
        video_path = video_service.create_flashcard_video(session_data, session_dir)
        
        # Update session data
        session_data['video_path'] = video_path
        session_data['status'] = 'video_created'
        
        with open(os.path.join(session_dir, 'session.json'), 'w') as f:
            json.dump(session_data, f)
        
        return jsonify({
            'session_id': session_id,
            'video_path': video_path,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_video/<session_id>')
def download_video(session_id):
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        video_path = session_data.get('video_path')
        if not video_path or not os.path.exists(video_path):
            return "Video not found", 404
        
        # Update status to downloaded
        session_data['status'] = 'downloaded'
        with open(os.path.join(session_dir, 'session.json'), 'w') as f:
            json.dump(session_data, f)
        
        return send_file(video_path, as_attachment=True, 
                        download_name=f"flashcards_{session_data['prompt']}.mp4")
        
    except Exception as e:
        return f"Error downloading video: {str(e)}", 500

@app.route('/preview_video/<session_id>')
def preview_video(session_id):
    """Serve video file for preview"""
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        session_file = os.path.join(session_dir, 'session.json')
        
        if not os.path.exists(session_file):
            return "Session not found", 404
            
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        video_path = session_data.get('video_path')
        if not video_path:
            return "Video path not found in session", 404
            
        # Convert relative path to absolute path
        if not os.path.isabs(video_path):
            video_path = os.path.abspath(video_path)
            
        if not os.path.exists(video_path):
            return f"Video file not found: {video_path}", 404
            
        # Check file permissions
        if not os.access(video_path, os.R_OK):
            return f"Cannot read video file: {video_path}", 403
        
        print(f"Serving video: {video_path}")
        return send_file(video_path, mimetype='video/mp4', as_attachment=False)
        
    except Exception as e:
        print(f"Error serving video: {e}")
        import traceback
        traceback.print_exc()
        return f"Error serving video: {str(e)}", 500

@app.route('/get_channels/<session_id>')
def get_channels(session_id):
    """Get available YouTube channels for selection"""
    try:
        if not youtube_service.is_enabled():
            return jsonify({'error': 'YouTube service not available'}), 400
        
        channels = youtube_service.get_available_channels()
        return jsonify({
            'success': True,
            'channels': channels
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload_to_youtube/<session_id>', methods=['POST'])
def upload_to_youtube(session_id):
    """Manual YouTube upload endpoint with channel selection"""
    try:
        # Get channel ID from request
        data = request.json if request.is_json else {}
        channel_id = data.get('channel_id')
        
        # Load session data
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        video_path = session_data.get('video_path')
        if not video_path or not os.path.exists(video_path):
            return jsonify({'error': 'Video not found'}), 404
        
        # Use the updated YouTube service directly
        youtube_result = youtube_service.upload_video(video_path, session_data, channel_id)
        
        if youtube_result and 'error' not in youtube_result:
            # Update session data with YouTube info
            session_data['youtube_info'] = youtube_result
            with open(os.path.join(session_dir, 'session.json'), 'w') as f:
                json.dump(session_data, f)
            
            return jsonify({
                'success': True,
                'youtube_info': youtube_result,
                'message': 'Video uploaded to YouTube successfully!'
            })
        else:
            error_msg = youtube_result.get('error', 'Failed to upload to YouTube. Check your configuration and try again.') if youtube_result else 'YouTube upload returned no result'
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/progress/<session_id>')
def progress(session_id):
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        session_file = os.path.join(session_dir, 'session.json')
        
        if not os.path.exists(session_file):
            return f"Session file not found: {session_file}", 404
            
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Debug logging
        print(f"Loading progress for session: {session_id}")
        print(f"Session status: {session_data.get('status', 'UNKNOWN')}")
        print(f"Items type: {type(session_data.get('items', None))}")
        print(f"Selected images type: {type(session_data.get('selected_images', None))}")
        
        # Ensure session_data has required structure
        if 'items' not in session_data:
            session_data['items'] = []
        if 'selected_images' not in session_data:
            session_data['selected_images'] = {}
        
        # Pre-calculate counts to avoid template issues
        items_count = len(session_data['items']) if session_data['items'] else 0
        selected_count = len(session_data['selected_images']) if session_data['selected_images'] else 0
        
        return render_template('progress.html', 
                             session_data=session_data,
                             items_count=items_count,
                             selected_count=selected_count)
        
    except Exception as e:
        print(f"Error in progress route: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error loading progress: {str(e)}", 500

@app.route('/debug/<session_id>')
def debug_session(session_id):
    try:
        session_dir = os.path.join('temp', session_id)
        session_file = os.path.join(session_dir, 'session.json')
        
        if not os.path.exists(session_file):
            return f"Session file not found: {session_file}", 404
            
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        debug_info = {
            'session_id': session_id,
            'status': session_data.get('status', 'UNKNOWN'),
            'keys': list(session_data.keys()),
            'items_type': str(type(session_data.get('items', None))),
            'items_length': len(session_data.get('items', [])) if hasattr(session_data.get('items', []), '__len__') else 'NO_LEN',
            'selected_images_type': str(type(session_data.get('selected_images', None))),
            'selected_images_length': len(session_data.get('selected_images', {})) if hasattr(session_data.get('selected_images', {}), '__len__') else 'NO_LEN',
            'has_video_path': 'video_path' in session_data,
            'video_path': session_data.get('video_path', 'NOT_FOUND')
        }
        
        return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"
        
    except Exception as e:
        return f"Debug error: {str(e)}", 500

@app.route('/api/session_status/<session_id>')
def session_status(session_id):
    try:
        # Load session data
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        return jsonify({
            'status': session_data.get('status', 'unknown'),
            'prompt': session_data.get('prompt', ''),
            'items_count': len(session_data.get('items', [])),
            'created_at': session_data.get('created_at')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<session_id>')
def api_status(session_id):
    """API endpoint to check session status"""
    try:
        session_dir = os.path.join('temp', session_id)
        with open(os.path.join(session_dir, 'session.json'), 'r') as f:
            session_data = json.load(f)
        
        return jsonify({
            'status': session_data.get('status', 'unknown'),
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    """Clear image cache - useful for debugging or when getting wrong images"""
    try:
        import shutil
        cache_dir = 'cache'
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir, exist_ok=True)
            return jsonify({'success': True, 'message': 'Image cache cleared successfully'})
        else:
            return jsonify({'success': True, 'message': 'Cache directory did not exist'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/default_images/<filename>')
def serve_default_image(filename):
    """Serve default/placeholder images"""
    try:
        default_folder = config['images'].get('default_images_folder', 'default_images')
        file_path = os.path.join(default_folder, filename)
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path)
        else:
            return jsonify({'error': 'Default image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
