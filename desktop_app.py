import sys
import os
import json
import hashlib
import threading
import requests
import webbrowser
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QScrollArea, QComboBox, QSpinBox,
    QCheckBox, QFileDialog, QMessageBox, QTabWidget, QListWidget,
    QListWidgetItem, QProgressBar, QStatusBar, QSplitter, QLineEdit,
    QSlider, QGroupBox, QGridLayout, QDockWidget, QMenu, QAction,
    QMenuBar, QShortcut, QFrame, QCalendarWidget, QTimeEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QDateTime, QSettings
from PyQt5.QtGui import QPixmap, QFont, QColor, QIcon, QKeySequence
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout
from PyQt5.QtCore import QSize

from config import Config


class NewsPostGeneratorCore:
    """Core logic for generating posts (extracted from web app)"""
    
    def __init__(self):
        self.config = Config()
        self.processed_news = self.load_processed_news()
        self.pending_news = []

        # Initialize Gemini
        try:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(self.config.GEMINI_MODEL)
        except Exception as e:
            print(f"Gemini initialization error: {e}")
            self.model = None

        # Ensure directories exist
        os.makedirs(self.config.POSTS_DIRECTORY, exist_ok=True)
        os.makedirs('temp', exist_ok=True)

        # Initialize fonts
        self._init_fonts()
        self._init_colors()

    def _init_fonts(self):
        """Initialize fonts with fallbacks"""
        font_paths = ['arialbd.ttf', 'arial.ttf', 'C:\\Windows\\Fonts\\arial.ttf']
        
        self.font_headline = self.font_headline_sm = self.font_body = \
        self.font_small = self.font_xsmall = self.font_logo = None
        
        for path in font_paths:
            try:
                self.font_headline = ImageFont.truetype(path, 72)
                self.font_headline_sm = ImageFont.truetype(path, 54)
                self.font_body = ImageFont.truetype(path, 32)
                self.font_small = ImageFont.truetype(path, 26)
                self.font_xsmall = ImageFont.truetype(path, 22)
                self.font_logo = ImageFont.truetype(path, 28)
                return
            except:
                continue
        
        # Fallback to default
        default = ImageFont.load_default()
        self.font_headline = self.font_headline_sm = self.font_body = \
        self.font_small = self.font_xsmall = self.font_logo = default

    def _init_colors(self):
        """Initialize color palette"""
        self.COLOR_BG_DARK = (10, 10, 30)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_CYAN = (0, 200, 255)
        self.COLOR_GOLD = (255, 215, 0)
        self.COLOR_ORANGE = (255, 140, 0)
        self.COLOR_PINK = (255, 20, 147)
        self.COLOR_LIME = (50, 255, 50)
        self.COLOR_YELLOW = (255, 255, 0)
        self.COLOR_MAGENTA = (255, 0, 255)
        self.COLOR_CORAL = (255, 127, 80)
        self.COLOR_TEAL = (0, 255, 200)
        self.COLOR_LAVENDER = (180, 130, 255)
        self.COLOR_ROSE = (255, 100, 180)
        self.COLOR_AQUA = (100, 255, 255)

        self.VIBRANT_COLORS = [
            self.COLOR_CYAN, self.COLOR_GOLD, self.COLOR_ORANGE, self.COLOR_PINK,
            self.COLOR_LIME, self.COLOR_YELLOW, self.COLOR_MAGENTA, self.COLOR_CORAL,
            self.COLOR_TEAL, self.COLOR_LAVENDER, self.COLOR_ROSE, self.COLOR_AQUA,
        ]

    def load_processed_news(self):
        """Load previously processed news"""
        try:
            with open(self.config.PROCESSED_NEWS_FILE, 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()

    def save_processed_news(self):
        """Save processed news"""
        with open(self.config.PROCESSED_NEWS_FILE, 'w') as f:
            json.dump(list(self.processed_news), f)

    def fetch_news(self):
        """Fetch news from API"""
        try:
            params = {
                'country': self.config.COUNTRY,
                'category': self.config.CATEGORY,
                'apiKey': self.config.NEWS_API_KEY,
                'pageSize': 20
            }
            response = requests.get(self.config.NEWS_API_URL, params=params, timeout=10)
            
            if response.status_code != 200:
                return []

            data = response.json()
            articles = data.get('articles', [])
            filtered_articles = []

            for article in articles:
                if article.get('title') and article.get('description'):
                    article_id = hashlib.md5(
                        f"{article['title']}{article.get('publishedAt', '')}".encode()
                    ).hexdigest()
                    article['id'] = article_id

                    if article_id not in self.processed_news:
                        filtered_articles.append(article)

            return filtered_articles

        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def generate_post_image(self, headline, summary):
        """Generate Instagram post image"""
        try:
            img = Image.new('RGB', (self.config.POST_WIDTH, self.config.POST_HEIGHT),
                           self.COLOR_BG_DARK)
            draw = ImageDraw.Draw(img)

            # Add headline
            y_position = 200
            draw.text((40, y_position), headline[:50], fill=self.COLOR_CYAN,
                     font=self.font_headline_sm)

            # Add summary
            y_position += 300
            for line in summary[:100].split('\n')[:3]:
                draw.text((40, y_position), line, fill=self.COLOR_WHITE,
                         font=self.font_body)
                y_position += 100

            # Save to file
            filename = f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.config.POSTS_DIRECTORY, filename)
            img.save(filepath)
            return filepath

        except Exception as e:
            print(f"Error generating image: {e}")
            return None

    def create_posts_from_news(self):
        """Create posts from pending news"""
        created = 0
        for article in self.pending_news[:self.config.MAX_POSTS_PER_BATCH]:
            try:
                headline = article.get('title', 'No Title')
                filepath = self.generate_post_image(headline, article.get('description', ''))

                if filepath:
                    self.processed_news.add(article['id'])
                    created += 1

            except Exception as e:
                print(f"Error creating post: {e}")

        self.pending_news = self.pending_news[self.config.MAX_POSTS_PER_BATCH:]
        self.save_processed_news()
        return created


