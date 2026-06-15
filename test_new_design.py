
import sys
import os
import json
from unittest.mock import MagicMock

# Mock config
import config
config.Config.GEMINI_API_KEY = "mock_key"
config.Config.POSTS_DIRECTORY = "test_posts"

from app import NewsPostGenerator

def test_generation():
    gen = NewsPostGenerator()
    # Mock Gemini response
    gen.model.generate_content = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "CAPTION: Test Caption\nSUMMARY: Test Summary\nHASHTAGS: #test #news\nDESIGN: ACCENT_COLOR: #FF00FF, STYLE: Cyberpunk"
    gen.model.generate_content.return_value = mock_response

    article = {
        'title': 'Test Article for New Design',
        'description': 'This is a test description for the new design logic.',
        'urlToImage': 'https://files.realpython.com/media/Natural-Language-Processing-With-Spacy-in-Python_Watermarked.801083431940.jpg',
        'source': {'name': 'Test Source'},
        'url': 'http://example.com',
        'publishedAt': '2025-01-01T00:00:00Z',
        'id': 'test_id_123'
    }

    print("Testing post creation...")
    gemini_content = gen.analyze_with_gemini(article)
    post = gen.create_instagram_post(article, gemini_content)
    
    if post:
        print(f"Success! Post created: {post['image_path']}")
        if os.path.exists(os.path.join('test_posts', post['image_path'])):
            print("File exists on disk.")
    else:
        print("Failed to create post.")

if __name__ == "__main__":
    if not os.path.exists('test_posts'):
        os.makedirs('test_posts')
    test_generation()
