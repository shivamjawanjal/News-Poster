from PIL import Image, ImageDraw, ImageFont
import textwrap
import uuid

def create_post(text):
    img = Image.new("RGB", (1080, 1080), "#0f172a")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("arial.ttf", 50)

    wrapped = textwrap.fill(text, width=30)
    draw.text((80, 300), wrapped, font=font, fill="white")

    filename = f"posts/{uuid.uuid4()}.png"
    img.save(filename)
    return filename

def extract_dominant_colors(self, img, n=5):
    """Extract dominant colors from a PIL Image (resized for speed)."""
    small = img.copy()
    small.thumbnail((100, 100))
    # Use getcolors after converting to RGB
    small = small.convert('RGB')
    colors = small.getcolors(maxcolors=10000)
    if not colors:
        return [(255,255,255), (0,0,0)]  # fallback
    colors.sort(reverse=True, key=lambda x: x[0])
    return [c[1] for c in colors[:n]]

def _darken_color(self, rgb, factor=0.6):
    """Darken an RGB tuple by multiplying by factor (0-1)."""
    return tuple(int(c * factor) for c in rgb)

def _contrast_color(self, rgb):
    """Return white or black depending on luminance."""
    r, g, b = rgb
    luminance = (0.299*r + 0.587*g + 0.114*b) / 255
    return (255, 255, 255) if luminance < 0.5 else (0, 0, 0)

def _fit_headline(self, draw, text, max_width, y_start, y_end, initial_font, min_font_size=30):
    """
    Find the largest font size that fits the text in the given vertical space,
    and return the (font, list of word lines) that best fills the space.
    """
    font = initial_font
    # Try decreasing font size until it fits
    while font.size >= min_font_size:
        words = text.split()
        lines = []
        # Word wrapping
        while words:
            line_words = []
            while words:
                test_line = " ".join(line_words + [words[0]])
                w = draw.textlength(test_line, font=font)
                if w <= max_width:
                    line_words.append(words.pop(0))
                else:
                    break
            lines.append(line_words)
            if not line_words:
                # Single long word doesn't fit at all? Force break
                if words:
                    # just take the word anyway (will overflow slightly)
                    line_words = [words.pop(0)]
                    lines.append(line_words)
                else:
                    break
        
        total_height = len(lines) * (font.size + 10)
        if y_start + total_height <= y_end:
            # Fits! Now try to increase font size a bit more to fill space
            # but we are decreasing from large, so this is the largest that fits
            # Actually we can check if a slightly larger font would also fit
            return font, lines
        # else try smaller font
        # Reduce font size by 2pt (could be smarter)
        try:
            font = ImageFont.truetype(font.path, font.size - 2)
        except:
            font = ImageFont.load_default()
    # Fallback: return the smallest acceptable font
    return font, lines

def _fit_caption(self, draw, text, max_width, y_start, y_end, initial_font, min_font_size=18):
    """
    Fit a single line or two of caption within the available vertical space.
    Returns a font that makes the text fill the width nicely.
    """
    font = initial_font
    while font.size >= min_font_size:
        w = draw.textlength(text, font=font)
        if w <= max_width:
            return font
        try:
            font = ImageFont.truetype(font.path, font.size - 2)
        except:
            font = ImageFont.load_default()
    return font