class NewsWorker(QThread):
    """Worker thread for fetching news"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, generator):
        super().__init__()
        self.generator = generator

    def run(self):
        try:
            news = self.generator.fetch_news()
            self.finished.emit(news)
        except Exception as e:
            self.error.emit(str(e))


class PostWorker(QThread):
    """Worker thread for creating posts"""
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, generator):
        super().__init__()
        self.generator = generator

    def run(self):
        try:
            created = self.generator.create_posts_from_news()
            self.finished.emit(created)
        except Exception as e:
            self.error.emit(str(e))


class SettingsDialog(QDialog):
    """Settings dialog for API keys and preferences"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.settings = QSettings("NewsPostGenerator", "settings")
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        self.setWindowTitle("⚙️ Settings")
        self.setGeometry(100, 100, 600, 700)
        
        layout = QVBoxLayout()
        
        # API Keys Section
        api_group = QGroupBox("🔑 API Keys")
        api_layout = QFormLayout()
        
        self.news_key = QTextEdit()
        self.news_key.setText(self.config.NEWS_API_KEY)
        self.news_key.setMaximumHeight(60)
        self.news_key.setToolTip("Get your free key from https://newsapi.org")
        api_layout.addRow("NewsAPI Key:", self.news_key)
        
        self.gemini_key = QTextEdit()
        self.gemini_key.setText(self.config.GEMINI_API_KEY)
        self.gemini_key.setMaximumHeight(60)
        self.gemini_key.setToolTip("Get your free key from https://makersuite.google.com/app/apikey")
        api_layout.addRow("Gemini API Key:", self.gemini_key)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Content Settings Section
        content_group = QGroupBox("📰 Content Settings")
        content_layout = QFormLayout()
        
        self.country = QComboBox()
        self.country.addItems(['us', 'gb', 'ca', 'au', 'in', 'de', 'fr', 'it', 'es', 'br'])
        self.country.setCurrentText(self.config.COUNTRY)
        content_layout.addRow("Country:", self.country)
        
        self.category = QComboBox()
        self.category.addItems(['technology', 'business', 'entertainment', 'health', 'science', 'sports', 'general'])
        self.category.setCurrentText(self.config.CATEGORY)
        content_layout.addRow("Category:", self.category)
        
        self.max_posts = QSpinBox()
        self.max_posts.setValue(self.config.MAX_POSTS_PER_BATCH)
        self.max_posts.setMinimum(1)
        self.max_posts.setMaximum(50)
        content_layout.addRow("Max Posts per Batch:", self.max_posts)
        
        # Auto-refresh
        self.auto_refresh = QCheckBox("Auto-refresh every (minutes):")
        self.auto_refresh_interval = QSpinBox()
        self.auto_refresh_interval.setMinimum(5)
        self.auto_refresh_interval.setMaximum(120)
        self.auto_refresh_interval.setValue(30)
        refresh_layout = QHBoxLayout()
        refresettings = QSettings("NewsPostGenerator", "settings")
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.fetch_news)
        self.current_selected_post = None
        
        self.setWindowTitle("📰 News Post Generator - Desktop Edition")
        self.setGeometry(100, 100, 1600, 950)
        
        # Apply dark theme
        self.apply_dark_theme()
        
        self.init_ui()
        self.create_menu_bar()
        self.create_shortcuts()
        
        # Load previous settings
        self.load_settings()
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Display Settings Section
        display_group = QGroupBox("🎨 Display Settings")
        display_layout = QFormLayout()
        
        self.preview_quality = QComboBox()
        self.preview_quality.addItems(['Low', 'Medium', 'High'])
        self.preview_quality.setCurrentText(self.settings.value("preview_quality", "High"))
        display_layout.addRow("Preview Quality:", self.preview_quality)
        
        self.theme = QComboBox()
        self.theme.addItems(['Dark', 'Light'])
        self.theme.setCurrentText(self.settings.value("theme", "Dark"))
        display_layout.addRow("Theme:", self.theme)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def restore_defaults(self):
        """Restore default settings"""
        self.country.setCurrentText('us')
        self.category.setCurrentText('technology')
        self.max_posts.setValue(5)
        self.auto_refresh.setChecked(False)
        self.preview_quality.setCurrentText('High')
        self.theme.setCurrentText('Dark')
    
    def apply_theme(self):
        """Apply dark theme to dialog"""
        dark_stylesheet = """
            QDialog {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QGroupBox {
                color: #00d4ff;
                border: 2px solid #0088cc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QComboBox, QSpinBox, QTextEdit, QLineEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #0088cc;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0088cc;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00a8ff;
            }
        """
        self.setStyleSheet(dark_stylesheet)


