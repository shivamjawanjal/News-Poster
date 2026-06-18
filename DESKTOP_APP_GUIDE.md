# News Post Generator - Desktop App

Your Flask web app has been converted to a **PyQt5 desktop application**!

## 📁 Files Created

- **`desktop_app.py`** - Main desktop application (1000+ lines)
- **`requirements-desktop.txt`** - Dependencies for desktop app

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install PyQt5 Pillow requests python-dotenv google-generativeai
```

Or:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:
```
NEWS_API_KEY=your_news_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run the App

```bash
python desktop_app.py
```

## ✨ Features

### 📰 Fetch News
- Click "Fetch News" to get latest articles
- News is fetched in the background (non-blocking)
- View fetched articles in the News tab

### ✨ Create Posts
- Click "Create Posts" to generate Instagram images
- Creates beautiful posts with headlines and summaries
- Posts saved in `posts/` directory

### 📊 View Statistics
- Track processed/pending news
- Monitor generated posts count
- View current settings

### 🖼️ Preview Posts
- Click any post to preview it
- View file details (size, creation date)
- Export posts to any location

### ⚙️ Settings Dialog
- Change API keys without editing files
- Switch country/category
- Adjust batch size
- Settings auto-save to `.env`

## 📦 Application Structure

```
desktop_app.py
├── NewsPostGeneratorCore     # Core logic (reused from web app)
├── NewsWorker                # Background thread for fetching
├── PostWorker                # Background thread for creation
├── SettingsDialog            # Settings UI
└── NewsPostDesktopApp        # Main window
```

## 🎨 UI Layout

```
┌─────────────────────────────────────────────┬─────────────────┐
│                                             │                 │
│  📰 NEWS  ✨ POSTS  📊 STATS  │ ⚙️ SETTINGS  │  PREVIEW (600px)│
│  ─────────────────────────────  │           │   ──────────────│
│  [📰 Article 1]                │           │  [Image Display]│
│  [📰 Article 2]                │           │                 │
│  [📰 Article 3]                │           │  ⬇️ File Details │
│                                │           │                 │
│  [📰 Fetch News] [✨ Create]   │ [Export]   │                 │
│  [Progress bar...]             │           │                 │
│  Status: Ready                 │           │                 │
└─────────────────────────────────────────────┴─────────────────┘
```

## 🔧 Technical Details

### Threading
- News fetching runs in `NewsWorker` thread to prevent UI freeze
- Post creation runs in `PostWorker` thread
- UI updates via PyQt5 signals

### File Storage
- Posts: `posts/`
- Processed news: `processed_news.json`
- Configuration: `.env` file

### API Integration
- NewsAPI for fetching articles
- Google Gemini for content generation (if implemented)

## 🎯 Advantages Over Web Version

✅ No need for web browser  
✅ Direct file system access  
✅ Easier API key management  
✅ Native desktop experience  
✅ Works offline (after initial setup)  
✅ Better for batch processing  
✅ No server/port management  

## 📝 Comparison: Web vs Desktop

| Feature | Web | Desktop |
|---------|-----|---------|
| Browser needed | ✅ | ❌ |
| Installation | Simple (Vercel) | Simple (pip) |
| File access | ⚠️ Limited | ✅ Full |
| Threading | ✅ | ✅ |
| UI responsiveness | ⚠️ Network dependent | ✅ Native |
| Offline use | ❌ | ✅ Partially |

## 🐛 Troubleshooting

### PyQt5 won't install
```bash
pip install PyQt5-sip
pip install PyQt5
```

### Fonts not loading
- App falls back to default font
- On Windows: Arial is detected automatically

### API key not working
- Check `.env` file is in project root
- Verify API key is correct
- Reload app after changing `.env`

## 📚 Next Steps

1. **Add More Features**:
   - Schedule periodic fetching
   - Advanced image templates
   - Social media upload integration

2. **Distribution**:
   - Package as `.exe` with PyInstaller
   - Create installer with NSIS
   - Distribute via GitHub Releases

3. **Enhancements**:
   - Dark/Light theme
   - Batch processing
   - Undo/Redo functionality
   - Drag-and-drop support

## 🔗 Resources

- PyQt5 Docs: https://doc.qt.io/qtforpython/
- PyInstaller: https://pyinstaller.org/
- NewsAPI: https://newsapi.org/
- Google Generative AI: https://makersuite.google.com/

## 💡 Tips

- Keep `.env` file secure (add to `.gitignore`)
- Test API keys before deploying
- Monitor generated files (they accumulate)
- Use "Refresh Posts" to reload after manual additions

Enjoy your desktop app! 🎉
