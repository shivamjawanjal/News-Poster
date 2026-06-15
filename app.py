from flask import Flask, render_template, jsonify, send_file
import requests
import json
import os
import time
import hashlib
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageOps
import google.generativeai as genai
import threading
import schedule
from config import Config
import random
import re
from io import BytesIO

app = Flask(__name__)


class NewsPostGenerator:
    def __init__(self):
        self.config = Config()
        self.processed_news = self.load_processed_news()
        self.pending_news = []

        # Initialize Gemini
        genai.configure(api_key=self.config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.config.GEMINI_MODEL)

        # Ensure directories exist
        os.makedirs(self.config.POSTS_DIRECTORY, exist_ok=True)

        # Initialize fonts (with fallbacks)
        try:
            self.font_headline = ImageFont.truetype("arialbd.ttf", 72)
            self.font_headline_sm = ImageFont.truetype("arialbd.ttf", 54)
            self.font_body = ImageFont.truetype("arial.ttf", 32)
            self.font_small = ImageFont.truetype("arial.ttf", 26)
            self.font_xsmall = ImageFont.truetype("arial.ttf", 22)
            self.font_logo = ImageFont.truetype("arialbd.ttf", 28)
        except:
            try:
                self.font_headline = ImageFont.truetype("arial.ttf", 72)
                self.font_headline_sm = ImageFont.truetype("arial.ttf", 54)
                self.font_body = ImageFont.truetype("arial.ttf", 32)
                self.font_small = ImageFont.truetype("arial.ttf", 26)
                self.font_xsmall = ImageFont.truetype("arial.ttf", 22)
                self.font_logo = ImageFont.truetype("arial.ttf", 28)
            except:
                self.font_headline = ImageFont.load_default()
                self.font_headline_sm = ImageFont.load_default()
                self.font_body = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
                self.font_xsmall = ImageFont.load_default()
                self.font_logo = ImageFont.load_default()

        # Base colours
        self.COLOR_BG_DARK = (10, 10, 30)          # Very dark blue (background only)
        self.COLOR_WHITE = (255, 255, 255)          # Pure white
        self.COLOR_CYAN = (0, 200, 255)             # Bright cyan
        self.COLOR_GOLD = (255, 215, 0)             # Gold
        self.COLOR_ORANGE = (255, 140, 0)           # Orange
        self.COLOR_PINK = (255, 20, 147)            # Hot pink
        self.COLOR_LIME = (50, 255, 50)             # Lime green
        self.COLOR_YELLOW = (255, 255, 0)           # Yellow
        self.COLOR_MAGENTA = (255, 0, 255)          # Magenta
        self.COLOR_CORAL = (255, 127, 80)           # Coral
        self.COLOR_TEAL = (0, 255, 200)             # Teal
        self.COLOR_LAVENDER = (180, 130, 255)       # Lavender
        self.COLOR_ROSE = (255, 100, 180)           # Rose
        self.COLOR_AQUA = (100, 255, 255)           # Aqua

        # Vibrant colours palette (for pairing with white)
        self.VIBRANT_COLORS = [
            self.COLOR_CYAN,
            self.COLOR_GOLD,
            self.COLOR_ORANGE,
            self.COLOR_PINK,
            self.COLOR_LIME,
            self.COLOR_YELLOW,
            self.COLOR_MAGENTA,
            self.COLOR_CORAL,
            self.COLOR_TEAL,
            self.COLOR_LAVENDER,
            self.COLOR_ROSE,
            self.COLOR_AQUA,
        ]

    # ═══════════════════════════════════════════════════════════════
    #  File‑based news ID management
    # ═══════════════════════════════════════════════════════════════
    def load_processed_news(self):
        """Load previously processed news IDs from JSON file."""
        try:
            with open(self.config.PROCESSED_NEWS_FILE, 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()

    def save_processed_news(self):
        """Save processed news IDs to JSON file."""
        with open(self.config.PROCESSED_NEWS_FILE, 'w') as f:
            json.dump(list(self.processed_news), f)

    # ═══════════════════════════════════════════════════════════════
    #  News fetching (primary + fallback)
    # ═══════════════════════════════════════════════════════════════
    def fetch_news(self):
        """Fetch fresh news from the configured News API."""
        try:
            params = {
                'country': self.config.COUNTRY,
                'category': self.config.CATEGORY,
                'apiKey': self.config.NEWS_API_KEY,
                'pageSize': 20
            }

            print(f"Fetching news from: {self.config.NEWS_API_URL}")

            response = requests.get(self.config.NEWS_API_URL, params=params)

            if response.status_code != 200:
                print(f"Error response: {response.text}")
                return []

            data = response.json()
            articles = data.get('articles', [])

            # Filter out articles without proper content
            filtered_articles = []
            for article in articles:
                if (article.get('title') and 
                    article.get('description') and 
                    article.get('url') and 
                    article.get('publishedAt')):

                    article_id = hashlib.md5(
                        f"{article['title']}{article['publishedAt']}".encode()
                    ).hexdigest()

                    article['id'] = article_id

                    if article_id not in self.processed_news:
                        filtered_articles.append(article)

            return filtered_articles

        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return self.fetch_fallback_news()

    def fetch_fallback_news(self):
        """Fallback news fetching if primary API fails."""
        try:
            fallback_urls = [
                "https://newsapi.org/v2/top-headlines?country=us&apiKey=demo",
                "https://api.rss2json.com/v1/api.json?rss_url=http://rss.cnn.com/rss/edition.rss",
                "https://api.rss2json.com/v1/api.json?rss_url=http://feeds.bbci.co.uk/news/rss.xml"
            ]

            for url in fallback_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        articles = []

                        if 'articles' in data:
                            articles = data['articles']
                        elif 'items' in data:
                            items = data['items']
                            for item in items[:10]:
                                articles.append({
                                    'title': item.get('title', 'No Title'),
                                    'description': item.get('description', 'No Description'),
                                    'url': item.get('link', '#'),
                                    'publishedAt': item.get('pubDate', datetime.now().isoformat()),
                                    'source': {'name': item.get('author', 'Unknown')},
                                    'urlToImage': item.get('thumbnail') or item.get('enclosure', {}).get('link') or ''
                                })

                        filtered_articles = []
                        for article in articles[:10]:
                            if article.get('title'):
                                article['id'] = hashlib.md5(
                                    f"{article['title']}{article.get('publishedAt', '')}".encode()
                                ).hexdigest()

                                if article['id'] not in self.processed_news:
                                    filtered_articles.append(article)

                        if filtered_articles:
                            return filtered_articles

                except Exception as e:
                    continue

            return []

        except Exception as e:
            print(f"Fallback also failed: {str(e)}")
            return []

    # ═══════════════════════════════════════════════════════════════
    #  Gemini AI content generation
    # ═══════════════════════════════════════════════════════════════
    def analyze_with_gemini(self, article):
        """Analyze news article and generate engaging content with Gemini."""
        try:
            prompt = f"""
            Analyze this news article and create an engaging Instagram post:
            
            TITLE: {article['title']}
            DESCRIPTION: {article.get('description', 'No description available')}
            SOURCE: {article.get('source', {}).get('name', 'Unknown source')}
            
            Please provide:
            1. A catchy, engaging caption (max 2200 characters with relevant hashtags)
            2. 5-7 relevant hashtags (make them trendy and engaging)
            
            IMPORTANT: Format your response EXACTLY like this:
            CAPTION: [your engaging caption here with emojis and hashtags]
            HASHTAGS: [your hashtags here separated by spaces]
            
            Make it viral-worthy and attention-grabbing!
            """

            print(f"Sending to Gemini: {article['title'][:50]}...")
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Parse the response
            caption = ""
            hashtags = ""

            caption_match = re.search(r'CAPTION:\s*(.*?)(?=\nHASHTAGS:|\n\n|\Z)', 
                                     response_text, re.DOTALL | re.IGNORECASE)
            if caption_match:
                caption = caption_match.group(1).strip()

            hashtags_match = re.search(r'HASHTAGS:\s*(.*?)(?=\nCAPTION:|\n\n|\Z)', 
                                      response_text, re.DOTALL | re.IGNORECASE)
            if hashtags_match:
                hashtags = hashtags_match.group(1).strip()

            if not caption:
                caption = f"🔥 {article['title']}\n\n{article.get('description', '')}\n\n⚡ Breaking News Update ⚡\n\n#News #Trending #Update"
                hashtags = "#news #breakingnews #trending #update #viral #today"

            return {
                "caption": caption,
                "hashtags": hashtags
            }

        except Exception as e:
            print(f"Error analyzing with Gemini: {str(e)}")
            emojis = ["🔥", "📰", "⚡", "💥", "🚨", "👀", "💡", "🌟"]
            emoji = random.choice(emojis)
            return {
                "caption": f"{emoji} {article['title']}\n\n{article.get('description', '')}\n\n#BreakingNews #Trending #Update",
                "hashtags": f"#news #breakingnews #{self.config.CATEGORY} #trending #update #viral"
            }

    # ═══════════════════════════════════════════════════════════════
    #  Colour helpers
    # ═══════════════════════════════════════════════════════════════
    def _pick_vibrant_color(self):
        """Pick a random vibrant colour."""
        return random.choice(self.VIBRANT_COLORS)

    # ═══════════════════════════════════════════════════════════════
    #  Dynamic text sizing helper
    # ═══════════════════════════════════════════════════════════════
    def _fit_headline(self, draw, text, max_width, y_start, y_end, initial_font, min_font_size=30):
        """
        Decrease font size until the wrapped text fits vertically in the given space.
        Returns (best_font, lines) where lines is a list of word lists.
        """
        font = initial_font

        while True:
            try:
                current_size = font.size
            except AttributeError:
                current_size = min_font_size

            if current_size < min_font_size:
                break

            words = text.split()
            lines = []
            while words:
                line_words = []
                while words:
                    test_line = " ".join(line_words + [words[0]])
                    w = draw.textlength(test_line, font=font)
                    if w <= max_width:
                        line_words.append(words.pop(0))
                    else:
                        break
                if not line_words and words:
                    line_words = [words.pop(0)]
                if line_words:
                    lines.append(line_words)

            total_height = len(lines) * (current_size + 10)
            if y_start + total_height <= y_end:
                return font, lines

            try:
                font = ImageFont.truetype(font.path, current_size - 2)
            except:
                if current_size == min_font_size:
                    return font, lines
                font = ImageFont.load_default()
                break

        return font, lines

    # ═══════════════════════════════════════════════════════════════
    #  Instagram post creation – White + One Colour ONLY
    # ═══════════════════════════════════════════════════════════════
    def create_instagram_post(self, article, gemini_content):
        """
        Create an attractive Instagram Story post.
        Design features:
      - Full-bleed background image with a dark vignette
      - Diagonal accent triangle in the top-left corner
      - Category pill + HOT badge
      - Glowing vertical accent bar on the left of the overlay
      - Logo · Date row with a hairline divider
      - Dynamic headline with alternating white/accent word coloring
      - Source + "READ MORE →" footer bar
    Only 2 colours used on every post: White + one vibrant accent.
        """
        try:
            W, H = self.config.POST_WIDTH, self.config.POST_HEIGHT   # 1080 × 1920

            # ── 1. Load / generate the base image ──────────────────────────
            img_url = article.get('urlToImage') or article.get('img_url')
            if img_url:
                try:
                    resp = requests.get(img_url, timeout=5,
                                        headers={'User-Agent': 'Mozilla/5.0'})
                    if resp.status_code == 200:
                        base_img = Image.open(BytesIO(resp.content)).convert('RGB')
                        img = ImageOps.fit(base_img, (W, H),
                                           method=Image.Resampling.LANCZOS)
                    else:
                        img = Image.new('RGB', (W, H), color=self.COLOR_BG_DARK)
                except Exception:
                    img = Image.new('RGB', (W, H), color=self.COLOR_BG_DARK)
            else:
                img = Image.new('RGB', (W, H), color=self.COLOR_BG_DARK)

            # ── 2. Pick ONE vibrant accent colour ──────────────────────────
            accent   = self._pick_vibrant_color()
            WHITE    = self.COLOR_WHITE
            OVERLAY  = (4, 4, 18)          # near-black dark blue

            draw = ImageDraw.Draw(img, 'RGBA')

            # ── 3. Full-image dark vignette (edges only) ───────────────────
            #    Four semi-transparent gradient strips around the perimeter
            vign_w = int(W * 0.35)
            vign_h = int(H * 0.35)
            for i in range(vign_w):
                alpha = int(160 * (1 - i / vign_w))
                draw.line([(i, 0), (i, H)], fill=(*OVERLAY, alpha))
            for i in range(vign_w):
                alpha = int(160 * (1 - i / vign_w))
                draw.line([(W - 1 - i, 0), (W - 1 - i, H)], fill=(*OVERLAY, alpha))
            for i in range(vign_h):
                alpha = int(180 * (1 - i / vign_h))
                draw.line([(0, i), (W, i)], fill=(*OVERLAY, alpha))

            # ── 4. Bottom overlay (45 % of canvas) ─────────────────────────
            overlay_h = int(H * 0.45)
            overlay_top = H - overlay_h

            # Smooth feathered top edge (200 px)
            feather = 200
            for i in range(feather):
                alpha = int((i / feather) ** 1.5 * 245)
                draw.line([(0, overlay_top - feather + i),
                           (W, overlay_top - feather + i)],
                          fill=(*OVERLAY, alpha))
            # Solid lower part
            draw.rectangle([(0, overlay_top), (W, H)],
                            fill=(*OVERLAY, 245))

            # ── 5. Diagonal accent triangle (top-left corner) ──────────────
            tri_size = 260
            draw.polygon([(0, 0), (tri_size, 0), (0, tri_size)],
                         fill=(*accent, 210))
            # Small inner white triangle for depth
            inner = int(tri_size * 0.28)
            draw.polygon([(0, 0), (inner, 0), (0, inner)],
                         fill=(*WHITE, 80))

            # ── 6. HOT badge (top-right) ────────────────────────────────────
            badge_margin = 48
            badge_w, badge_h = 160, 64
            bx = W - badge_margin - badge_w
            by = badge_margin
            draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h],
                                    radius=14, fill=(*accent, 230))
            draw.text((bx + badge_w // 2, by + badge_h // 2 - 2),
                      "HOT", font=self.font_logo,
                      fill=WHITE, anchor='mm')

            # ── 7. Category pill ────────────────────────────────────────────
            category_text = self.config.CATEGORY.upper()
            pill_x, pill_y = 60, 58
            pill_pad_x, pill_pad_y = 28, 14
            pill_tw = draw.textlength(category_text, font=self.font_xsmall)
            pill_w = int(pill_tw) + pill_pad_x * 2
            pill_h = 52
            # Semi-transparent filled pill
            pill_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            pill_draw  = ImageDraw.Draw(pill_layer)
            pill_draw.rounded_rectangle(
                [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
                radius=26, fill=(*accent, 55))
            pill_draw.rounded_rectangle(
                [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
                radius=26, outline=(*accent, 180), width=3)
            img.paste(Image.alpha_composite(
                Image.new('RGBA', (W, H), (0, 0, 0, 0)), pill_layer),
                mask=pill_layer.split()[3])
            draw = ImageDraw.Draw(img, 'RGBA')
            draw.text((pill_x + pill_w // 2, pill_y + pill_h // 2),
                      category_text, font=self.font_xsmall,
                      fill=accent, anchor='mm')

            # ── 8. Glowing vertical bar left of overlay ─────────────────────
            bar_x   = 44
            bar_top = overlay_top + 20
            bar_bot = H - 60
            bar_w   = 6
            # Glow (soft wider bar behind)
            glow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            glow_draw  = ImageDraw.Draw(glow_layer)
            for offset, alpha in [(10, 18), (7, 35), (4, 60), (2, 100)]:
                glow_draw.rounded_rectangle(
                    [bar_x - offset, bar_top,
                     bar_x + bar_w + offset, bar_bot],
                    radius=3, fill=(*accent, alpha))
            glow_draw.rounded_rectangle(
                [bar_x, bar_top, bar_x + bar_w, bar_bot],
                radius=3, fill=(*accent, 255))
            img.paste(Image.alpha_composite(
                Image.new('RGBA', (W, H), (0, 0, 0, 0)), glow_layer),
                mask=glow_layer.split()[3])
            draw = ImageDraw.Draw(img, 'RGBA')

            # ── 9. Logo · Date row ──────────────────────────────────────────
            logo_left = 80
            logo_y    = overlay_top + 52
            draw.text((logo_left, logo_y),      "TOP",  font=self.font_logo, fill=WHITE)
            tw_top = draw.textlength("TOP",  font=self.font_logo)
            draw.text((logo_left + tw_top + 6, logo_y), "NEWS", font=self.font_logo, fill=accent)
            tw_news = draw.textlength("NEWS", font=self.font_logo)

            dot_x = logo_left + tw_top + tw_news + 24
            dot_y = logo_y + self.font_logo.size // 2
            r = 6
            draw.ellipse([dot_x - r, dot_y - r, dot_x + r, dot_y + r],
                         fill=(*accent, 130))

            date_str = datetime.now().strftime("%d %b %Y").upper()
            draw.text((dot_x + 20, logo_y), date_str,
                      font=self.font_xsmall, fill=(*WHITE, 170))

            # Hairline divider
            div_y = logo_y + self.font_logo.size + 22
            draw.line([(80, div_y), (W - 80, div_y)],
                      fill=(*accent, 70), width=2)

            # ── 10. Headline (dynamic sizing, word-level colour) ─────────────
            headline_raw = article['title']
            if ' - ' in headline_raw:
                headline_raw = headline_raw.split(' - ')[0]
            headline_text = headline_raw.upper()

            margin        = 80
            max_width = W - margin - 60    # leave room for the bar
            h_start       = div_y + 36
            h_end         = H - 110

            best_font, lines = self._fit_headline(
                draw, headline_text, max_width,
                h_start, h_end, self.font_headline)

            current_y = h_start
            word_index = 0
            for line_words in lines:
                x = margin
                for word in line_words:
                    color = WHITE if word_index % 2 == 0 else accent
                    word_str = word + " "
                    draw.text((x, current_y), word_str,
                              font=best_font, fill=color)
                    x += draw.textlength(word_str, font=best_font)
                    word_index += 1
                current_y += best_font.size + 14

            # ── 11. Source + "READ MORE →" footer bar ───────────────────────
            footer_h = 68
            footer_top = H - footer_h

            footer_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            footer_draw  = ImageDraw.Draw(footer_layer)
            footer_draw.rectangle([(0, footer_top), (W, H)],
                                   fill=(*accent, 38))
            img.paste(Image.alpha_composite(
                Image.new('RGBA', (W, H), (0, 0, 0, 0)), footer_layer),
                mask=footer_layer.split()[3])
            draw = ImageDraw.Draw(img, 'RGBA')

            # Thin top border on footer
            draw.line([(0, footer_top), (W, footer_top)],
                      fill=(*accent, 120), width=2)

            source_name = article.get('source', {}).get('name', 'NEWS').upper()
            footer_text_y = footer_top + footer_h // 2
            draw.text((margin, footer_text_y),
                      f"SOURCE: {source_name}",
                      font=self.font_xsmall, fill=accent, anchor='lm')
            draw.text((W - margin, footer_text_y),
                      "READ MORE →",
                      font=self.font_xsmall, fill=WHITE, anchor='rm')

            # ── 12. Save ─────────────────────────────────────────────────────
            filename = f"post_{int(time.time())}_{random.randint(100, 999)}.jpg"
            filepath = os.path.join(self.config.POSTS_DIRECTORY, filename)
            img.convert('RGB').save(filepath, "JPEG", quality=95)

            return {
                "image_path": filename,
                "article_title":      article['title'],
                "caption":    gemini_content['caption'],
                "hashtags":   gemini_content['hashtags'],
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error creating post: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    # ═══════════════════════════════════════════════════════════════
    #  Batch processing & storage
    # ═══════════════════════════════════════════════════════════════
    def process_news_batch(self):
        """Process a batch of news articles."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processing news batch...")

        articles = self.fetch_news()

        if not articles:
            print("No new articles found. Trying pending...")
            if self.pending_news:
                articles = self.pending_news[:self.config.MAX_POSTS_PER_BATCH]
                self.pending_news = self.pending_news[self.config.MAX_POSTS_PER_BATCH:]
            else:
                return []

        if self.pending_news and len(articles) < self.config.MAX_POSTS_PER_BATCH:
            needed = self.config.MAX_POSTS_PER_BATCH - len(articles)
            articles.extend(self.pending_news[:needed])
            self.pending_news = self.pending_news[needed:]

        to_process = articles[:self.config.MAX_POSTS_PER_BATCH]
        extra = articles[self.config.MAX_POSTS_PER_BATCH:]
        if extra:
            self.pending_news = (extra + self.pending_news)[:10]

        created_posts = []

        for article in to_process:
            try:
                print(f"Processing: {article['title'][:60]}...")
                gemini_content = self.analyze_with_gemini(article)
                post = self.create_instagram_post(article, gemini_content)

                if post:
                    self.processed_news.add(article['id'])
                    self.save_post_to_db(post)
                    created_posts.append(post)
                    print(f"✓ Created post for: {article['title'][:50]}...")
                else:
                    print(f"✗ Failed to create post for: {article['title'][:50]}...")

            except Exception as e:
                print(f"Error processing article: {str(e)}")
                import traceback
                traceback.print_exc()

        self.save_processed_news()
        print(f"Created {len(created_posts)} posts")
        return created_posts

    def save_post_to_db(self, post):
        """Save post metadata to JSON file."""
        try:
            db_file = "posts_database.json"
            if os.path.exists(db_file):
                with open(db_file, 'r') as f:
                    posts = json.load(f)
            else:
                posts = []

            posts.append(post)
            if len(posts) > 50:
                posts = posts[-50:]

            with open(db_file, 'w') as f:
                json.dump(posts, f, indent=2)
        except Exception as e:
            print(f"Error saving to database: {e}")

    def get_recent_posts(self, limit=10):
        """Get recent posts from database."""
        try:
            db_file = "posts_database.json"
            if os.path.exists(db_file):
                with open(db_file, 'r') as f:
                    posts = json.load(f)
                posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return posts[:limit]
            return []
        except Exception as e:
            print(f"Error getting recent posts: {e}")
            return []

    def get_stats(self):
        """Get system statistics."""
        return {
            'processed_count': len(self.processed_news),
            'pending_count': len(self.pending_news),
            'next_check': (datetime.now() + 
                          timedelta(minutes=self.config.CHECK_INTERVAL_MINUTES)).strftime('%H:%M:%S')
        }


# ═══════════════════════════════════════════════════════════════
#  Initialize the generator
# ═══════════════════════════════════════════════════════════════
generator = NewsPostGenerator()

print("=" * 50)
print("Starting News Instagram Post Generator")
print("=" * 50)
print(f"Model: {Config.GEMINI_MODEL}")
print(f"Category: {Config.CATEGORY}")
print(f"Check interval: {Config.CHECK_INTERVAL_MINUTES} minutes")
print("=" * 50)

initial_posts = generator.process_news_batch()
print(f"✓ Created {len(initial_posts)} initial posts")
print("=" * 50)


# ═══════════════════════════════════════════════════════════════
#  Scheduler
# ═══════════════════════════════════════════════════════════════
def scheduled_task():
    print(f"\n{'='*50}\nScheduled task at {datetime.now().strftime('%H:%M:%S')}\n{'='*50}")
    with app.app_context():
        generator.process_news_batch()


def run_scheduler():
    schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(scheduled_task)
    while True:
        schedule.run_pending()
        time.sleep(60)


# ═══════════════════════════════════════════════════════════════
#  Flask Routes
# ═══════════════════════════════════════════════════════════════
@app.route('/')
def index():
    posts = generator.get_recent_posts(12)
    stats = generator.get_stats()
    return render_template('index.html', posts=posts, stats=stats)


@app.route('/api/posts')
def get_posts():
    return jsonify(generator.get_recent_posts(20))


@app.route('/api/create-posts')
def create_posts():
    posts = generator.process_news_batch()
    return jsonify({
        'success': True,
        'created': len(posts),
        'posts': posts[:3]
    })


@app.route('/api/stats')
def get_system_stats():
    return jsonify(generator.get_stats())


@app.route('/post/<path:filename>')
def serve_post_image(filename):
    try:
        return send_file(os.path.join('posts', filename))
    except:
        return "Image not found", 404


@app.route('/api/clear-pending')
def clear_pending():
    generator.pending_news = []
    return jsonify({'success': True, 'message': 'Pending queue cleared'})


if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("\n" + "=" * 50)
    print("Web server starting on http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000, use_reloader=False)