class NewsPostDesktopApp(QMainWindow):
    """Main desktop application window"""
    
    def __init__(self):
        super().__init__()
        self.generator = NewsPostGeneratorCore()
        self.news_worker = None
        self.post_worker = None
        self.init_ui()
        self.setWindowTitle("News Post Generator - Desktop")
        self.setGeometry(100, 100, 1400, 900)

    def init_ui(self):
        """Initialize UI with improved layout"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout()
        
        # ─── LEFT PANEL: Controls & Tabs ───
        left_panel = QVBoxLayout()
        
        # Header with title
        header = QVBoxLayout()
        title = QLabel("📰 News Post Generator")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)
        
        # Quick category buttons
        category_layout = QHBoxLayout()
        categories = ['Technology', 'Business', 'Entertainment', 'Health']
        for cat in categories:
            btn = QPushButton(cat)
            btn.setMaximumWidth(100)
            btn.setToolTip(f"Quick filter: {cat}")
            btn.clicked.connect(lambda checked, c=cat: self.quick_category_filter(c))
            category_layout.addWidget(btn)
        header.addLayout(category_layout)
        left_panel.addLayout(header)
        
        # Control buttons (improved layout)
        controls = QGridLayout()
        controls.setSpacing(10)
        
        fetch_btn = self.create_button("📰 Fetch News", self.fetch_news, "Fetch latest news articles")
        fetch_btn.setMinimumHeight(45)
        controls.addWidget(fetch_btn, 0, 0)
        
        create_btn = self.create_button("✨ Create Posts", self.create_posts, "Generate Instagram posts")
        create_btn.setMinimumHeight(45)
        controls.addWidget(create_btn, 0, 1)
        
        refresh_btn = self.create_button("🔄 Refresh", self.refresh_posts_list, "Refresh posts list")
        refresh_btn.setMinimumHeight(45)
        controls.addWidget(refresh_btn, 1, 0)
        
        settings_btn = self.create_button("⚙️ Settings", self.open_settings, "Configure API keys")
        settings_btn.setMinimumHeight(45)
        controls.addWidget(settings_btn, 1, 1)
        
        left_panel.addLayout(controls)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search posts by title...")
        self.search_input.textChanged.connect(self.filter_posts)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        left_panel.addLayout(search_layout)
        
        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding: 8px 20px; }")
        
        # News tab
        news_widget = self.create_news_tab()
        tabs.addTab(news_widget, "📰 News")
        
        # Posts tab
        posts_widget = self.create_posts_tab()
        tabs.addTab(posts_widget, "✨ Posts")
        
        # Stats tab
        stats_widget = self.create_stats_tab()
        tabs.addTab(stats_widget, "📊 Stats")
        
        left_panel.addWidget(tabs)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMaximumHeight(8)
        left_panel.addWidget(self.progress)
        
        # Status label
        self.status_label = QLabel("✅ Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        left_panel.addWidget(self.status_label)
        
        # ─── RIGHT PANEL: Preview ───
        right_panel = QVBoxLayout()
        
        preview_title = QLabel("🖼️ Preview")
        preview_title_font = QFont()
        preview_title_font.setPointSize(14)
        preview_title_font.setBold(True)
        preview_title.setFont(preview_title_font)
        right_panel.addWidget(preview_title)
        
        # Image preview
        self.preview_image = QLabel()
        self.preview_image.setAlignment(Qt.AlignCenter)
        self.preview_image.setMinimumSize(400, 600)
        self.preview_image.setMaximumWidth(600)
        self.preview_image.setStyleSheet("border: 2px solid #0088cc; border-radius: 5px;")
        
        scroll = QScrollArea()
        scroll.setWidget(self.preview_image)
        scroll.setWidgetResizable(True)
        right_panel.addWidget(scroll)
        
        # Preview details
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(180)
        self.preview_text.setStyleSheet("border: 1px solid #0088cc; border-radius: 3px;")
        right_panel.addWidget(self.preview_text)
        
        # Action buttons for preview
        action_layout = QGridLayout()
        action_layout.setSpacing(8)
        
        export_btn = self.create_button("💾 Export", self.export_post, "Export post to file")
        export_btn.setMinimumHeight(40)
        action_layout.addWidget(export_btn, 0, 0)
        
        open_folder_btn = self.create_button("📂 Open Folder", self.open_posts_folder, "Open posts directory")
        open_folder_btn.setMinimumHeight(40)
        action_layout.addWidget(open_folder_btn, 0, 1)
        
        copy_path_btn = self.create_button("📋 Copy Path", self.copy_post_path, "Copy file path")
        copy_path_btn.setMinimumHeight(40)
        action_layout.addWidget(copy_path_btn, 1, 0)
        
        delete_btn = self.create_button("🗑️ Delete", self.delete_post, "Delete post")
        delete_btn.setMinimumHeight(40)
        delete_btn.setStyleSheet("background-color: #cc0000; color: white; border: none; border-radius: 3px; padding: 8px; font-weight: bold;")
        action_layout.addWidget(delete_btn, 1, 1)
        
        right_panel.addLayout(action_layout)
        
        # Combine panels
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([800, 600])
        
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        
        # Initial load
        self.refresh_posts_list()
        self.update_stats()

    def create_button(self, text, callback, tooltip):
        """Helper to create styled button"""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        return btn
    
    def create_news_tab(self):
        """Create news tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("📰 Latest News")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        label.setFont(font)
        layout.addWidget(label)
        
        self.news_list = QListWidget()
        self.news_list.setStyleSheet("border: 1px solid #0088cc; border-radius: 3px;")
        layout.addWidget(self.news_list)
        
        widget.setLayout(layout)
        return widget
    
    def create_posts_tab(self):
        """Create posts tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("✨ Generated Posts")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        label.setFont(font)
        layout.addWidget(label)
        
        self.posts_list = QListWidget()
        self.posts_list.itemClicked.connect(self.show_post_preview)
        self.posts_list.setStyleSheet("border: 1px solid #0088cc; border-radius: 3px;")
        self.posts_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.posts_list.customContextMenuRequested.connect(self.show_posts_context_menu)
        layout.addWidget(self.posts_list)
        
        widget.setLayout(layout)
        return widget
    
    def create_stats_tab(self):
        """Create stats tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("border: 1px solid #0088cc; border-radius: 3px;")
        layout.addWidget(self.stats_text)
        
        btn_layout = QHBoxLayout()
        refresh_btn = self.create_button("🔄 Refresh", self.update_stats, "Refresh statistics")
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def apply_dark_theme(self):
        """Apply modern dark theme"""
        dark_stylesheet = """
            QMainWindow {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #0088cc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00a8ff;
            }
            QPushButton:pressed {
                background-color: #0066aa;
            }
            QTabWidget::pane {
                border: 1px solid #0088cc;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 8px 20px;
                border: 1px solid #0088cc;
            }
            QTabBar::tab:selected {
                background-color: #0088cc;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #0088cc;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #0088cc;
            }
            QTextEdit, QLineEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #0088cc;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox, QSpinBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #0088cc;
                border-radius: 3px;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #0088cc;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #00d4ff;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #0088cc;
                border-radius: 6px;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border-top: 1px solid #0088cc;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QMenu::item:selected {
                background-color: #0088cc;
            }
        """
        self.setStyleSheet(dark_stylesheet)
    
    def create_menu_bar(self):
        """Create menu bar with actions"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 File")
        
        open_folder_action = QAction("📂 Open Posts Folder", self)
        open_folder_action.triggered.connect(self.open_posts_folder)
        open_folder_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Exit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("🛠️ Tools")
        
        fetch_action = QAction("📰 Fetch News", self)
        fetch_action.triggered.connect(self.fetch_news)
        fetch_action.setShortcut("Ctrl+F")
        tools_menu.addAction(fetch_action)
        
        create_action = QAction("✨ Create Posts", self)
        create_action.triggered.connect(self.create_posts)
        create_action.setShortcut("Ctrl+P")
        tools_menu.addAction(create_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.open_settings)
        settings_action.setShortcut("Ctrl+,")
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("📚 Documentation", self)
        docs_action.triggered.connect(self.open_documentation)
        help_menu.addAction(docs_action)
    
    def create_shortcuts(self):
        """Create keyboard shortcuts"""
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, self.delete_all_posts)
        QShortcut(QKeySequence("F5"), self, self.refresh_posts_list)
    
    def load_settings(self):
        """Load settings from QSettings"""
        pass
    
    def quick_category_filter(self, category):
        """Quick filter by category"""
        self.generator.config.CATEGORY = category.lower()
        self.fetch_news()
    
    def filter_posts(self, text):
        """Filter posts by search text"""
        for i in range(self.posts_list.count()):
            item = self.posts_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def show_posts_context_menu(self, position):
        """Show context menu on right-click"""
        item = self.posts_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }
            QMenu::item:selected {
                background-color: #0088cc;
            }
        """)
        
        preview_action = menu.addAction("👁️ Preview")
        preview_action.triggered.connect(lambda: self.show_post_preview(item))
        
        export_action = menu.addAction("💾 Export")
        export_action.triggered.connect(self.export_post)
        
        copy_action = menu.addAction("📋 Copy Path")
        copy_action.triggered.connect(self.copy_post_path)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(self.delete_post)
        
        menu.exec_(self.posts_list.mapToGlobal(position))

    def fetch_news(self):
        """Fetch news in background thread"""
        if not self.generator.config.NEWS_API_KEY or self.generator.config.NEWS_API_KEY == "":
            QMessageBox.warning(self, "⚠️ Configuration Required", 
                              "Please configure your NewsAPI key in Settings first!")
            self.open_settings()
            return
        
        self.status_label.setText("⏳ Fetching news...")
        self.statusBar().showMessage("⏳ Connecting to NewsAPI...")
        self.news_list.clear()
        
        if self.news_worker and self.news_worker.isRunning():
            self.status_label.setText("⚠️ Already fetching news...")
            return
        
        self.news_worker = NewsWorker(self.generator)
        self.news_worker.finished.connect(self.on_news_fetched)
        self.news_worker.error.connect(self.on_fetch_error)
        self.news_worker.start()

    def on_news_fetched(self, articles):
        """Handle fetched news"""
        self.generator.pending_news.extend(articles)
        
        for article in articles:
            item = QListWidgetItem()
            title = article.get('title', 'No Title')[:60]
            item.setText(f"📰 {title}")
            item.setData(Qt.UserRole, article)
            self.news_list.addItem(item)
        
        msg = f"✅ Fetched {len(articles)} new articles"
        self.status_label.setText(msg)
        self.statusBar().showMessage(msg)
        self.update_stats()
        
        if articles:
            QMessageBox.information(self, "✅ Success", f"Fetched {len(articles)} articles!\n\nReady to create posts.")

    def on_fetch_error(self, error):
        """Handle fetch error"""
        msg = f"❌ Error: {str(error)[:50]}"
        self.status_label.setText(msg)
        self.statusBar().showMessage(msg)
        QMessageBox.critical(self, "❌ Error", f"Failed to fetch news:\n\n{error}")

    def create_posts(self):
        """Create posts from pending news"""
        if not self.generator.pending_news:
            QMessageBox.information(self, "ℹ️ Info", "No pending news to create posts from.\n\nPlease fetch news first!")
            return
        
        self.status_label.setText("⏳ Creating posts...")
        self.statusBar().showMessage("⏳ Generating images...")
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        if self.post_worker and self.post_worker.isRunning():
            return
        
        self.post_worker = PostWorker(self.generator)
        self.post_worker.finished.connect(self.on_posts_created)
        self.post_worker.error.connect(self.on_create_error)
        self.post_worker.start()

    def on_posts_created(self, count):
        """Handle posts creation"""
        self.progress.setVisible(False)
        msg = f"✅ Created {count} posts"
        self.status_label.setText(msg)
        self.statusBar().showMessage(msg)
        self.refresh_posts_list()
        self.update_stats()
        
        if count > 0:
            QMessageBox.information(self, "✅ Success", f"Successfully created {count} post{'s' if count != 1 else ''}!")

    def on_create_error(self, error):
        """Handle creation error"""
        self.progress.setVisible(False)
        msg = f"❌ Error: {str(error)[:50]}"
        self.status_label.setText(msg)
        self.statusBar().showMessage(msg)
        QMessageBox.critical(self, "❌ Error", f"Failed to create posts:\n\n{error}")

    def refresh_posts_list(self):
        """Refresh posts list"""
        self.posts_list.clear()
        try:
            post_dir = self.generator.config.POSTS_DIRECTORY
            if not os.path.exists(post_dir):
                os.makedirs(post_dir, exist_ok=True)
                return
            
            posts = sorted(os.listdir(post_dir), reverse=True)
            valid_posts = [p for p in posts if p.endswith(('.png', '.jpg', '.jpeg'))]
            
            for post in valid_posts[:50]:  # Show last 50
                item = QListWidgetItem()
                item.setText(f"🖼️ {post}")
                item.setData(Qt.UserRole, os.path.join(post_dir, post))
                self.posts_list.addItem(item)
            
            self.status_label.setText(f"✅ Loaded {len(valid_posts)} posts")
        except Exception as e:
            print(f"Error loading posts: {e}")
            self.status_label.setText("⚠️ Could not load posts")

    def show_post_preview(self, item):
        """Show post preview"""
        if not item:
            return
        
        try:
            filepath = item.data(Qt.UserRole)
            if not filepath or not os.path.exists(filepath):
                self.status_label.setText("⚠️ File not found")
                return
            
            pixmap = QPixmap(filepath)
            if pixmap.isNull():
                self.status_label.setText("⚠️ Could not load image")
                return
            
            # Scale to fit preview
            scaled = pixmap.scaledToHeight(600, Qt.SmoothTransformation)
            self.preview_image.setPixmap(scaled)
            
            # Show file info
            stat_info = os.stat(filepath)
            file_size = stat_info.st_size / 1024
            created_time = datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            
            info_text = f"""
📄 {os.path.basename(filepath)}

📊 Size: {file_size:.1f} KB
📅 Created: {created_time}
📐 Dimensions: {pixmap.width()}×{pixmap.height()}
            """
            self.preview_text.setText(info_text)
            self.status_label.setText(f"✅ Preview: {os.path.basename(filepath)}")
            self.current_selected_post = filepath
            
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Error", f"Could not load preview:\n\n{e}")
            self.status_label.setText("❌ Error loading preview")

    def export_post(self):
        """Export selected post"""
        current = self.posts_list.currentItem()
        if not current:
            QMessageBox.warning(self, "⚠️ Warning", "Please select a post first")
            return
        
        source = current.data(Qt.UserRole)
        filepath, _ = QFileDialog.getSaveFileName(
            self, "💾 Export Post", os.path.basename(source), "PNG Files (*.png);;All Files (*)"
        )
        
        if filepath:
            try:
                with open(source, 'rb') as src:
                    with open(filepath, 'wb') as dst:
                        dst.write(src.read())
                QMessageBox.information(self, "✅ Success", f"Post exported to:\n{filepath}")
                self.status_label.setText("✅ Post exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Export failed: {e}")
                self.status_label.setText(f"❌ Export error: {str(e)}")

    def open_posts_folder(self):
        """Open posts directory in file explorer"""
        try:
            folder = os.path.abspath(self.generator.config.POSTS_DIRECTORY)
            if os.name == 'nt':  # Windows
                os.startfile(folder)
            else:  # Mac/Linux
                import subprocess
                subprocess.Popen(['xdg-open' if os.name == 'posix' else 'open', folder])
            self.status_label.setText("📂 Posts folder opened")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {e}")

    def copy_post_path(self):
        """Copy post file path to clipboard"""
        current = self.posts_list.currentItem()
        if not current:
            QMessageBox.warning(self, "⚠️ Warning", "Please select a post first")
            return
        
        filepath = current.data(Qt.UserRole)
        clipboard = QApplication.clipboard()
        clipboard.setText(filepath)
        self.status_label.setText(f"📋 Copied: {os.path.basename(filepath)}")

    def delete_post(self):
        """Delete selected post"""
        current = self.posts_list.currentItem()
        if not current:
            QMessageBox.warning(self, "⚠️ Warning", "Please select a post first")
            return
        
        filepath = current.data(Qt.UserRole)
        reply = QMessageBox.question(self, "🗑️ Delete Post", 
                                    f"Are you sure you want to delete:\n{os.path.basename(filepath)}?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(filepath)
                self.refresh_posts_list()
                self.status_label.setText("✅ Post deleted")
                QMessageBox.information(self, "✅ Success", "Post deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Delete failed: {e}")

    def delete_all_posts(self):
        """Delete all posts (keyboard shortcut)"""
        reply = QMessageBox.question(self, "⚠️ Delete All Posts", 
                                    "Are you sure you want to delete ALL posts? This cannot be undone!",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                post_dir = self.generator.config.POSTS_DIRECTORY
                for file in os.listdir(post_dir):
                    if file.endswith(('.png', '.jpg', '.jpeg')):
                        os.remove(os.path.join(post_dir, file))
                self.refresh_posts_list()
                self.status_label.setText("✅ All posts deleted")
                QMessageBox.information(self, "✅ Success", "All posts deleted!")
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Delete failed: {e}")

    def show_about(self):
        """Show about dialog"""
        about_text = """
<b>📰 News Post Generator</b>
<br><br>
<b>Version:</b> 2.0 (Desktop Edition)
<br><b>License:</b> MIT
<br>
<br>An intelligent news-to-Instagram post generator powered by:
<br>• <b>NewsAPI</b> - News data
<br>• <b>Google Gemini</b> - AI content generation
<br>• <b>Pillow</b> - Image generation
<br>
<br><b>Features:</b>
<br>✓ Real-time news fetching
<br>✓ AI-powered image generation
<br>✓ Batch post creation
<br>✓ Dark theme UI
<br>✓ Easy API configuration
<br>
<br><b>Made with ❤️ using PyQt5</b>
        """
        
        dlg = QMessageBox(self)
        dlg.setWindowTitle("ℹ️ About News Post Generator")
        dlg.setText(about_text)
        dlg.setTextFormat(Qt.RichText)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def open_documentation(self):
        """Open documentation"""
        try:
            docs_files = [
                'DESKTOP_APP_GUIDE.md',
                'START_DESKTOP_APP.md',
                'PACKAGING_GUIDE.md'
            ]
            
            for doc in docs_files:
                if os.path.exists(doc):
                    os.startfile(doc) if os.name == 'nt' else os.system(f'open "{doc}"')
                    break
            
            self.status_label.setText("📚 Documentation opened")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open documentation: {e}")

    def update_stats(self):
        """Update statistics"""
        try:
            post_dir = self.generator.config.POSTS_DIRECTORY
            if not os.path.exists(post_dir):
                os.makedirs(post_dir, exist_ok=True)
                posts_count = 0
            else:
                posts_count = len([f for f in os.listdir(post_dir)
                                  if f.endswith(('.png', '.jpg', '.jpeg'))])
            
            stats = f"""
╔══════════════════════════════════════════════════╗
║           📊 STATISTICS & OVERVIEW              ║
╚══════════════════════════════════════════════════╝

📰 News Statistics:
   • Processed: {len(self.generator.processed_news)} articles
   • Pending: {len(self.generator.pending_news)} articles
   • Total: {len(self.generator.processed_news) + len(self.generator.pending_news)}

🖼️ Post Statistics:
   • Generated: {posts_count} posts
   • Size on disk: {sum(os.path.getsize(os.path.join(post_dir, f)) for f in os.listdir(post_dir) if f.endswith(('.png', '.jpg'))) / 1024 / 1024:.1f} MB

⚙️ Current Settings:
   • Country: {self.generator.config.COUNTRY.upper()}
   • Category: {self.generator.config.CATEGORY}
   • Batch Size: {self.generator.config.MAX_POSTS_PER_BATCH} posts
   • Post Format: {self.generator.config.POST_WIDTH}×{self.generator.config.POST_HEIGHT}px

🎯 Next Steps:
   1. Click "📰 Fetch News" to get latest articles
   2. Click "✨ Create Posts" to generate images
   3. Preview and export your posts!
            """
            self.stats_text.setText(stats)
        except Exception as e:
            self.stats_text.setText(f"⚠️ Error loading stats:\n{e}")

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.generator.config, self)
        if dialog.exec_():
            # Update config
            self.generator.config.NEWS_API_KEY = dialog.news_key.toPlainText().strip()
            self.generator.config.GEMINI_API_KEY = dialog.gemini_key.toPlainText().strip()
            self.generator.config.COUNTRY = dialog.country.currentText()
            self.generator.config.CATEGORY = dialog.category.currentText()
            self.generator.config.MAX_POSTS_PER_BATCH = dialog.max_posts.value()
            
            # Re-initialize Gemini with new key
            try:
                genai.configure(api_key=self.generator.config.GEMINI_API_KEY)
                self.generator.model = genai.GenerativeModel(self.generator.config.GEMINI_MODEL)
            except Exception as e:
                QMessageBox.warning(self, "⚠️ Warning", f"Could not configure Gemini:\n{e}")
            
            # Save to .env
            self.save_config_to_env()
            self.status_label.setText("✅ Settings saved")
            self.statusBar().showMessage("✅ Configuration updated!")
            
            QMessageBox.information(self, "✅ Settings Saved", "Your settings have been updated successfully!")

    def save_config_to_env(self):
        """Save settings to .env file"""
        try:
            with open('.env', 'w') as f:
                f.write(f"NEWS_API_KEY={self.generator.config.NEWS_API_KEY}\n")
                f.write(f"GEMINI_API_KEY={self.generator.config.GEMINI_API_KEY}\n")
                f.write(f"# Country: {self.generator.config.COUNTRY}\n")
                f.write(f"# Category: {self.generator.config.CATEGORY}\n")
            self.settings.setValue("country", self.generator.config.COUNTRY)
            self.settings.setValue("category", self.generator.config.CATEGORY)
        except Exception as e:
            print(f"Error saving config: {e}")
            QMessageBox.warning(self, "⚠️ Error", f"Could not save configuration:\n{e}")


def main():
    app = QApplication(sys.argv)
    window = NewsPostDesktopApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
