# Flash Cards Video Creator 🎬

An AI-powered web application that generates educational flashcard videos from simple text prompts. Enter a topic like **"Body Parts"** or **"Animals"**, and the app produces a polished MP4 video complete with images, voiceovers, and subtitles — ready to share or upload to YouTube.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features ✨

| Feature | Description |
|---------|-------------|
| **AI Content Generation** | Azure OpenAI (GPT-4) generates relevant items for any topic |
| **Multi-Provider Images** | Fetches images from Pexels, Unsplash, and Pixabay with automatic fallback |
| **Interactive Image Selection** | Web UI to pick the best image from up to 5 options per item |
| **Professional Voiceovers** | Azure Text-to-Speech with natural-sounding neural voices |
| **Subtitle Overlay** | Bold, readable subtitles with configurable font, size, and styling |
| **YouTube Upload** | One-click upload to YouTube with channel selection |
| **Smart Caching** | Caches API responses to avoid redundant calls and speed up re-runs |
| **Parallel Fetching** | Concurrent image downloads for faster processing |
| **Fully Configurable** | Video resolution, duration, voice, subtitle style, and more via `config.yaml` |

---

## Quick Start 🚀

### Prerequisites

- **Python 3.8+**
- **FFmpeg** — `brew install ffmpeg` (macOS) · `sudo apt install ffmpeg` (Ubuntu)

### 1. Clone & Install

```bash
git clone https://github.com/your-username/flash.git
cd flash
chmod +x setup.sh
./setup.sh
```

The setup script creates a virtual environment, installs dependencies, and sets up required directories.

### 2. Configure API Keys

```bash
cp config.yaml.sample config.yaml
nano config.yaml  # Add your API keys
```

### 3. Run

```bash
source venv/bin/activate
python app.py
```

### 4. Open Browser

Navigate to **http://localhost:5000**

---

## API Keys 🔑

### Required

