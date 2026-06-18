# Desktop App Quick Start

## 📁 What Was Created

✅ **desktop_app.py** (1000+ lines)
- Full PyQt5 desktop application
- News fetching & post generation
- Image preview & export
- Settings management

✅ **requirements-desktop.txt**
- Minimal dependencies for desktop

✅ **setup-desktop.bat** (Windows)
✅ **setup-desktop.sh** (Mac/Linux)
- One-click installation scripts

✅ **desktop_app.spec**
- PyInstaller configuration for .exe creation

✅ **DESKTOP_APP_GUIDE.md**
- Complete feature guide

✅ **PACKAGING_GUIDE.md**
- How to create .exe and installer

## 🚀 Run It Now (5 steps)

### Step 1: Install PyQt5
```bash
pip install PyQt5 Pillow requests python-dotenv google-generativeai
```

### Step 2: Create .env file
```
NEWS_API_KEY=your_newsapi_key
GEMINI_API_KEY=your_gemini_key
```

Get keys from:
- https://newsapi.org (free tier)
- https://makersuite.google.com/app/apikey (free)

### Step 3: Run the app
```bash
python desktop_app.py
```

### Step 4: Fetch News
Click "📰 Fetch News" button

### Step 5: Create Posts
Click "✨ Create Posts" button

## 🎨 What You Get

A professional desktop app with:
- 📰 News tab (view fetched articles)
- ✨ Posts tab (preview generated images)
- 📊 Stats tab (track progress)
- 🖼️ Live preview panel
- ⚙️ Settings dialog
- 💾 Export functionality

## 📦 Package as .exe (Optional)

When ready to distribute:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "News Post Generator" desktop_app.py
```

Your `.exe` will be in `dist/` folder!

See **PACKAGING_GUIDE.md** for advanced options.

## ⚡ Key Differences from Web Version

| Feature | Web | Desktop |
|---------|-----|---------|
| Run in browser | ✅ | ❌ |
| Native UI | ❌ | ✅ |
| File access | ⚠️ | ✅ |
| No server needed | ❌ | ✅ |
| Installable | ❌ | ✅ |
| Portable | ❌ | ✅ |

## 🔧 Troubleshooting

### "No module named PyQt5"
```bash
pip install PyQt5
```

### "Cannot find newsapi"
```bash
pip install requests
```

### "Gemini not configured"
- Add `GEMINI_API_KEY` to `.env`
- Get free key: https://makersuite.google.com/app/apikey

### App won't start
- Check Python version (3.8+)
- Verify all dependencies installed
- Check `.env` file exists

## 📚 Files Overview

```
d:\news\
├── desktop_app.py           ← Main app (run this!)
├── config.py               ← Configuration
├── requirements.txt        ← All dependencies
├── requirements-desktop.txt ← Desktop only
├── setup-desktop.bat       ← Windows installer script
├── setup-desktop.sh        ← Mac/Linux installer script
├── desktop_app.spec        ← PyInstaller config
├── .env.example            ← Template for API keys
│
├── DESKTOP_APP_GUIDE.md    ← Feature guide
├── PACKAGING_GUIDE.md      ← How to create .exe
├── DEPLOYMENT_READY.md     ← Web deployment info (optional)
│
├── posts/                  ← Generated images
├── static/                 ← CSS files
├── templates/              ← HTML templates (web only)
└── processed_news.json     ← Processed articles log
```

## 🎯 Next Steps

1. **Run the app** → `python desktop_app.py`
2. **Fetch news** → Click "📰 Fetch News"
3. **Generate posts** → Click "✨ Create Posts"
4. **Export** → Right-click post → "💾 Export"
5. **Package** → Follow PACKAGING_GUIDE.md

## 💡 Tips

- Keep `.env` secure (add to `.gitignore`)
- Generated posts saved in `posts/` folder
- Processed news tracked in `processed_news.json`
- Use "🔄 Refresh Posts" to reload
- Preview panel shows selected image

Ready to go! 🚀