| Service | Purpose | Get It |
|---------|---------|--------|
| **Azure OpenAI** | AI content generation (GPT-4) | [Azure AI Studio](https://ai.azure.com/) |
| **Azure Speech Service** | Text-to-speech voiceovers | [Azure Speech](https://azure.microsoft.com/services/cognitive-services/speech-services/) (free tier: 500K chars/month) |

> **Note:** If you don't have Azure OpenAI, you can use a standard [OpenAI API key](https://platform.openai.com/api-keys) as a fallback.

### Image Providers (at least one required)

| Provider | Cost | Get It |
|----------|------|--------|
| **Pexels** ⭐ Recommended | Free | [pexels.com/api](https://www.pexels.com/api/) |
| **Unsplash** | Free tier | [unsplash.com/developers](https://unsplash.com/developers) |
| **Pixabay** | Free | [pixabay.com/api/docs](https://pixabay.com/api/docs/) |

### Optional

| Service | Purpose | Get It |
|---------|---------|--------|
| **YouTube Data API v3** | Upload videos to YouTube | [Google Cloud Console](https://console.cloud.google.com/) |

---

## How It Works 🔄

```
┌──────────┐    ┌───────────┐    ┌──────────────┐    ┌────────────────┐
│  Enter   │───▶│ AI generates│───▶│ Fetch images │───▶│ Select images  │
│  Topic   │    │ item list  │    │ (5 per item) │    │ via web UI     │
└──────────┘    └───────────┘    └──────────────┘    └────────┬───────┘
                                                              │
┌──────────┐    ┌───────────┐    ┌──────────────┐            │
│ Download │◀───│ Assemble  │◀───│ Generate TTS │◀───────────┘
│ or Upload│    │ video     │    │ audio        │
└──────────┘    └───────────┘    └──────────────┘
```

1. **Enter a topic** — e.g., "Animals", "Colors", "Solar System"
2. **AI generates items** — GPT-4 returns a list of relevant terms
3. **Images are fetched** — Up to 5 options per item from configured providers (parallel)
4. **User selects images** — Pick the best image for each card in the web UI
5. **Audio is generated** — Azure TTS creates voiceovers for each item
6. **Video is assembled** — FFmpeg combines images, audio, and subtitles into a polished MP4
7. **Download or upload** — Save locally or upload directly to YouTube

---

## Project Structure 📁

```
flash/
├── app.py                    # Flask application & API routes
├── config.yaml.sample        # Configuration template (copy to config.yaml)
├── requirements.txt          # Python dependencies
├── setup.sh                  # Automated setup script
├── pytest.ini                # Test configuration
│
├── services/                 # Core business logic
│   ├── ai_service.py        #   Azure OpenAI / OpenAI integration
│   ├── image_service.py     #   Multi-provider image search & caching
│   ├── tts_service.py       #   Azure Text-to-Speech
│   ├── video_service.py     #   FFmpeg video assembly & subtitles
│   └── youtube_service.py   #   YouTube Data API upload
│
├── templates/                # Jinja2 HTML templates
│   ├── index.html            #   Home page — enter topic
│   ├── select_images.html    #   Image selection grid
│   └── progress.html         #   Video generation progress & preview
│
├── static/                   # Frontend assets
│   ├── css/main.css
│   └── js/main.js
│
├── tests/                    # Test suite
│   ├── test_ai_service.py   #   Unit tests (pytest)
│   ├── fixtures.py           #   Test data & helpers
│   └── scripts/              #   Ad-hoc debug/investigation scripts
│
├── default_images/           # Fallback placeholder images
├── cache/                    # Cached API responses (gitignored)
├── temp/                     # Session working directories (gitignored)
└── output/                   # Generated videos (gitignored)
```

---

## Configuration ⚙️

All settings are managed in `config.yaml`. Copy from the sample to get started:

```bash
cp config.yaml.sample config.yaml
```

### Key Settings

| Section | Settings | Defaults |
|---------|----------|----------|
| **Video** | Resolution, FPS, max duration, display duration per card | 1920×1080, 30fps, 120s max, 4s per image |
| **Images** | Provider, download count, orientation, size tiers | Pexels, 5 per item, landscape, large |
| **Audio** | Voice name, language, region | `en-US-AvaMultilingualNeural`, en-US |
| **Subtitles** | Font, size, color, outline, shadow, background | Arial Bold, 48pt, white on black |
| **YouTube** | Privacy, title template, tags, auto-upload | Unlisted, disabled auto-upload |
| **Cache** | Enabled, TTL, max size | Enabled, 24h TTL, 500MB |

---

## API Endpoints 📡

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Home page |
| `POST` | `/create_flashcards` | Generate items from prompt |
| `GET` | `/fetch_images/<session_id>` | Fetch images for all items |
| `GET` | `/select_images?session_id=` | Image selection UI |
| `POST` | `/save_selections` | Save selected images |
| `GET` | `/generate_audio/<session_id>` | Generate TTS audio |
| `GET` | `/create_video/<session_id>` | Assemble final video |
| `GET` | `/download_video/<session_id>` | Download MP4 |
| `GET` | `/preview_video/<session_id>` | Stream video preview |
| `GET` | `/progress/<session_id>` | Progress & preview page |
| `POST` | `/upload_to_youtube/<session_id>` | Upload to YouTube |
| `GET` | `/get_channels/<session_id>` | List YouTube channels |
| `POST` | `/clear_cache` | Clear image cache |
| `GET` | `/api/session_status/<session_id>` | Session status JSON |

---

## Usage Examples 💡

### Educational Flash Cards
```
Topic: "Body Parts"
→ head, eyes, nose, mouth, ears, hands, feet, …
→ 2-minute video with images and voiceovers
```

### Science Topics
```
Topic: "Solar System"
→ sun, mercury, venus, earth, mars, jupiter, …
→ Perfect for classroom teaching
```

### Language Learning
```
Topic: "Common Animals"
→ cat, dog, bird, fish, elephant, …
→ Great for vocabulary building & pronunciation
```

---

## Development 👨‍💻

### Run in Debug Mode

```bash
source venv/bin/activate
python app.py  # Runs with debug=True on port 5000
```

### Run Tests

```bash
source venv/bin/activate
python -m pytest -v
```

### Production Deployment

```bash
source venv/bin/activate
gunicorn app:app --bind 0.0.0.0:5000 --workers 2
```

### Adding a New Image Provider

1. Add a `_search_<provider>()` method in `services/image_service.py`
2. Add the API key to `config.yaml.sample` and your `config.yaml`
3. Update the fallback chain in `search_images()`

---

## Troubleshooting 🔧

| Problem | Solution |
|---------|----------|
| **"No API key configured"** | Check `config.yaml` has valid keys; ensure proper YAML formatting |
| **"FFmpeg not found"** | Install: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Ubuntu) |
| **"No images found"** | Verify image provider API keys; try different search terms |
| **"Audio generation failed"** | Check Azure Speech credentials and region in `config.yaml` |
| **Wrong/stale images** | Use the **Clear Cache** button or `POST /clear_cache` |
| **YouTube upload fails** | Ensure `youtube_client_secrets.json` exists with valid OAuth2 credentials |

### Performance Tips

- Enable caching (on by default) to avoid redundant API calls
- Use `thumbnail_size: tiny` for fast image selection page loading
- Reduce `download_count` if image fetching is slow
- Lower resolution (e.g., `1280x720`) for faster video assembly

---

## Tech Stack 🛠️

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3, Flask |
| **AI** | Azure OpenAI (GPT-4) / OpenAI API |
| **TTS** | Azure Cognitive Services Speech SDK |
| **Video** | FFmpeg, Pillow |
| **Images** | Pexels, Unsplash, Pixabay APIs |
| **Upload** | YouTube Data API v3 (OAuth2) |
| **Frontend** | Jinja2, vanilla JavaScript, CSS |

---

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License 📄

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ for education and learning**
